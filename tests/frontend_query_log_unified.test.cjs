const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../frontend/app.js'), 'utf8');

function load() {
  const start = source.indexOf('function isDbQueryEvent(');
  const end = source.indexOf('function renderQueriesForAdvanced(', start);
  assert.ok(start >= 0 && end > start, 'cannot slice the log-entry helpers');
  const context = {};
  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  return context;
}

const queryOut = {
  event: 'db.query_out',
  timestamp: '2026-11-16T10:00:00Z',
  fields: { payload: { tool: 'db_read', target_id: 'dev-main', row_count: 3, truncated: true, sql_hash: 'aaaaaaaaaaaaaaaa' } }
};
const queryFailed = {
  event: 'db.query_failed',
  fields: { payload: { tool: 'db_write', target_id: 'dev-main', error: 'Invalid object name', sql_hash: 'bbbbbbbbbbbbbbbb' } }
};

test('unified server query events are recognised as DB query events', () => {
  const c = load();
  assert.equal(c.isDbQueryEvent(queryOut), true);
  assert.equal(c.isDbQueryEvent(queryFailed), true);
  assert.equal(c.isDbQueryEvent({ event: 'db.anonymizer_decisions' }), false);
  assert.equal(c.isDbQueryEvent({ event: 'query_out' }), true);
});

test('the log line message summarises db.query_out and db.query_failed from the nested payload', () => {
  const c = load();
  const out = c.entryDisplayMessage(queryOut);
  assert.match(out, /db_read/);
  assert.match(out, /3 rows/);
  assert.match(out, /risultato troncato/);
  assert.match(out, /aaaaaaaaaaaaaaaa/);
  const failed = c.entryDisplayMessage(queryFailed);
  assert.match(failed, /db_write/);
  assert.match(failed, /Invalid object name/);
});

test('the meta payload of a unified query event is flat and has no nested payload', () => {
  const c = load();
  const meta = c.entryMetaPayload(queryOut);
  assert.equal(meta.tool, 'db_read');
  assert.equal(meta.target_id, 'dev-main');
  assert.equal(meta.row_count, 3);
  assert.equal(meta.sql_hash, 'aaaaaaaaaaaaaaaa');
  assert.equal(Object.hasOwn(meta, 'payload'), false);
  const failedMeta = c.entryMetaPayload(queryFailed);
  assert.equal(failedMeta.error, 'Invalid object name');
});

test('legacy query_out events keep their summary', () => {
  const c = load();
  const legacy = { event: 'query_out', fields: { tool: 'db_dev_read', response: { rowCount: 7, truncated: false } } };
  assert.equal(c.entryDisplayMessage(legacy), 'db_dev_read | 7 rows');
});
