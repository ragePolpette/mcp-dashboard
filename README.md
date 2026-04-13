# MCP Dashboard

`mcp-dashboard` is a local control plane for running and observing a workstation-scale MCP stack from one place.

It combines service lifecycle control, structured log inspection, secret-aware runtime options, a local vault, SQL target registry management, and a service-specific admin surface for `llm-memory`.

## What It Does

- starts, stops, and restarts MCP services from the UI
- shows runtime state per service, including pid, port, health, and recent events
- streams and filters normalized logs from multiple service-specific parsers
- stores reusable local secrets through `vault://` references without exposing cleartext values in the UI
- manages runtime-editable SQL targets exported for `llm-sql-db-mcp`
- exposes `llm-memory` admin views for summary, audit, projects, fast-memory candidates, and distillation runs

## Architecture

The dashboard is split into two layers:

- `backend/`: FastAPI control plane for service management, log ingestion, vault handling, DB target registry, and service-specific proxy endpoints
- `frontend/`: browser UI for service cards, advanced panels, settings, and operator workflows

The backend owns orchestration and filesystem state under `runtime/`. The frontend stays intentionally thin and consumes the backend API surface.

## Key Capabilities

- Service control: start, stop, restart, and status endpoints for registered services
- Log inspection: normalized logs, alerts, activity, and query inspection per service capability
- Secret-aware runtime options: local vault references without round-tripping cleartext values
- DB target registry: local editing and runtime export for policy-driven SQL MCP services
- Memory admin proxy: summary, audit, projects, candidate queue, distillation workflow, and run history for `llm-memory`

## Project Layout

```text
mcp-dashboard/
├── backend/
│   ├── app/
│   └── config/
├── frontend/
├── runtime/
├── tests/
└── start-dashboard.ps1
```

## Run Locally

Requirements:

- Python 3.11+
- backend dependencies from `backend/requirements.txt`

Quick start on Windows:

```powershell
pwsh -ExecutionPolicy Bypass -File .\start-dashboard.ps1
```

Optional hot reload:

```powershell
pwsh -ExecutionPolicy Bypass -File .\start-dashboard.ps1 -Reload
```

Default endpoints:

- UI: `http://127.0.0.1:8790/`
- Health: `http://127.0.0.1:8790/health`

## Main API Surface

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

## Security Model

This dashboard is designed to make local operator workflows safer without pretending to be a cloud secret-management platform.

The key rules are:

- services consume `vault://` references instead of hardcoded secrets where possible
- the UI works with secret-aware runtime options rather than round-tripping cleartext values
- secret values are not returned in cleartext once stored through dashboard flows
- service-specific admin actions are proxied through explicit backend endpoints instead of exposing raw shell access

## Status

The project is usable today as a local operations dashboard for MCP services and is oriented toward serious workstation and small-team environments rather than public cloud deployment.

## Related Repositories

- `llm-memory`
- `llm_context`
- `llm-bitbucket-mcp`
- `llm-sql-db-mcp`
