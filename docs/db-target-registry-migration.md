# DB Target Registry Migration

## Goal

Move the dashboard away from the static `dev-main` / `prod-main` model and make DB targets a first-class registry object.

## Ownership Model

The dashboard should be the source of truth for:

- target identity
- environment
- active/disabled state
- read/write policy
- anonymization policy
- provider/model selection
- limits
- vault references for connection material

The SQL MCP server should consume an exported runtime snapshot, not dashboard internals.

## Recommended Registry Shape

Persisted dashboard state should keep the full control-plane model, while the export to the MCP server should trim secret material.

Persisted fields:

- `target_id`
- `display_name`
- `environment`
- `status`
- `connection_ref`
- `read_enabled`
- `write_enabled`
- `anonymization_enabled`
- `anonymization_mode`
- `llm_provider`
- `llm_model`
- `max_rows`
- `max_result_bytes`
- any dashboard-specific notes

Exported runtime fields:

- same safety metadata
- resolved policy view
- no secret values

## Migration Flow

1. Bootstrap the registry from the existing legacy DB targets.
2. Convert connection strings to vault refs where possible.
3. Mark `environment=prod` targets as fenced and immutable in policy.
4. Export a runtime registry file for `llm-sql-db-mcp`.
5. Stop treating `dev-main` / `prod-main` as special cases in the UI.

## Current Incompatibilities

The current dashboard state still assumes the old service registry model in several places:

- `backend/config/services.json` is static and still contains target-specific option fields for the SQL MCP service.
- `backend/app/main.py` does not expose CRUD APIs for DB targets yet.
- the frontend can render options and vault-backed secrets, but it has no dedicated DB target admin surface.
- the dashboard vault integration exists, but it is currently scoped to service options rather than a DB target registry export.

That means the migration must be staged. The dashboard can seed and export the new registry, but it should not require a full UI rewrite first.

## Hardening Rules

The dashboard must not expose a control that can weaken prod guarantees.

That means:

- no write toggle for prod unless policy explicitly allows it
- no UI path that disables prod anonymization
- no cleartext secret persistence in service option state
- no coupling between UI defaults and prod policy

## Operational Risk

The dangerous failure mode is stale export data.

If the dashboard writes a new registry but the MCP server still sees an old file, the system will diverge.
Use atomic writes and an explicit refresh contract rather than manual edits.

## Rollout Checklist

Before any deploy, verify:

- the registry file contains both imported legacy targets
- `prod` targets still load with write disabled and anonymization enabled
- `db_write` is denied on prod even if the registry is malformed or overridden
- vault refs resolve cleanly for the connection secret path used by the dashboard
- the dashboard export path does not leak connection strings

## Practical Next Step

Treat the dashboard registry as the authoritative model and add a small migration layer that converts the old two-target setup into the new registry without changing the query engine.
