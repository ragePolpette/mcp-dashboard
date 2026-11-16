const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../frontend/app.js'), 'utf8');

function slice(from, to) {
  const start = source.indexOf(from);
  const end = source.indexOf(to, start);
  assert.ok(start >= 0 && end > start, `cannot slice ${from}`);
  return source.slice(start, end);
}

function load() {
  const context = { TextEncoder };
  vm.createContext(context);
  // Helper dei target (cloneValue .. normalizeDbTargetDraft) e riepilogo policy.
  vm.runInContext(slice('function cloneValue(', 'function summarizeDbTargetBinding('), context);
  vm.runInContext(slice('function summarizeDbTargetPolicy(', 'function summarizeDbTargetLimits('), context);
  return context;
}

test('the default draft has DDL off and db_ddl is a selectable tool', () => {
  const c = load();
  assert.equal(c.defaultDbTargetDraft().ddl_enabled, false);
  // `const` non diventa proprieta' del contesto vm: la leggiamo valutandola.
  assert.ok(vm.runInContext('DB_TARGET_TOOL_OPTIONS', c).includes('db_ddl'));
});

test('a record reads ddl_enabled from the flat field or from the policy section', () => {
  const c = load();
  assert.equal(c.normalizeDbTargetRecord({ target_id: 'a', ddl_enabled: true }).ddl_enabled, true);
  assert.equal(c.normalizeDbTargetRecord({ target_id: 'a', policy: { ddl_enabled: true } }).ddl_enabled, true);
  assert.equal(c.normalizeDbTargetRecord({ target_id: 'a' }).ddl_enabled, false);
});

test('a dev target without anonymization keeps ddl_enabled in the draft', () => {
  const c = load();
  const draft = c.normalizeDbTargetDraft({ target_id: 'dev-main', environment: 'dev', ddl_enabled: true, anonymization_enabled: false });
  assert.equal(draft.ddl_enabled, true);
});

test('the draft forces ddl_enabled off on prod and on anonymized targets', () => {
  const c = load();
  const prod = c.normalizeDbTargetDraft({ target_id: 'p', environment: 'prod', ddl_enabled: true, anonymization_enabled: false });
  const anonymized = c.normalizeDbTargetDraft({
    target_id: 'a', environment: 'dev', ddl_enabled: true, anonymization_enabled: true, anonymization_mode: 'deterministic'
  });
  assert.equal(prod.ddl_enabled, false);
  assert.equal(anonymized.ddl_enabled, false);
});

test('the policy summary shows the DDL state', () => {
  const c = load();
  assert.match(c.summarizeDbTargetPolicy({ read_enabled: true, write_policy: 'deny', ddl_enabled: true }), /ddl ON/);
  assert.match(c.summarizeDbTargetPolicy({ read_enabled: true, write_policy: 'deny', ddl_enabled: false }), /ddl OFF/);
});

test('the editor exposes the DDL checkbox, disabled on prod and anonymized targets, and adds db_ddl on toggle', () => {
  assert.match(source, /data-db-target-field="ddl_enabled" type="checkbox"/);
  assert.match(source, /Consenti variazioni schema \(DDL\)/);
  assert.match(source, /\$\{prod \|\| draft\.anonymization_enabled \? "disabled" : ""\}>Consenti variazioni schema/);
  assert.match(source, /field === "ddl_enabled" && draft\.ddl_enabled/);
});
