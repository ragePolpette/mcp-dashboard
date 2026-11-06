"""On-demand schema classification for the SQL MCP (the "Classifica schema" button).

The dashboard never classifies anything itself: it runs the SQL MCP CLI
(`anon-catalog classify`, `proposals`, `accept`, `reject`) with the same environment the SQL
service gets (target connection strings from the vault, catalog path, classifier options), so
secrets never leave the process environment and the proposal format has a single owner.
"""

from __future__ import annotations

import json
import subprocess
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CLI_RELATIVE_PATH = Path("src") / "cli" / "anon-catalog.js"
CLI_TIMEOUT_SECONDS = 60
LOG_TAIL_LINES = 40
ALLOWED_PROPOSAL_STATUSES = {"all", "review", "proposed-safe", "proposed-sensitive", "rejected"}
ALLOWED_KINDS = {"name", "org", "email", "phone", "address", "city", "text", "date", "iban"}
MAX_KEYS = 2000


def _clean_keys(keys: list[str]) -> list[str]:
    """Column keys come from the browser and end up as CLI arguments: only schema.table.column."""
    clean = []
    for key in keys or []:
        if not isinstance(key, str):
            continue
        key = key.strip()
        if not key or key.startswith("-") or key.count(".") < 2 or len(key) > 400 or any(ord(ch) < 32 for ch in key):
            raise SqlClassifierError(f"Chiave colonna non valida: {key[:80]}")
        clean.append(key)
    if not clean:
        raise SqlClassifierError("Nessuna colonna selezionata.")
    if len(clean) > MAX_KEYS:
        raise SqlClassifierError("Troppe colonne in una sola richiesta.")
    return clean


class SqlClassifierError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SqlClassifierRunner:
    def __init__(self, state_dir: Path, env_for_service: Callable[[], tuple[Any, dict[str, str]]]):
        """`env_for_service` returns (control definition, full process env) for the SQL service."""
        self.state_dir = Path(state_dir)
        self._env_for_service = env_for_service
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None
        self._meta: dict[str, Any] = {}

    @property
    def status_path(self) -> Path:
        return self.state_dir / "classifier-status.json"

    @property
    def report_path(self) -> Path:
        return self.state_dir / "classifier-report.json"

    @property
    def log_path(self) -> Path:
        return self.state_dir / "classifier-run.log"

    def _command(self, control: Any, args: list[str]) -> list[str]:
        node = str(control.start_command[0]) if control.start_command else "node"
        return [node, str(CLI_RELATIVE_PATH), *args]

    def _require_catalog(self, env: dict[str, str]) -> None:
        if not env.get("ANON_CATALOG_PATH"):
            raise SqlClassifierError("ANON_CATALOG_PATH non configurato per il servizio SQL: catalogo assente.", 409)

    def start(self, target_id: str, *, model: str | None = None, eval_count: int | None = None, force: bool = False) -> dict[str, Any]:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                raise SqlClassifierError("Una classificazione e gia in corso.", 409)
            control, env = self._env_for_service()
            self._require_catalog(env)
            if not target_id or target_id.startswith("-"):
                raise SqlClassifierError("Target non valido.")
            args = ["classify", "--target", target_id, "--status-file", str(self.status_path), "--report", str(self.report_path)]
            if model:
                args += ["--model", model]
            if eval_count:
                args += ["--eval", str(int(eval_count))]
            if force:
                args.append("--force")
            self.state_dir.mkdir(parents=True, exist_ok=True)
            for path in (self.status_path, self.report_path):
                path.unlink(missing_ok=True)
            log_handle = self.log_path.open("w", encoding="utf-8")
            try:
                self._proc = subprocess.Popen(
                    self._command(control, args),
                    cwd=str(control.workdir),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                )
            finally:
                log_handle.close()
            self._meta = {
                "target_id": target_id,
                "mode": "eval" if eval_count else "classify",
                "model": model or env.get("ANON_CLASSIFIER_MODEL") or "",
                "started_at": _now(),
            }
            return self.status()

    def _read_json(self, path: Path) -> dict[str, Any] | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _log_tail(self) -> list[str]:
        try:
            lines = self.log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        return lines[-LOG_TAIL_LINES:]

    def status(self) -> dict[str, Any]:
        proc = self._proc
        running = proc is not None and proc.poll() is None
        exit_code = None if proc is None or running else proc.returncode
        return {
            "running": running,
            "exit_code": exit_code,
            "run": dict(self._meta),
            "progress": self._read_json(self.status_path),
            "report": None if running else self._read_json(self.report_path),
            "log_tail": [] if running or exit_code == 0 else self._log_tail(),
        }

    def _run_cli(self, args: list[str], positional: list[str] | None = None) -> dict[str, Any]:
        control, env = self._env_for_service()
        self._require_catalog(env)
        try:
            completed = subprocess.run(
                # "--" ends option parsing: nothing coming from the browser can become a CLI option.
                self._command(control, [*args, "--json", "--", *(positional or [])]),
                cwd=str(control.workdir),
                env=env,
                capture_output=True,
                text=True,
                timeout=CLI_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SqlClassifierError("La CLI del catalogo non ha risposto in tempo.", 504) from exc
        if completed.returncode not in (0, 1):
            raise SqlClassifierError((completed.stderr or "Errore della CLI del catalogo.").strip()[:300], 400)
        try:
            return json.loads(completed.stdout or "{}")
        except ValueError as exc:
            raise SqlClassifierError((completed.stderr or "Risposta della CLI non valida.").strip()[:300], 502) from exc

    def proposals(self, status: str = "all") -> dict[str, Any]:
        if status not in ALLOWED_PROPOSAL_STATUSES:
            raise SqlClassifierError("Stato proposta non valido.")
        return self._run_cli(["proposals", "--status", status])

    def accept(self, keys: list[str], *, as_verdict: str | None = None, kind: str | None = None, status: str | None = None) -> dict[str, Any]:
        args = ["accept"]
        positional: list[str] = []
        if status:
            if status not in {"proposed-safe", "proposed-sensitive"}:
                raise SqlClassifierError("Si accettano in blocco solo proposed-safe o proposed-sensitive.")
            args += ["--status", status]
        else:
            positional = _clean_keys(keys)
        if as_verdict:
            if as_verdict not in {"safe", "sensitive"}:
                raise SqlClassifierError("Verdetto non valido.")
            args += ["--as", as_verdict]
        if kind:
            if kind not in ALLOWED_KINDS:
                raise SqlClassifierError("Tipo non valido.")
            args += ["--kind", kind]
        return self._run_cli(args, positional)

    def reject(self, keys: list[str]) -> dict[str, Any]:
        return self._run_cli(["reject"], _clean_keys(keys))


__all__ = ["SqlClassifierError", "SqlClassifierRunner"]
