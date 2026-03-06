# Log Pipeline Spec (Extensible)

## Obiettivo
Visualizzare log MCP in modo estensibile senza cambiare codice UI/backend ad ogni nuova voce.

## Pipeline
1. **Sources**
   - definite per servizio in `services.json`
   - ogni source ha `path`, `channel`, `tags`
2. **Parser chain**
   - sequenza parser per servizio (`json`, `python`, `uvicorn_access`, `node_deprecation`, ...)
   - primo parser che matcha produce struttura base
3. **Rule engine**
   - applica regole `default` + set specifici servizio
   - regole possono settare `event`, `level`, campi custom e tag
4. **UI renderer**
   - mostra colonne standard (`level`, `event`, `message`)
   - tutto il resto finisce in `meta` JSON auto-render

## Entry normalizzata
Campi sempre presenti:
- `service_id`
- `channel`
- `source_path`
- `message`
- `level`
- `event`
- `raw`
- `tags[]`
- `fields{}`

Campi opzionali parser-derived:
- `timestamp`
- `logger`

## Estensione parser
Per nuovi formati log:
1. aggiungere parser in `backend/app/log_parsers.py`
2. registrarlo in `_PARSER_MAP`
3. inserirlo nella `parser_chain` del servizio

## Estensione regole (senza codice)
Per nuove voci log applicative:
1. aggiungere regola in `backend/config/log_rules.json`
2. usare:
   - `contains` per match semplice
   - `regex` per pattern
   - `set` per arricchire campi
   - `add_tags` per filtraggio UI

Esempio:
```json
{
  "regex": "WRITER_MODEL_UNTRUSTED",
  "set": {
    "event": "memory.compliance_reject",
    "level": "WARN"
  },
  "add_tags": ["memory", "compliance"]
}
```

## Compatibilità futura
- nuovi campi log sono visualizzati automaticamente in `meta`.
- non serve aggiornare frontend per ogni nuova chiave.
- consigliato mantenere naming coerente:
  - `event` in formato `domain.action`
  - `level` in `DEBUG|INFO|WARN|ERROR|CRITICAL`
