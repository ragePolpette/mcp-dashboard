from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402
from app.sql_classifier import SqlClassifierError, SqlClassifierRunner, _clean_keys  # noqa: E402
from dashboard_client import dashboard_client  # noqa: E402

# Stand-in for `node src/cli/anon-catalog.js`: echoes its argv as JSON, or writes status/report files.
FAKE_CLI = """
import json, sys, time
args = sys.argv[1:]
if args and args[0] == "classify":
    status = args[args.index("--status-file") + 1]
    report = args[args.index("--report") + 1]
    time.sleep(0.3)
    open(report, "w").write(json.dumps({"mode": "classify", "model": "m", "counts": {"review": 1}, "errors": []}))
    open(status, "w").write(json.dumps({"state": "done"}))
    sys.exit(0)
print(json.dumps({"argv": args, "accepted": [], "skipped": [], "rejected": [], "proposals": [], "runs": []}))
"""


def _runner(tmp: str, *, catalog: bool = True) -> SqlClassifierRunner:
    workdir = Path(tmp) / "sql"
    (workdir / "src" / "cli").mkdir(parents=True)
    (workdir / "src" / "cli" / "anon-catalog.js").write_text(FAKE_CLI, encoding="utf-8")
    control = SimpleNamespace(start_command=[sys.executable], workdir=workdir)
    env = {"PATH": "", "ANON_CATALOG_PATH": str(Path(tmp) / "c.json")} if catalog else {"PATH": ""}
    return SqlClassifierRunner(Path(tmp) / "state", lambda: (control, env))


def test_column_keys_from_the_browser_cannot_become_cli_options():
    assert _clean_keys(["dbo.t.c", " sys.tables.name "]) == ["dbo.t.c", "sys.tables.name"]
    for bad in (["--file=/etc/passwd"], ["dbo.t"], ["dbo.t.c\nx"], []):
        with pytest.raises(SqlClassifierError):
            _clean_keys(bad)


def test_accept_and_reject_pass_keys_after_the_option_terminator():
    with tempfile.TemporaryDirectory() as tmp:
        runner = _runner(tmp)
        argv = runner.accept(["dbo.t.c"], as_verdict="sensitive", kind="name")["argv"]
        assert argv == ["accept", "--as", "sensitive", "--kind", "name", "--json", "--", "dbo.t.c"]
        assert runner.reject(["dbo.t.c"])["argv"] == ["reject", "--json", "--", "dbo.t.c"]
        assert runner.accept([], status="proposed-safe")["argv"] == ["accept", "--status", "proposed-safe", "--json", "--"]
        with pytest.raises(SqlClassifierError):
            runner.accept(["dbo.t.c"], kind="invented")
        with pytest.raises(SqlClassifierError):
            runner.proposals("anything")


def test_classification_runs_in_background_and_one_at_a_time():
    with tempfile.TemporaryDirectory() as tmp:
        runner = _runner(tmp)
        started = runner.start("dev-main", model="m")
        assert started["running"] is True
        with pytest.raises(SqlClassifierError) as busy:
            runner.start("dev-main")
        assert busy.value.status_code == 409
        for _ in range(50):
            if not runner.status()["running"]:
                break
            time.sleep(0.1)
        status = runner.status()
        assert status["exit_code"] == 0
        assert status["report"]["counts"] == {"review": 1}
        assert status["progress"]["state"] == "done"


def test_classifier_needs_a_catalog():
    with tempfile.TemporaryDirectory() as tmp:
        runner = _runner(tmp, catalog=False)
        with pytest.raises(SqlClassifierError) as missing:
            runner.start("dev-main")
        assert missing.value.status_code == 409


def test_classifier_api_rejects_unknown_targets():
    client = dashboard_client(app)
    response = client.post("/api/sql-classifier/run", json={"target_id": "no-such-target"})
    assert response.status_code == 404
    status = client.get("/api/sql-classifier/status")
    assert status.status_code == 200
    assert status.json()["running"] is False


def test_sql_service_exposes_the_classifier_model_option():
    client = dashboard_client(app)
    option_ids = {item["id"] for item in client.get("/api/services/llm-sql-db-mcp/options").json()["options"]}
    assert "anon_classifier_model" in option_ids
    assert json.loads(json.dumps(sorted(option_ids)))
