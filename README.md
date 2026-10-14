# MCP Dashboard

[![CI](https://github.com/ragePolpette/mcp-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/ragePolpette/mcp-dashboard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

A local control plane for running and observing a workstation-scale MCP stack from one place.

## Overview

`mcp-dashboard` combines service lifecycle control, structured log inspection, secret-aware runtime options, a local vault, SQL target registry management, and a service-specific admin surface for `llm-memory`.

## Features

- Start, stop, and restart MCP services from the UI
- Runtime state per service, including pid, port, health, and recent events
- Normalized logs from multiple service-specific parsers, with filtering, alerts, and activity views
- Reusable local secrets stored through `vault://` references, without exposing cleartext values in the UI
- Runtime-editable SQL targets exported for `llm-sql-db-mcp`
- `llm-memory` admin views for summary, audit, projects, fast-memory candidates, and distillation runs

## Architecture

- `backend/`: FastAPI control plane for service management, log ingestion, vault handling, the DB target registry, and service-specific proxy endpoints
- `frontend/`: browser UI for service cards, advanced panels, settings, and operator workflows
- `modules/local_secret_vault/`: local encrypted secret store used by the backend (scrypt key derivation, AES-GCM encryption)

The backend owns orchestration and filesystem state under `runtime/`. The frontend is a thin client of the backend API.

```text
mcp-dashboard/
├── backend/
│   ├── app/
│   └── config/
├── docs/
├── frontend/
├── modules/
├── runtime/        (created at run time, git-ignored)
├── tests/
└── start-dashboard.ps1
```

## Quick start

Requirements: Python 3.11 or newer.

```bash
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt    # Windows: .venv\Scripts\pip
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8790
```

On Windows, `start-dashboard.ps1` wraps the same uvicorn command. It uses `.venv\Scripts\python.exe` if present and otherwise the `python` on `PATH`:

```powershell
pwsh -ExecutionPolicy Bypass -File .\start-dashboard.ps1
pwsh -ExecutionPolicy Bypass -File .\start-dashboard.ps1 -Reload
```

Default endpoints:

- UI: `http://127.0.0.1:8790/`
- Health: `http://127.0.0.1:8790/health`

## Configuration

Service definitions live in `backend/config/services.json`. `backend/config/services.example.json` shows the expected shape: id, name, parser chain, rule sets, and a `control` block with working directory, start command, host, port, pid file, log files, environment, and runtime options. Options marked `secret` are resolved from the vault.

Other files in `backend/config/`: `alerts.json`, `log_rules.json` (see `log_rules.example.json`), and `db_targets.bootstrap.json`. Runtime state, including the vault, is written under `runtime/`. State files are written atomically (temporary file plus rename), so an interrupted write never leaves a truncated JSON file behind.

Environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MCP_DASHBOARD_ALLOWED_HOSTS` | `localhost,127.0.0.1,::1` | Comma-separated host names accepted in the `Host` header. `*` disables the check. |
| `MCP_DASHBOARD_STATUS_POLL_SECONDS` | `3` | Interval of the background poller that refreshes service status. |

Dashboard preferences (Control Center > Dashboard) include `vault_auto_lock_minutes` (default 30, `0` disables auto-lock).

## Usage

Main API endpoints:

- `GET /api/services`
- `GET /api/services/{service_id}/status`
- `POST /api/services/{service_id}/start`
- `POST /api/services/{service_id}/stop`
- `POST /api/services/{service_id}/restart`
- `GET /api/services/{service_id}/logs`
- `GET /api/vault`
- `GET /api/db-targets`
- `GET /api/session` (returns the session token, see Security)
- `GET /api/services/{service_id}/memory-admin/summary`
- `GET /api/services/{service_id}/memory-admin/candidates`
- `GET /api/services/{service_id}/memory-admin/distillation/runs`
- `POST /api/services/{service_id}/memory-admin/distillation/prepare`
- `POST /api/services/{service_id}/memory-admin/distillation/apply`

State-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) must send `X-Requested-With: mcp-dashboard` and `X-Dashboard-Token: <token>`. Scripts on the same machine can read the token from `runtime/dashboard_session.token`:

```bash
TOKEN=$(cat runtime/dashboard_session.token)
curl -X POST http://127.0.0.1:8790/api/services/llm-memory/restart \
  -H "X-Requested-With: mcp-dashboard" -H "X-Dashboard-Token: $TOKEN"
```

For the SQL target workflow, see [docs/sql-connections.md](docs/sql-connections.md). Validation notes for Max Result Bytes and multi-target handling are in [docs/ANY_BYTES_MULTI_TARGET_VALIDATION.md](docs/ANY_BYTES_MULTI_TARGET_VALIDATION.md).

## Security

The dashboard is meant for local operator workflows. It is not a cloud secret-management platform.

- Services consume `vault://` references instead of hardcoded secrets where possible
- The UI works with secret-aware runtime options and does not round-trip cleartext values
- Secret values are not returned in cleartext once stored through dashboard flows
- Service-specific admin actions go through explicit backend endpoints, not raw shell access
- The backend does not implement user authentication, so bind it to `127.0.0.1` (the default)

### Request protection

- **Trusted hosts**: every request must carry a `Host` header listed in `MCP_DASHBOARD_ALLOWED_HOSTS` (loopback names by default). Requests for other host names get `400`, which also blocks DNS rebinding.
- **Origin check**: state-changing requests that send an `Origin` (or, without it, a `Referer`) must come from the dashboard itself (same scheme, host and port). Anything else, including `Origin: null`, gets `403`.
- **CSRF marker**: state-changing requests must send `X-Requested-With: mcp-dashboard`. A plain HTML form on another site cannot set it.
- **Session token**: the backend generates a random token at start-up and requires it as `X-Dashboard-Token` on every state-changing request, including `kill-all` and vault deletions. The bundled frontend reads it from `GET /api/session`; local scripts can read `runtime/dashboard_session.token`, written with mode `0600` and removed on shutdown. The token changes on every restart.

If you expose the dashboard on a LAN by extending `MCP_DASHBOARD_ALLOWED_HOSTS`, anyone who can reach the port can still obtain the token and control the services. Put an authenticating reverse proxy in front of it in that case.

### Vault

- Vault references use letters, digits, `_` and `-`, with single dots as separators (for example `vault://db.dev.main`). Slashes, colons and `..` are rejected for new references; references created earlier with slashes or colons keep working as long as they resolve inside the vault store.
- The vault locks itself after `vault_auto_lock_minutes` without vault activity (unlock, save, delete). Resolving secrets for services does not count as activity. Set it to `0` to disable auto-lock.
- While the vault is locked, `GET /api/vault` lists reference names only, without timestamps or usage. Deleting a secret requires an unlocked vault.

See [SECURITY.md](SECURITY.md) for the threat model and how to report vulnerabilities.

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
python -m pytest -q
npm test            # same as: node --test tests/*.cjs
```

The Node tests need Node 22 and no npm dependencies. Ruff and pytest are configured in `pyproject.toml`. See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).

## Project status

Usable as a local operations dashboard for MCP services, oriented toward workstation and small-team environments rather than public cloud deployment.

## Related projects

- `llm-memory`
- `llm_context`
- `llm-bitbucket-mcp`
- `llm-sql-db-mcp`

## License

MIT. See [LICENSE](LICENSE).
