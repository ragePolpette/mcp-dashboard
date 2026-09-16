"""Connection management uses synthetic secrets and never contacts SQL Server."""
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import app.main as main
from app.db_target_registry import DbTargetRegistry
from app.secret_vault import DashboardSecretVault
from app.sql_connections import build_connection_string, parse_connection_string, save_connection_profile

PASSWORD = ' Synthetic;"quoted"=password '
PROFILE = dict(server='sql.example.test', port=1433, database='example', username='reader', password=PASSWORD)

@pytest.fixture
def setup(tmp_path, monkeypatch):
    vault = DashboardSecretVault(tmp_path / 'vault')
    vault.initialize('Synthetic-passphrase-2026!')
    bootstrap = tmp_path / 'bootstrap.json'
    bootstrap.write_text('{"targets": []}')
    registry = DbTargetRegistry(tmp_path / 'targets.json', tmp_path / 'runtime.json', bootstrap, vault=vault)
    registry.create_target({'target_id': 'example', 'environment': 'dev', 'status': 'disabled',
                            'connection': {'env_var': 'CUSTOM_SQL_CONNECTION'}})
    monkeypatch.setattr(main, 'vault_manager', vault)
    monkeypatch.setattr(main, 'db_target_registry', registry)
    monkeypatch.setattr(main.process_manager, 'status', lambda *a, **kw: {'running': False})
    return TestClient(main.app), vault, registry, tmp_path

def test_save_encrypts_and_never_returns_password(setup):
    client, vault, registry, path = setup
    response = client.put('/api/db-targets/example/connection', json=PROFILE)
    assert response.status_code == 200, response.text
    assert PASSWORD not in response.text
    profile = client.get('/api/db-targets/example/connection').json()
    assert profile['password_set'] and 'password' not in profile
    assert profile['server'] == PROFILE['server']
    target = registry.get_target('example')
    assert target['connection']['env_var'] == 'CUSTOM_SQL_CONNECTION'
    secret = vault.resolve_secret(target['connection']['vault_ref'])
    assert parse_connection_string(secret)['password'] == PASSWORD
    for file in path.rglob('*'):
        if file.is_file():
            assert PASSWORD.encode() not in file.read_bytes()
            assert secret.encode() not in file.read_bytes()
    assert client.put('/api/db-targets/example/connection', json={**PROFILE, 'password': '', 'database': 'changed'}).status_code == 200
    assert parse_connection_string(vault.resolve_secret(target['connection']['vault_ref']))['password'] == PASSWORD

def test_shared_reference_is_not_overwritten(setup):
    client, vault, registry, _ = setup
    original = build_connection_string(PROFILE)
    vault.upsert_secret('db.shared', original)
    registry.update_target('example', {'connection': {'vault_ref': 'db.shared'}})
    registry.create_target({'target_id': 'second', 'connection': {'vault_ref': 'db.shared'}})
    assert client.put('/api/db-targets/example/connection', json={**PROFILE, 'password': 'Replacement!'}).status_code == 200
    assert vault.resolve_secret('db.shared') == original
    assert registry.get_target('example')['connection']['vault_ref'] != registry.get_target('second')['connection']['vault_ref']

@pytest.mark.parametrize('patch', [{'port': 0}, {'port': True}, {'port': 65536}, {'encrypt': 'false'}, {'server': 'host;Password=oops'}, {'password': ['secret']}])
def test_bad_input_does_not_leak_or_store_secret(setup, patch):
    client, vault, _, _ = setup
    response = client.put('/api/db-targets/example/connection', json={**PROFILE, **patch})
    assert response.status_code == 400
    assert PASSWORD not in response.text and 'oops' not in response.text
    assert vault.list_entries() == []

def test_locked_vault_and_missing_target_leave_no_entries(setup):
    client, vault, _, _ = setup
    assert client.put('/api/db-targets/missing/connection', json=PROFILE).status_code == 404
    assert vault.list_entries() == []
    vault.lock()
    assert client.put('/api/db-targets/example/connection', json=PROFILE).status_code == 400
    assert client.get('/api/db-targets/example/connection').status_code == 400

@pytest.mark.parametrize('extra', ['Encrypt=strict;', 'Application Name=Custom;'])
def test_advanced_settings_are_not_silently_lost(setup, extra):
    client, vault, registry, _ = setup
    secret = build_connection_string(PROFILE) + extra
    vault.upsert_secret('db.advanced', secret)
    registry.update_target('example', {'connection': {'vault_ref': 'db.advanced'}})
    assert client.put('/api/db-targets/example/connection', json=PROFILE).status_code == 400
    assert vault.resolve_secret('db.advanced') == secret

def test_failed_registry_update_rolls_back_secret(setup, monkeypatch):
    _, vault, registry, _ = setup
    target = registry.get_target('example')
    monkeypatch.setattr(registry, 'update_target', Mock(side_effect=RuntimeError('synthetic failure')))
    with pytest.raises(RuntimeError):
        save_connection_profile(target, PROFILE, vault, registry)
    assert vault.list_entries() == []

def test_apply_validates_before_restart_and_passes_resolved_environment(setup, monkeypatch):
    client, vault, registry, _ = setup
    monkeypatch.setattr(main.options_manager, 'options_env', lambda service: {})
    monkeypatch.setattr(main.options_manager, 'missing_required_options', lambda *a, **kw: [])
    restart = Mock(return_value={'ok': True, 'status': {'health_ok': True}})
    monkeypatch.setattr(main.process_manager, 'restart', restart)
    registry.update_target('example', {'status': 'active'})
    assert client.post('/api/db-targets/runtime/apply').status_code == 400
    restart.assert_not_called()
    assert client.put('/api/db-targets/example/connection', json=PROFILE).status_code == 200
    assert client.post('/api/db-targets/runtime/apply').status_code == 200
    env = restart.call_args.kwargs['env_overrides']
    assert parse_connection_string(env['CUSTOM_SQL_CONNECTION'])['password'] == PASSWORD
    assert Path(env['TARGETS_FILE']).exists()
    vault.lock()
    restart.reset_mock()
    assert client.post('/api/db-targets/runtime/apply').status_code == 400
    restart.assert_not_called()

def test_apply_requires_prod_salt_and_reports_start_failure(setup, monkeypatch):
    client, _, registry, _ = setup
    monkeypatch.setattr(main.options_manager, 'options_env', lambda service: {})
    monkeypatch.setattr(main.options_manager, 'missing_required_options', lambda *a, **kw: [])
    restart = Mock(return_value={'ok': False})
    monkeypatch.setattr(main.process_manager, 'restart', restart)
    assert client.put('/api/db-targets/example/connection', json=PROFILE).status_code == 200
    registry.update_target('example', {'environment': 'prod', 'status': 'active', 'anonymization': {'enabled': True, 'mode': 'hybrid', 'provider': 'ollama', 'model': 'qwen2.5:3b-instruct'}})
    assert client.post('/api/db-targets/runtime/apply').status_code == 400
    restart.assert_not_called()
    monkeypatch.setattr(main.options_manager, 'options_env', lambda service: {'ANON_HASH_SALT': 'synthetic-salt'})
    assert client.post('/api/db-targets/runtime/apply').status_code == 503


def test_prod_can_disable_anonymization_and_apply_without_salt(setup, monkeypatch):
    client, _, registry, _ = setup
    monkeypatch.setattr(main.options_manager, 'options_env', lambda service: {})
    monkeypatch.setattr(main.options_manager, 'missing_required_options', lambda *a, **kw: [])
    restart = Mock(return_value={'ok': True, 'status': {'health_ok': True}})
    monkeypatch.setattr(main.process_manager, 'restart', restart)
    assert client.put('/api/db-targets/example/connection', json=PROFILE).status_code == 200
    registry.update_target('example', {'environment': 'prod', 'status': 'active',
        'anonymization': {'enabled': True, 'mode': 'hybrid', 'provider': 'ollama', 'model': 'test-model'}})
    response = client.put('/api/db-targets/example', json={'values': {'anonymization': {'enabled': False}}})
    assert response.status_code == 200
    target = response.json()['target']
    assert target['anonymization'] == {'enabled': False, 'mode': 'off', 'provider': 'none', 'model': ''}
    assert target['runtime']['anonymization_required'] is False
    assert target['policy']['write_policy'] == 'deny'
    exported = registry.runtime_snapshot()['targets'][0]
    assert exported['anonymization_enabled'] is False
    assert exported['anonymization_mode'] == 'off'
    assert client.post('/api/db-targets/runtime/apply').status_code == 200
    restart.assert_called_once()
