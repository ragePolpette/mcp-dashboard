"""Tests for the Jenkins destination registry, its API and the MCP admin client."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from dashboard_client import dashboard_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import main  # noqa: E402
from app.jenkins_admin_client import JenkinsAdminClient, JenkinsAdminError  # noqa: E402
from app.jenkins_demo_registry import JenkinsDemoRegistry, normalize_registry  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ServiceControlDefinition, ServiceDefinition  # noqa: E402


# ---------- registry ----------


def test_empty_registry_defaults_to_confirm_for_everything():
    with tempfile.TemporaryDirectory() as tmp:
        registry = JenkinsDemoRegistry(Path(tmp) / "jenkins.json")
        assert registry.snapshot() == {"default_policy": "confirm", "demos": []}
        assert json.loads(registry.runtime_env()["JENKINS_DEMO_POLICIES"]) == {"default": "confirm", "demos": {}}


def test_registry_round_trip_and_runtime_shape():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "jenkins.json"
        registry = JenkinsDemoRegistry(path)
        registry.replace({
            "default_policy": "deny",
            "demos": [{"name": "demo4", "policy": "allow"}, {"name": "demo", "policy": "confirm"}],
        })
        reloaded = JenkinsDemoRegistry(path)
        assert reloaded.snapshot()["demos"] == [{"name": "demo4", "policy": "allow"}, {"name": "demo", "policy": "confirm"}]
        assert reloaded.runtime_value() == {"default": "deny", "demos": {"demo4": "allow", "demo": "confirm"}}
        assert json.loads(path.read_text(encoding="utf-8"))["version"] == 1


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"default_policy": "allow"}, "default_policy"),
        ({"demos": [{"name": "demo4", "policy": "allow"}, {"name": "demo4", "policy": "deny"}]}, "Duplicate"),
        ({"demos": [{"name": "demo*", "policy": "allow"}]}, "Invalid destination name"),
        ({"demos": [{"name": "demo 4", "policy": "allow"}]}, "Invalid destination name"),
        ({"demos": [{"name": "", "policy": "allow"}]}, "Invalid destination name"),
        ({"demos": [{"name": "demo4", "policy": "yes"}]}, "Invalid policy"),
        ({"demos": {"demo4": "allow"}}, "list"),
    ],
)
def test_registry_rejects_invalid_payloads(payload, message):
    with pytest.raises(ValueError, match=message):
        normalize_registry(payload)


def test_names_are_exact_and_case_sensitive():
    registry = normalize_registry({"demos": [{"name": "Demo4", "policy": "allow"}, {"name": "demo4", "policy": "deny"}]})
    assert [item["name"] for item in registry["demos"]] == ["Demo4", "demo4"]


def test_invalid_saved_registry_falls_back_to_confirm_defaults():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "jenkins.json"
        path.write_text(json.dumps({"default_policy": "allow", "demos": []}), encoding="utf-8")
        assert JenkinsDemoRegistry(path).runtime_value() == {"default": "confirm", "demos": {}}


def test_classify_reports_new_and_missing_destinations():
    with tempfile.TemporaryDirectory() as tmp:
        registry = JenkinsDemoRegistry(Path(tmp) / "jenkins.json")
        registry.replace({"default_policy": "confirm", "demos": [
            {"name": "demo4", "policy": "allow"}, {"name": "old", "policy": "deny"},
        ]})
        result = registry.classify(["demo", "demo4", "demo9"])
        assert result["new"] == ["demo", "demo9"]
        assert result["missing"] == ["old"]
        assert result["effective_policies"] == {"demo": "confirm", "demo4": "allow", "demo9": "confirm"}


# ---------- runtime env ----------


def test_runtime_env_carries_registry_and_admin_key_that_options_cannot_override(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        registry = JenkinsDemoRegistry(Path(tmp) / "jenkins.json")
        registry.replace({"default_policy": "confirm", "demos": [{"name": "demo4", "policy": "allow"}]})
        monkeypatch.setattr(main, "jenkins_demo_registry", registry)
        monkeypatch.setattr(main, "jenkins_admin_client", JenkinsAdminClient(key="k" * 43))
        monkeypatch.setattr(
            main.options_manager, "options_env",
            lambda service: {"JENKINS_URL": "http://jenkins:8088", "JENKINS_MCP_ADMIN_KEY": "from-options"}
            if service.service_id == "llm-jenkins-mcp" else {},
        )
        env = main._runtime_env_overrides(main.registry.get("llm-jenkins-mcp"))
        assert json.loads(env["JENKINS_DEMO_POLICIES"]) == {"default": "confirm", "demos": {"demo4": "allow"}}
        assert env["JENKINS_MCP_ADMIN_KEY"] == "k" * 43
        assert env["JENKINS_URL"] == "http://jenkins:8088"

        other = main._runtime_env_overrides(main.registry.get("llm-bitbucket-mcp"))
        assert "JENKINS_MCP_ADMIN_KEY" not in other and "JENKINS_DEMO_POLICIES" not in other


def test_admin_key_is_random_and_long():
    a, b = JenkinsAdminClient(), JenkinsAdminClient()
    assert a.key != b.key and len(a.key) >= 32


# ---------- API ----------


class _FakeAdmin:
    def __init__(self, choices=None, active=None, error: JenkinsAdminError | None = None):
        self.choices = choices or []
        self.active = active
        self.error = error
        self.key = "fake"

    def runtime_env(self):
        return {"JENKINS_MCP_ADMIN_KEY": "x" * 40}

    def destinations(self, service):
        if self.error:
            raise self.error
        return list(self.choices)

    def active_policies(self, service):
        if self.error:
            raise self.error
        return self.active


@pytest.fixture
def jenkins_api(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        registry = JenkinsDemoRegistry(Path(tmp) / "jenkins.json")
        monkeypatch.setattr(main, "jenkins_demo_registry", registry)
        calls = {"restart": 0}
        state = {"running": True}
        monkeypatch.setattr(main.process_manager, "status", lambda service, **_k: {"running": state["running"]})

        def _restart(service, **_k):
            calls["restart"] += 1
            return {"ok": True, "status": {"running": True}}

        monkeypatch.setattr(main.process_manager, "restart", _restart)
        monkeypatch.setattr(main.options_manager, "missing_required_options", lambda service, **_k: [])
        yield {"client": dashboard_client(app), "registry": registry, "calls": calls, "state": state,
               "monkeypatch": monkeypatch}


def test_api_get_and_replace_registry(jenkins_api):
    client = jenkins_api["client"]
    assert client.get("/api/jenkins-demos").json()["registry"] == {"default_policy": "confirm", "demos": []}
    saved = client.put("/api/jenkins-demos", json={"values": {
        "default_policy": "deny", "demos": [{"name": "demo4", "policy": "allow"}],
    }})
    assert saved.status_code == 200
    assert saved.json()["registry"]["demos"] == [{"name": "demo4", "policy": "allow"}]
    rejected = client.put("/api/jenkins-demos", json={"values": {"default_policy": "allow"}})
    assert rejected.status_code == 400
    assert jenkins_api["registry"].snapshot()["default_policy"] == "deny"


def test_api_requires_session_token_for_changes():
    unauthenticated = dashboard_client(app, authenticated=False)
    assert unauthenticated.put("/api/jenkins-demos", json={"values": {}}).status_code == 403
    assert unauthenticated.post("/api/jenkins-demos/discover").status_code == 403
    assert unauthenticated.post("/api/jenkins-demos/runtime/apply").status_code == 403


def test_api_discover_lists_new_destinations(jenkins_api):
    jenkins_api["registry"].replace({"default_policy": "confirm", "demos": [{"name": "demo4", "policy": "allow"}]})
    jenkins_api["monkeypatch"].setattr(main, "jenkins_admin_client", _FakeAdmin(choices=["demo", "demo4", "demo12"]))
    response = jenkins_api["client"].post("/api/jenkins-demos/discover")
    assert response.status_code == 200
    payload = response.json()
    assert payload["new"] == ["demo", "demo12"]
    assert payload["effective_policies"]["demo12"] == "confirm"


def test_api_discover_reports_mcp_errors(jenkins_api):
    jenkins_api["monkeypatch"].setattr(
        main, "jenkins_admin_client", _FakeAdmin(error=JenkinsAdminError("Jenkins MCP non raggiungibile: avvia il servizio.", 409)))
    response = jenkins_api["client"].post("/api/jenkins-demos/discover")
    assert response.status_code == 409
    assert "avvia il servizio" in response.json()["detail"]


def test_api_apply_restarts_only_when_registry_changed(jenkins_api):
    registry = jenkins_api["registry"]
    registry.replace({"default_policy": "confirm", "demos": [{"name": "demo4", "policy": "allow"}]})
    fake = _FakeAdmin(active={"default": "confirm", "demos": {"demo4": "allow"}})
    jenkins_api["monkeypatch"].setattr(main, "jenkins_admin_client", fake)
    client = jenkins_api["client"]

    same = client.post("/api/jenkins-demos/runtime/apply").json()
    assert same["restarted"] is False and jenkins_api["calls"]["restart"] == 0

    registry.replace({"default_policy": "confirm", "demos": [{"name": "demo4", "policy": "confirm"}]})
    changed = client.post("/api/jenkins-demos/runtime/apply").json()
    assert changed["restarted"] is True and jenkins_api["calls"]["restart"] == 1


def test_api_apply_restarts_when_active_registry_is_unknown(jenkins_api):
    jenkins_api["monkeypatch"].setattr(
        main, "jenkins_admin_client", _FakeAdmin(error=JenkinsAdminError("chiave non accettata", 409)))
    result = jenkins_api["client"].post("/api/jenkins-demos/runtime/apply").json()
    assert result["restarted"] is True and jenkins_api["calls"]["restart"] == 1


def test_api_apply_when_stopped_only_saves(jenkins_api):
    jenkins_api["state"]["running"] = False
    result = jenkins_api["client"].post("/api/jenkins-demos/runtime/apply").json()
    assert result["restarted"] is False and "prossimo avvio" in result["message"]
    assert jenkins_api["calls"]["restart"] == 0


def test_api_apply_refuses_restart_with_missing_options(jenkins_api):
    jenkins_api["monkeypatch"].setattr(main, "jenkins_admin_client", _FakeAdmin(active={"default": "deny", "demos": {}}))
    jenkins_api["monkeypatch"].setattr(main.options_manager, "missing_required_options", lambda service, **_k: ["jenkins_token"])
    response = jenkins_api["client"].post("/api/jenkins-demos/runtime/apply")
    assert response.status_code == 400 and "jenkins_token" in response.json()["detail"]
    assert jenkins_api["calls"]["restart"] == 0


# ---------- admin client against a local fake MCP ----------


class _FakeMcp(BaseHTTPRequestHandler):
    key = "chiave-corretta"
    mode = "ok"

    def log_message(self, *args):
        pass

    def _send(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get("X-Admin-Key") != self.key:
            return self._send(401, {"error": "unauthorized"})
        if self.path == "/admin/destinations":
            if _FakeMcp.mode == "jenkins_down":
                return self._send(502, {"error": "impossibile leggere le destinazioni del job da Jenkins: timeout"})
            return self._send(200, {"choices": ["demo", "demo4"], "default_policy": "confirm"})
        if self.path == "/admin/policies":
            return self._send(200, {"default": "confirm", "demos": {"demo4": "allow"}})
        return self._send(404, {})


@pytest.fixture
def fake_mcp():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMcp)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _FakeMcp.mode = "ok"
    port = server.server_address[1]
    service = ServiceDefinition(
        service_id="llm-jenkins-mcp",
        name="LLM Jenkins MCP",
        log_sources=[],
        control=ServiceControlDefinition(
            workdir=Path("."), start_command=["true"], host="127.0.0.1", port=port,
            health_url=f"http://127.0.0.1:{port}/health",
        ),
    )
    yield service
    server.shutdown()


def test_admin_client_sends_key_and_reads_choices_and_policies(fake_mcp):
    client = JenkinsAdminClient(key="chiave-corretta", timeout_seconds=5)
    assert client.destinations(fake_mcp) == ["demo", "demo4"]
    assert client.active_policies(fake_mcp) == {"default": "confirm", "demos": {"demo4": "allow"}}


def test_admin_client_maps_wrong_key_to_restart_hint(fake_mcp):
    with pytest.raises(JenkinsAdminError, match="riavvialo") as exc:
        JenkinsAdminClient(key="sbagliata", timeout_seconds=5).destinations(fake_mcp)
    assert exc.value.status_code == 409


def test_admin_client_passes_jenkins_errors_through(fake_mcp):
    _FakeMcp.mode = "jenkins_down"
    with pytest.raises(JenkinsAdminError, match="impossibile leggere le destinazioni") as exc:
        JenkinsAdminClient(key="chiave-corretta", timeout_seconds=5).destinations(fake_mcp)
    assert exc.value.status_code == 502


def test_admin_client_refuses_non_loopback_health_url(fake_mcp):
    fake_mcp.control.health_url = "http://jenkins-mcp.example:8785/health"
    with pytest.raises(JenkinsAdminError, match="loopback"):
        JenkinsAdminClient(key="x", timeout_seconds=1).destinations(fake_mcp)
