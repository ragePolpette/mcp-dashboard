# AGENTS.md (mcp-dashboard)

Regole locali per il progetto `mcp-dashboard`.

## Scope
- Valido solo sotto `mcp-dashboard/`.

## Obiettivo
- Dashboard locale per gestione e monitoring MCP.
- In questa fase: pipeline log estensibile (sources + parsers + rules + UI dinamica).

## Regole implementative
- Nessun comando shell arbitrario esposto via API.
- Config servizi e regole in JSON versionato.
- Nuove voci log devono essere supportabili via `log_rules.json` senza patch frontend.

## File chiave
- `backend/config/services.json`
- `backend/config/log_rules.json`
- `backend/app/log_parsers.py`
- `backend/app/log_rules.py`
- `backend/app/log_pipeline.py`
