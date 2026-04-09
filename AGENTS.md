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

## Dependency Policy
- Se modifichi `backend/requirements*.txt`, `package.json`, `package-lock.json` o altri manifest dipendenze del repo, esegui `node ..\..\dependency-policy\dependency-policy-check.mjs --repo . --mode auto` prima di chiudere il task.
- Se il check fallisce, il task non va considerato concluso senza eccezione approvata in `..\..\SECURITY_EXCEPTIONS.md`.
- Se non tocchi manifest o lockfile dipendenze, questo check non è obbligatorio.

## Chiusura task
- Se hai toccato manifest o lockfile dipendenze, nel riepilogo finale devi riportare esplicitamente quale comando di dependency-policy hai eseguito e se è passato o fallito.
- Non dichiarare il task concluso omettendo un risultato dependency-policy fallito.

