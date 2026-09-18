"""Synthetic persistence/export regression tests; no real vault or database."""
import json
import pytest
from fastapi.testclient import TestClient
from test_db_target_registry_api import _make_registry
from app.main import app


def test_many_targets_flat_settings_persist_and_export(tmp_path):
    registry, _ = _make_registry(str(tmp_path))
    ids = ["client-a", "client_a", "CLIENT-A"] + [f"client-{n}" for n in range(100)]
    for i, target_id in enumerate(ids):
        registry.create_target({"target_id": target_id, "display_name": f"Cliente à {i} / report",
                                "status": "disabled", "connection_vault_ref": f"vault://synthetic.{i}"})
    envs = [registry.get_target(t)["connection"]["env_var"] for t in ids]
    assert len(set(envs)) == len(ids)
    untouched = registry.get_target(ids[1])
    edited = registry.update_target(ids[0], {
        "display_name": "Nuovo nome è / QA", "environment": "qa", "read_enabled": False,
        "write_policy": "allow", "max_rows": 7, "max_result_bytes": "Any",
        "anonymization_enabled": True, "anonymization_mode": "hybrid",
        "llm_provider": "ollama", "llm_model": "synthetic-model", "allowed_tools": [],
        "connection_vault_ref": "vault://synthetic.changed"})
    assert edited["limits"] == {"max_rows": 7, "max_result_bytes": None}
    assert edited["policy"]["read_enabled"] is False
    assert edited["policy"]["write_policy"] == "allow"
    assert edited["anonymization"]["model"] == "synthetic-model"
    assert edited["anonymization"]["provider"] == "ollama"
    assert edited["allowed_tools"] == []
    assert edited["connection"]["vault_ref"] == "vault://synthetic.changed"
    other = registry.get_target(ids[1])
    untouched.pop("state"); other.pop("state")
    assert other == untouched
    reloaded, _ = _make_registry(str(tmp_path))
    assert reloaded.get_target(ids[0])["limits"]["max_result_bytes"] is None
    exported = json.loads(reloaded.runtime_path.read_text())["targets"]
    assert next(t for t in exported if t["target_id"] == ids[0])["max_result_bytes"] is None
    reloaded.update_target(ids[0], {"max_result_bytes": 2000})
    assert reloaded.get_target(ids[0])["limits"]["max_result_bytes"] == 2000
    reloaded.delete_target(ids[0])
    assert reloaded.get_target(ids[1]) is not None


def test_duplicate_binding_and_invalid_limits_are_rejected(tmp_path):
    registry, _ = _make_registry(str(tmp_path))
    target = registry.create_target({"target_id": "one"})
    with pytest.raises(ValueError, match="already assigned"):
        registry.create_target({"target_id": "two", "connection_env_var": target["connection"]["env_var"]})
    with pytest.raises(ValueError, match="Duplicate"):
        registry.create_target({"target_id": "one"})
    for value in (0, -1, True, 1.2, "oops", ""):
        with pytest.raises(ValueError, match="max_result_bytes"):
            registry.update_target("one", {"max_result_bytes": value})
    assert registry.get_target("one")["limits"]["max_result_bytes"] == 131072
    with pytest.raises(ValueError, match="target_id"):
        registry.create_target({"target_id": "not/a/path"})


def test_api_any_roundtrip_and_neighbor_isolation(tmp_path, monkeypatch):
    registry, _ = _make_registry(str(tmp_path))
    monkeypatch.setattr("app.main.db_target_registry", registry)
    monkeypatch.setattr("app.main.process_manager.status", lambda service: {"running": False})
    client = TestClient(app)
    for target_id in ("one", "two"):
        response = client.post("/api/db-targets", json={"values": {
            "target_id":target_id, "status":"disabled", "max_result_bytes":1024}})
        assert response.status_code == 200
    response = client.put("/api/db-targets/one", json={"values": {"max_result_bytes":None, "max_rows":7}})
    assert response.status_code == 200
    assert response.json()["target"]["limits"] == {"max_rows":7, "max_result_bytes":None}
    assert registry.get_target("two")["limits"]["max_result_bytes"] == 1024
