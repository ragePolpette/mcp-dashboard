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

Other files in `backend/config/`: `alerts.json`, `log_rules.json` (see `log_rules.example.json`), and `db_targets.bootstrap.json`. Runtime state, including the vault, is written under `runtime/`.

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
- `GET /api/services/{service_id}/memory-admin/summary`
- `GET /api/services/{service_id}/memory-admin/candidates`
- `GET /api/services/{service_id}/memory-admin/distillation/runs`
- `POST /api/services/{service_id}/memory-admin/distillation/prepare`
- `POST /api/services/{service_id}/memory-admin/distillation/apply`

For the SQL target workflow, see [docs/sql-connections.md](docs/sql-connections.md). Validation notes for Max Result Bytes and multi-target handling are in [docs/ANY_BYTES_MULTI_TARGET_VALIDATION.md](docs/ANY_BYTES_MULTI_TARGET_VALIDATION.md).

## Security

The dashboard is meant for local operator workflows. It is not a cloud secret-management platform.

- Services consume `vault://` references instead of hardcoded secrets where possible
- The UI works with secret-aware runtime options and does not round-trip cleartext values
- Secret values are not returned in cleartext once stored through dashboard flows
- Service-specific admin actions go through explicit backend endpoints, not raw shell access
- The backend does not implement API authentication, so bind it to `127.0.0.1` (the default)

See [SECURITY.md](SECURITY.md) for the threat model and how to report vulnerabilities.

## Development

```bash
pip install -r backend/requirements.txt pytest httpx
python -m pytest -q
node --test tests/*.cjs
```

The Node tests need Node 22 and no npm dependencies. No linter is configured. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Project status

Usable as a local operations dashboard for MCP services, oriented toward workstation and small-team environments rather than public cloud deployment.

## Related projects

- `llm-memory`
- `llm_context`
- `llm-bitbucket-mcp`
- `llm-sql-db-mcp`

## License

MIT. See [LICENSE](LICENSE).
