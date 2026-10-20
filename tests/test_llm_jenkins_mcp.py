"""Tests for the llm-jenkins-mcp service definition, log parser and rule set."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.log_pipeline import LogPipeline  # noqa: E402
from app.log_parsers import parse_with_chain  # noqa: E402
from app.log_rules import LogRuleEngine  # noqa: E402
from app.models import ParsedLogEntry  # noqa: E402

CONFIG = ROOT / "backend" / "config"


def _parse(line: str) -> ParsedLogEntry:
    entry = ParsedLogEntry(
        service_id="llm-jenkins-mcp",
        channel="stderr",
        source_path="/tmp/x.log",
        message="",
    )
    return parse_with_chain(line, entry, ["json", "llm_jenkins_mcp_event"])


def test_jenkins_event_parser_extracts_fields():
    line = (
        '[LLM_JENKINS_MCP] 2026-10-20T09:15:30.123Z tool.call '
        '{"tool":"trigger_demo_deploy","demo":"demo4","branch":"feature/x",'
        '"outcome":"ok","duration_ms":1234}'
    )
    entry = _parse(line)
    assert entry.event == "tool.call"
    assert entry.logger == "LLM_JENKINS_MCP"
    assert entry.timestamp == "2026-10-20T09:15:30.123Z"
    assert entry.fields["tool"] == "trigger_demo_deploy"
    assert entry.fields["demo"] == "demo4"
    assert entry.fields["outcome"] == "ok"
    assert entry.message == "trigger_demo_deploy -> ok"
    assert "llm-jenkins-mcp" in entry.tags


def test_jenkins_event_parser_rejects_other_lines():
    for line in (
        "[LLM_BB_MCP] 2026-10-20T09:15:30.123Z tool.call {}",
        "plain text",
        "[LLM_JENKINS_MCP] not-a-timestamp tool.call {}",
        '[LLM_JENKINS_MCP] 2026-10-20T09:15:30.123Z tool.call {"broken"',
    ):
        entry = _parse(line)
        assert entry.event != "tool.call" or entry.logger != "LLM_JENKINS_MCP"


def _pipeline() -> LogPipeline:
    return LogPipeline(LogRuleEngine(CONFIG / "log_rules.json"))


def _entry(line: str):
    from app.models import ServiceDefinition, ServiceLogSource

    service = ServiceDefinition(
        service_id="llm-jenkins-mcp",
        name="LLM Jenkins MCP",
        log_sources=[ServiceLogSource(path=Path("/tmp/x.log"), channel="stderr")],
        parser_chain=["json", "llm_jenkins_mcp_event"],
        rule_sets=["llm-jenkins-mcp"],
    )
    return _pipeline().parse_line(service=service, source=service.log_sources[0], line=line)


def test_rule_set_marks_successful_trigger_as_deploy():
    entry = _entry(
        '[LLM_JENKINS_MCP] 2026-10-20T09:15:30.123Z tool.call '
        '{"tool":"trigger_demo_deploy","demo":"demo4","branch":"feature/x",'
        '"outcome":"ok","duration_ms":1234}'
    )
    assert entry.event == "jenkins.deploy.triggered"
    assert entry.level == "INFO"
    assert "deploy" in entry.tags and "write" in entry.tags


def test_rule_set_marks_rejected_call():
    entry = _entry(
        '[LLM_JENKINS_MCP] 2026-10-20T09:15:30.123Z tool.call '
        '{"tool":"trigger_demo_deploy","demo":"demo4","branch":"main; rm -rf /",'
        '"outcome":"rejected","duration_ms":1,"error":"ERRORE: nome branch non valido"}'
    )
    assert entry.event == "jenkins.tool.rejected"
    assert entry.level == "WARN"
    assert "rejected" in entry.tags


def test_rule_set_marks_error_call():
    entry = _entry(
        '[LLM_JENKINS_MCP] 2026-10-20T09:15:30.123Z tool.call '
        '{"tool":"get_demo_status","demo":"demo3","outcome":"error","duration_ms":42,'
        '"error":"ERRORE: timeout nella chiamata a Jenkins."}'
    )
    assert entry.event == "jenkins.tool.error"
    assert entry.level == "ERROR"


def test_rule_set_marks_auth_error():
    entry = _entry(
        '[LLM_JENKINS_MCP] 2026-10-20T09:15:30.123Z tool.call '
        '{"tool":"get_demo_status","demo":"demo3","outcome":"error","duration_ms":42,'
        '"error":"ERRORE: Chiamata a Jenkins: HTTP 401, credenziali non valide."}'
    )
    assert entry.event == "jenkins.auth_error"
    assert entry.level == "ERROR"
    assert "security" in entry.tags


def test_services_config_defines_llm_jenkins_mcp():
    config = json.loads((CONFIG / "services.json").read_text(encoding="utf-8"))
    services = {s["id"]: s for s in config["services"]}
    assert "llm-jenkins-mcp" in services
    svc = services["llm-jenkins-mcp"]
    assert svc["control"]["port"] == 8785
    assert svc["control"]["host"] == "127.0.0.1"
    assert svc["control"]["health_url"] == "http://127.0.0.1:8785/health"
    assert svc["parser_chain"] == ["json", "llm_jenkins_mcp_event"]
    assert svc["rule_sets"] == ["llm-jenkins-mcp"]
    options = {o["id"]: o for o in svc["control"]["options"]}
    assert options["jenkins_token"]["secret"] is True
    assert options["jenkins_token"]["required"] is True
    assert options["jenkins_url"]["secret"] is False
    assert options["jenkins_user"]["secret"] is False
    assert options["jenkins_allowed_demos"]["required"] is False
    env_vars = {o["env_var"] for o in svc["control"]["options"]}
    assert env_vars == {"JENKINS_URL", "JENKINS_USER", "JENKINS_TOKEN", "JENKINS_ALLOWED_DEMOS"}


def test_alerts_config_has_jenkins_rules():
    config = json.loads((CONFIG / "alerts.json").read_text(encoding="utf-8"))
    rules = config["services"].get("llm-jenkins-mcp")
    assert rules, "nessuna regola alert per llm-jenkins-mcp"
    events = {r["event"] for r in rules}
    assert "jenkins.auth_error" in events
    assert "jenkins.config_invalid" in events
