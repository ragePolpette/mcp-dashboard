# Changelog

## Unreleased

### Added

- LLM Jenkins MCP > Destinazioni: registry of deploy destinations by exact name with an `allow`, `confirm` or `deny` policy, plus a default policy for unlisted destinations (`confirm` or `deny`, never `allow`). Stored in `runtime/jenkins_demo_policies.json` and passed to the service as `JENKINS_DEMO_POLICIES`.
- "Aggiorna da Jenkins" reads the job's `DESTINAZIONE` choices through the running MCP (`POST /api/jenkins-demos/discover`, read-only `/admin/destinations` on loopback) and lists the destinations still to classify. The dashboard has no Jenkins credentials; it authenticates to the MCP with a key generated per dashboard process (`JENKINS_MCP_ADMIN_KEY`), never persisted.
- "Applica" (`POST /api/jenkins-demos/runtime/apply`) restarts the Jenkins service only when its active registry (`/admin/policies`) differs from the saved one.
- Jenkins rule set and alerts for queued deploys, two-step confirmations (`confirm.requested/used/expired/invalid`), denied admin requests and configuration warnings.

### Security

- State-changing API requests (`POST`, `PUT`, `PATCH`, `DELETE`) now require the `X-Requested-With: mcp-dashboard` header and the per-process session token in `X-Dashboard-Token`. Requests whose `Origin` or `Referer` is not the dashboard itself are rejected with `403`. Scripts calling the API must add both headers; the token is available in `runtime/dashboard_session.token` (mode `0600`) and through `GET /api/session`.
- Requests with a `Host` header outside `localhost`, `127.0.0.1` and `::1` are rejected with `400`. Set `MCP_DASHBOARD_ALLOWED_HOSTS` to a comma-separated list to allow other names.
- Vault references are restricted to letters, digits, `_`, `-` and single dots. Slashes, colons and `..` are rejected for new references, and ciphertext paths are verified to stay inside the vault store. Existing references that already contain slashes or colons remain usable.
- Deleting a vault secret now requires an unlocked vault. The API answers `423` while it is locked.
- The vault locks itself after 30 minutes without vault activity. Configure it with the `vault_auto_lock_minutes` preference; `0` disables it.
- While the vault is locked, `GET /api/vault` returns reference names only, without timestamps, and an empty `ref_usage`.
- API error details, alert names and messages, vault references and service names are HTML-escaped in the UI.

### Fixed

- Vault usage for DB targets is shown as `DB target <id>` instead of `undefined.undefined`.
- Vault metadata, ciphertexts and the dashboard state files (`db_targets.json`, `bitbucket_repositories.json`, `service_options.json`, `dashboard_settings.json`) are written atomically. Concurrent vault updates no longer lose entries.
- Log pruning rewrites files in place line by line instead of loading them into memory, and clearing logs truncates them in place, so services that keep their log files open keep writing to them.
- Log text filters match field values instead of serialized JSON, so searching a key name no longer matches every entry and non-ASCII text is found.
- `Kill 'em All` now asks uvicorn for a graceful shutdown and only forces the exit after 10 seconds.
- Creating the per-service process lock is now thread-safe.

### Changed

- The `json` log parser also reads the .NET JSON console formatter keys (`Timestamp`, `LogLevel`, `Category`, `Message`), so .NET services get their own level and timestamp instead of the ingestion time.
- `JENKINS_ALLOWED_DEMOS` is no longer a Jenkins MCP option: destinations are managed in the registry.
- Service status is refreshed by a background poller (every 3 seconds, `MCP_DASHBOARD_STATUS_POLL_SECONDS`) and served from a cache. Start, stop and restart invalidate it.
- Live log streaming reads files in a worker thread and only emits complete lines.
- Added `pyproject.toml` with ruff and pytest configuration, `requirements-dev.txt`, and a `package.json` with `npm test`. CI now runs `ruff check`.
