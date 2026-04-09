# MCP Dashboard

MCP Dashboard is a local control plane for managing and observing a workstation-scale MCP stack from one place.

It combines service lifecycle control, structured log inspection, secret-aware runtime options, a local vault, and SQL target registry management in a single dashboard. The project is part of the broader Yetzirah toolchain and is designed for local-first developer environments rather than multi-tenant cloud deployment.

## What It Does

- starts, stops, and restarts MCP services from the UI
- shows runtime state per service, including pid, port, and health
- streams and filters normalized logs from multiple service-specific parsers
- stores reusable local secrets through `vault://` references without exposing cleartext values in the UI
- manages runtime-editable SQL targets exported for `llm-sql-db-mcp`
- exposes read-only admin views for `llm-memory`

## Architecture

The dashboard is split into two layers:

- `backend/`: FastAPI control plane for service management, log ingestion, vault handling, DB target registry, and service-specific proxy endpoints
- `frontend/`: lightweight browser UI for widgets, advanced inspection panels, settings, and operator actions

The backend owns service orchestration and filesystem state under `runtime/`. The frontend stays intentionally thin and consumes the backend API surface.

## Key Capabilities

- Service control: start, stop, restart, and status endpoints for registered services
- Log pipeline: parser chain plus rule engine for enriched events, alerts, and UI filtering
- Secret management: in-memory secret options and persistent local vault references
- DB target registry: runtime editing and export for policy-driven SQL MCP services
- Memory admin proxy: summary, audit, and project views for `llm-memory`

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
- `fastapi`, `uvicorn`, and backend requirements from `backend/requirements.txt`

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

## Status

This repository is in active development. The current codebase is already usable as a local operations dashboard for MCP services, but the public-facing documentation and visual presentation are still being refined.

The current emphasis is on:

- operational clarity for local service stacks
- safer runtime configuration handling
- structured observability for MCP-oriented workflows

## Notes

- This project is local-first and workstation-oriented by design.
- Secret values are never returned in cleartext once stored through the dashboard flows.
- The log pipeline is intentionally extensible so new service parsers and rule sets can be added without redesigning the UI.

## Related Repositories

- `llm-memory`
- `llm_context`
- `llm-bitbucket-mcp`
- `llm-sql-db-mcp`

## Development Process

Built with AI-assisted workflows, while architecture, tradeoffs, integration, review, and validation were directed by the author.
