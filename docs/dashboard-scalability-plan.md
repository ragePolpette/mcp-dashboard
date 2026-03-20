# Dashboard Scalability Plan

## Goal

Prepare `mcp-dashboard` for the next 2 MCP services without growing the current
hardcoded layout and service-specific UI rules.

This plan addresses two problems together:

1. service-specific branching is growing in `frontend/app.js`
2. the current home card layout does not scale well when more MCP services are added

Target result:

- home = compact responsive grid of service cards
- advanced panel = full single-service workspace
- service rendering = driven by registry metadata and capabilities, not by ad hoc `service_id` checks

## Current Pain Points

### Data / control model

- `backend/config/services.json` currently defines services, but the frontend still
  relies on hardcoded checks like:
  - `isDbService(serviceId)`
  - `isActivityService(serviceId)`
- feature support is inferred from ids instead of declared as service metadata
- onboarding a new MCP currently risks touching multiple places in the UI logic

### Visual model

- cards already carry too much content:
  - status
  - metrics
  - trend
  - multiple log previews
  - actions
- with 2 more MCPs, the side-by-side layout becomes too dense
- the advanced panel already has the richer information density needed for operations,
  so the home view should stop trying to be a mini-detail view

## Target UI Model

### Home

Home should become an operational overview.

Each card should show only:

- service name
- state badge
- host/port
- PID
- latest event summary
- one compact metrics line, only if useful for that service kind
- actions:
  - `Aggiorna`
  - `Start`
  - `Stop`
  - `Restart`
  - `Avanzate`

Each card should **not** try to embed:

- multiple preview log entries
- large metric blocks
- full query previews
- duplicated detail already available in the advanced panel

### Advanced panel

The advanced panel becomes the complete workspace for one service.

Possible sections:

- overview
- startup/runtime options
- alerts
- query inspector
- activity
- logs

Section visibility should be driven by service capabilities.

## Target Service Model

Extend `backend/config/services.json` with a light registry model:

```json
{
  "id": "llm-context",
  "name": "LLM Context",
  "kind": "rag",
  "group": "knowledge",
  "capabilities": [
    "logs",
    "activity",
    "alerts",
    "runtime_options",
    "health_details"
  ]
}
```

### Proposed `kind` values

- `db`
- `rag`
- `memory`
- `ops`
- `custom`

### Proposed `group` values

- `database`
- `knowledge`
- `runtime`
- `custom`

### Proposed `capabilities`

- `logs`
- `alerts`
- `runtime_options`
- `query_inspector`
- `activity`
- `health_details`
- `project_status`
- `scope_overview`

The first pass only needs the capabilities already supported by the dashboard.

## Capability Mapping For Current Services

### `llm-context`

- `kind`: `rag`
- `group`: `knowledge`
- `capabilities`:
  - `logs`
  - `activity`
  - `alerts`
  - `runtime_options`
  - `health_details`

### `llm-memory`

- `kind`: `memory`
- `group`: `knowledge`
- `capabilities`:
  - `logs`
  - `activity`
  - `alerts`
  - `runtime_options`
  - `health_details`

### `llm-db-dev-mcp`

- `kind`: `db`
- `group`: `database`
- `capabilities`:
  - `logs`
  - `query_inspector`
  - `alerts`
  - `runtime_options`
  - `health_details`

### `llm-db-prod-mcp`

- `kind`: `db`
- `group`: `database`
- `capabilities`:
  - `logs`
  - `query_inspector`
  - `alerts`
  - `runtime_options`
  - `health_details`

## Frontend Refactor Target

The current frontend should move from id-based conditions to capability-based
helpers.

Current logic to replace:

- `isDbService(serviceId)`
- `isActivityService(serviceId)`

Target helpers:

- `serviceKind(service)`
- `serviceGroup(service)`
- `hasCapability(service, capability)`
- `supportsQueryInspector(service)`
- `supportsActivity(service)`
- `supportsAlerts(service)`
- `supportsRuntimeOptions(service)`

This change should happen before adding the next MCP services.

## Home Card Redesign

### Current direction to reduce

- large list previews
- stacked KPI blocks
- stacked trend and multi-row details

### Target compact card structure

1. header
   - name
   - status
2. meta line
   - host/port
   - PID
3. latest event line
   - compact single-line preview
4. compact service-specific summary line
   - one line only
5. actions row

### Responsive behavior

- desktop wide: `repeat(auto-fit, minmax(280px, 1fr))`
- medium width: naturally falls to 2 columns
- narrow width: single column

The card should stop trying to be a rich console.

## Advanced Panel Target Structure

The advanced panel should remain the place for dense information.

Recommended order:

1. service title + runtime meta
2. runtime options
3. alerts
4. query inspector or activity
5. logs

Rules:

- DB services show `Query Inspector`
- RAG / Memory services show `Activity`
- logs always remain available
- future sections should be capability-gated, not id-gated

## Backend Changes Needed In Next Implementation Step

### `backend/config/services.json`

Add:

- `kind`
- `group`
- `capabilities`

No runtime behavior change is required in this file beyond extra metadata.

### `backend/app/main.py`

Minimal backend changes expected:

- no major API redesign needed
- keep existing endpoints
- only add or adjust fields if the frontend needs a compact overview payload later

The current endpoints are already enough for a first UI scalability pass.

## Frontend Changes Needed In Next Implementation Step

### `frontend/app.js`

Main responsibilities:

- replace service-id branching with capability checks
- simplify card rendering
- keep advanced panel rendering dynamic by capability
- preserve:
  - `Query Inspector`
  - `Activity`
  - `Alerts`
  - runtime options

### `frontend/index.html`

Likely only light structural changes are needed:

- keep the existing grid root
- keep one advanced panel
- do not create per-service detailed sections in the home layout

### `frontend/styles.css`

Main work:

- shrink card density
- rebalance spacing
- keep clear separation between overview and detailed workspace
- preserve current visual language unless readability forces a change

## Non-Goals For The Next Step

Do not include these yet:

- terminal/console embedding
- full plugin architecture
- project-centric dashboard view
- runtime profiles
- drag-and-drop layout
- multi-page navigation

Those are later-scale features and are not needed to absorb 2 more MCP services.

## Suggested Implementation Order

1. extend `services.json` with `kind`, `group`, `capabilities`
2. refactor `frontend/app.js` to read capabilities instead of checking ids
3. simplify home card rendering
4. keep advanced panel feature parity
5. verify current 4 MCP services still render correctly
6. only then add the next 2 MCP services

## Acceptance Criteria

The next implementation step should be considered done when:

- adding a new MCP mostly requires a new `services.json` entry
- the home page remains readable with 6 services
- the advanced panel still exposes query/activity/log workflows without regression
- the frontend no longer relies on service-specific behavior hidden in multiple branches

## Practical Recommendation

Implement this as one dedicated dashboard refactor PR before onboarding the next
2 MCPs.

That PR should be intentionally scoped to:

- service metadata
- capability-driven rendering
- compact home cards
- unchanged operational semantics

This gives the next MCP onboarding step a stable base and avoids a second UI rewrite.
