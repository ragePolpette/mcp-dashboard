"""Tests for extensible log pipeline."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.log_pipeline import LogPipeline  # noqa: E402
from app.log_rules import LogRuleEngine  # noqa: E402
from app.models import ServiceDefinition, ServiceLogSource  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def test_rule_engine_enriches_llm_memory_compliance_events():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        rules_path = tmp_dir / "rules.json"
        _write_json(
            rules_path,
            {
                "rule_sets": {
                    "default": [],
                    "llm-memory": [
                        {
                            "regex": "WRITER_MODEL_UNTRUSTED",
                            "set": {"event": "memory.compliance_reject", "level": "WARN"},
                            "add_tags": ["memory", "compliance"],
                        }
                    ],
                }
            },
        )

        engine = LogRuleEngine(rules_path)
        pipeline = LogPipeline(engine)
        service = ServiceDefinition(
            service_id="llm-memory",
            name="LLM Memory",
            log_sources=[ServiceLogSource(path=tmp_dir / "dummy.log", channel="stderr")],
            parser_chain=["json", "python", "uvicorn_access", "node_deprecation"],
            rule_sets=["llm-memory"],
        )

        entry = pipeline.parse_line(
            service=service,
            source=service.log_sources[0],
            line='{"message":"WRITER_MODEL_UNTRUSTED","level":"ERROR"}',
        )
        assert entry.event == "memory.compliance_reject"
        assert entry.level == "WARN"
        assert "memory" in entry.tags


def test_pipeline_keeps_dynamic_fields_for_ui_rendering():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        rules_path = tmp_dir / "rules.json"
        _write_json(rules_path, {"rule_sets": {"default": []}})

        engine = LogRuleEngine(rules_path)
        pipeline = LogPipeline(engine)
        service = ServiceDefinition(
            service_id="llm-context",
            name="LLM Context",
            log_sources=[ServiceLogSource(path=tmp_dir / "dummy.log", channel="stderr")],
            parser_chain=["json"],
            rule_sets=[],
        )
        entry = pipeline.parse_line(
            service=service,
            source=service.log_sources[0],
            line='{"message":"hello","level":"INFO","event":"x","custom_field":"abc","custom_num":7}',
        )
        assert entry.fields["custom_field"] == "abc"
        assert entry.fields["custom_num"] == 7


def test_pipeline_keeps_fallback_timestamp_for_plain_text_logs():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        rules_path = tmp_dir / "rules.json"
        _write_json(rules_path, {"rule_sets": {"default": []}})

        engine = LogRuleEngine(rules_path)
        pipeline = LogPipeline(engine)
        service = ServiceDefinition(
            service_id="llm-db-dev-mcp",
            name="LLM DB DEV MCP",
            log_sources=[ServiceLogSource(path=tmp_dir / "dummy.log", channel="stdout")],
            parser_chain=["json", "python", "uvicorn_access", "node_deprecation"],
            rule_sets=[],
        )
        fallback_timestamp = datetime.now().astimezone().isoformat()
        entry = pipeline.parse_line(
            service=service,
            source=service.log_sources[0],
            line="llm-db-dev-mcp listening at http://127.0.0.1:8781/mcp",
            fallback_timestamp=fallback_timestamp,
        )

        assert entry.event == "log.line"
        assert entry.timestamp == fallback_timestamp
