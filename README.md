# MCP Dashboard (Logs + Control v3)

Questo progetto e' destinato a vivere come **repository standalone** dentro il workspace DEV `Yetzirah`.
Il runtime locale, quando deployato, resta in `Binah\mcp-dashboard`.

Dashboard web locale per monitoring e controllo servizi MCP:

- vista widget con tutti i servizi nella stessa schermata
- stato runtime per servizio (running/stopped/pid/porta)
- azioni `Start`, `Stop`, `Restart` da UI
- opzioni pre-avvio per servizio
- gestione opzioni `secret` (es. connection string DB) non esposte in chiaro in API/UI e non salvate su disco
- vault locale persistente per segreti riusabili via riferimenti `vault://...`
- registry `DB Targets` per target SQL runtime-editable con export verso `llm-sql-db-mcp`
- pannello `Avanzate` con log dettagliati e stream SSE
- pipeline log estensibile (sources + parser chain + rules)

## Avvio

```powershell
pwsh -ExecutionPolicy Bypass -File C:\Users\Gianmarco\Urgewalt\Yetzirah\tools\start-dashboard.ps1
```

Script canonico di avvio: [start-dashboard.ps1](/C:/Users/Gianmarco/Urgewalt/Yetzirah/tools/start-dashboard.ps1)

La copia Desktop [Avvia_MCP_Dashboard_Binah.bat](/C:/Users/Gianmarco/Desktop/Avvia_MCP_Dashboard_Binah.bat) e' solo un wrapper di comodita': deve limitarsi ad aprire la dashboard usando lo script canonico in `Yetzirah\tools`, senza logica locale duplicata.

Di default la dashboard parte senza `--reload`, per evitare processi reloader appesi e rendere il lifecycle piu prevedibile.
Per hot reload esplicito in sviluppo:

```powershell
pwsh -ExecutionPolicy Bypass -File C:\Users\Gianmarco\Urgewalt\Yetzirah\tools\start-dashboard.ps1 -Reload
```

Su Windows, il comportamento di shutdown verificato da questo repository e' validato con PowerShell 7 (`pwsh`).
Lo script resta avviabile anche da `powershell.exe`, ma il caso di terminazione brutale del processo padre e' stato verificato solo con `pwsh`.

Endpoint:
- UI: `http://127.0.0.1:8790/`
- API health: `http://127.0.0.1:8790/health`

## API controllo servizi

- `GET /api/services`
- `GET /api/services/{service_id}/status`
- `POST /api/services/{service_id}/start`
- `POST /api/services/{service_id}/stop`
- `POST /api/services/{service_id}/restart`

## API opzioni pre-avvio

- `GET /api/services/{service_id}/options`
- `POST /api/services/{service_id}/options`

## API vault e DB targets

- `GET /api/vault`
- `POST /api/vault/init`
- `POST /api/vault/unlock`
- `POST /api/vault/lock`
- `POST /api/vault/entries`
- `DELETE /api/vault/entries`
- `GET /api/db-targets`
- `GET /api/db-targets/{target_id}`
- `POST /api/db-targets`
- `PUT /api/db-targets/{target_id}`
- `POST /api/db-targets/{target_id}/disable`
- `POST /api/db-targets/{target_id}/enable`
- `GET /api/services/llm-memory/memory-admin/summary`
- `GET /api/services/llm-memory/memory-admin/audit`
- `GET /api/services/llm-memory/memory-admin/projects`

Le opzioni non secret vengono salvate in `runtime/service_options.json` e applicate al prossimo `Start/Restart`.
Le opzioni `secret` restano solo in memoria del backend dashboard finche' la dashboard resta attiva e non vengono mai salvate su disco.
I servizi avviati dalla dashboard partono con terminale nascosto; stdout/stderr vengono rediretti ai file log configurati e sono consultabili dal pannello `Avanzate`.
Nel pannello `Avanzate` puoi filtrare i log per:
- `Level`
- `Event`
- `Channel` (`stdout` / `stderr`)
- `Source` (file log specifico, ad esempio `DEV`, `RUNTIME`, `SERVICE`)

## Punto 3 (DB dev/prod)

Configurate opzioni secret per:
- `llm-db-dev-mcp` -> `DB_DEV_CONNECTION_STRING`
- `llm-db-prod-mcp` -> `DB_PROD_CONNECTION_STRING`

Nel pannello `Avanzate`:
- inserisci la connection string
- `Salva Opzioni`
- esegui `Restart` del servizio DB

Le opzioni secret non vengono restituite in chiaro; viene mostrato solo se il valore e' impostato.
Se fai `Restart` dalla stessa dashboard web/backend, la connection string resta disponibile in memoria.
Se riavvii la dashboard, la devi reinserire.

Con il registry `DB Targets`, `llm-sql-db-mcp` non dipende piu da una lista rigida di target hardcoded nelle opzioni del servizio.
La dashboard mantiene il modello di controllo e genera un export runtime dedicato consumato dal server SQL MCP.

Per `llm-memory`, il dashboard espone anche un proxy backend read-only verso la superficie admin locale del servizio.
Questo evita letture dirette del database dal pannello e mantiene il confine pulito tra UI/control-plane e ownership del runtime `llm-memory`.

## Config servizi

File principali:
- `backend/config/services.json`
- `backend/config/services.example.json`
- `backend/config/log_rules.json`

Per abilitare controllo su un servizio aggiungere `control`:
- `workdir`
- `start_command` (array di argomenti)
- `host` / `port` (opzionali ma consigliati)
- `pid_file`, `stdout_log`, `stderr_log` (consigliati)
- `env` (opzionale)
- `options` (opzionale) con campi:
  - `id`, `label`, `type`, `env_var`, `default`
  - `secret` per valori sensibili

## Log estensibili

Per nuove voci log applicative:
1. aggiorna source/parsers in `services.json`
2. aggiungi regole in `log_rules.json`
3. riavvia dashboard

La UI renderizza automaticamente i campi extra in `meta`.

Note operative:
- il widget `LLM Context` usa un trend basato sugli eventi reali `context.retrieved`, non sul solo volume generico di log
- i servizi con `health_url` configurata mostrano uno stato runtime piu affidabile (`Running`, `Unhealthy`)
- durante azioni da UI lo stato operativo espone anche transizioni esplicite (`Starting`, `Stopping`, `Restarting`)

Dettagli:
- `docs/LOG_PIPELINE_SPEC.md`
- `docs/db-target-registry-migration.md`
