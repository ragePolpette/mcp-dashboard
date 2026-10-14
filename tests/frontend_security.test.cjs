const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const frontendDir = path.join(__dirname, '../frontend');
const source = fs.readFileSync(path.join(frontendDir, 'app.js'), 'utf8');
const sqlSource = fs.readFileSync(path.join(frontendDir, 'sql-connections.js'), 'utf8');
const html = fs.readFileSync(path.join(frontendDir, 'index.html'), 'utf8');
const PAYLOAD = '<img src=x onerror="globalThis.pwned=1">';

function extract(name) {
  const match = new RegExp(`\\n(async )?function ${name}\\(`).exec(source);
  assert.ok(match, `function ${name} not found`);
  const start = match.index + 1;
  const next = /\n(async )?function [A-Za-z0-9_]+\(|\n(const|let|var) /g;
  next.lastIndex = start + 1;
  const end = next.exec(source);
  return source.slice(start, end ? end.index : source.length);
}

function load(ctx, names) {
  vm.createContext(ctx);
  for (const name of names) vm.runInContext(extract(name), ctx);
  return ctx;
}

function fakeElement() {
  const el = {
    innerHTML: '', textContent: '', className: '', children: [], dataset: {}, listeners: {},
    classList: {add() {}, remove() {}, toggle() {}, contains() { return false; }},
    appendChild(child) { this.children.push(child); return child; },
    removeChild(child) { this.children = this.children.filter(item => item !== child); },
    get firstChild() { return this.children[0] || null; },
    addEventListener(type, fn) { this.listeners[type] = fn; },
    querySelector() { return fakeElement(); },
    focus() {}
  };
  return el;
}

function fakeDocument() {
  return {
    createElement: () => fakeElement(),
    createDocumentFragment: () => fakeElement(),
    getElementById: () => null
  };
}

function vaultHandlers() {
  const noop = () => {};
  return {saveVaultEntry: noop, lockVault: noop, unlockVault: noop, initializeVault: noop,
    deleteVaultEntry: noop, copyToClipboard: noop, setSettingsFlash: noop};
}

function renderedMarkup(el) {
  return [el.innerHTML, ...el.children.map(renderedMarkup)].join('\n');
}

function assertInert(markup) {
  assert.equal(markup.includes('<img'), false, markup);
  assert.ok(markup.includes('&lt;img'), 'payload should be rendered as text');
}

test('settings flash messages and refs are escaped', () => {
  const ctx = load({settingsFlash: fakeElement(), settingsFlashState: null, copyToClipboard: () => {}},
    ['escapeHtml', 'renderSettingsFlash', 'setSettingsFlash']);
  ctx.setSettingsFlash(`Errore: ${PAYLOAD}`, 'error', `vault://x${PAYLOAD}`);
  assertInert(ctx.settingsFlash.innerHTML);
  assert.equal(ctx.settingsFlash.innerHTML.includes('"globalThis'), false);
});

test('alert names and messages are escaped', () => {
  const alertList = fakeElement();
  const ctx = load({
    document: fakeDocument(), alertList, alertSummary: fakeElement(),
    getServiceAlerts: () => ({triggered_count: 1, status: 'alert', triggered: [
      {name: PAYLOAD, message: PAYLOAD, severity: 'alert', current_value: PAYLOAD, op: '>', threshold: 1}
    ]})
  }, ['escapeHtml', 'alertClass', 'alertLabel', 'clearAlertList', 'renderAlertsForAdvanced']);
  ctx.renderAlertsForAdvanced('svc');
  assertInert(renderedMarkup(alertList));
});

test('vault entries escape refs and describe DB target usage without undefined', () => {
  const ref = `vault://db${PAYLOAD}`;
  const vaultEntries = fakeElement();
  const ctx = load({
    document: fakeDocument(), vaultStatusCard: fakeElement(), vaultControls: fakeElement(), vaultEntries,
    vaultEditingRef: '', formatTimestamp: () => '2026-10-14', ...vaultHandlers(),
    vaultState: {initialized: true, unlocked: true, entry_count: 1, auto_lock_seconds: 1800,
      entries: [{ref, name: 'x', updated_at: '2026-10-14'}],
      ref_usage: {[ref]: [{target_id: 'prod-main', field_id: 'connection'}, {service_id: 'llm-memory', option_id: 'api_key'}]}}
  }, ['escapeHtml', 'formatVaultRefUsage', 'renderVaultPanel']);
  ctx.renderVaultPanel();
  const markup = renderedMarkup(vaultEntries);
  assertInert(markup);
  assert.ok(markup.includes('DB target prod-main'));
  assert.ok(markup.includes('llm-memory.api_key'));
  assert.equal(markup.includes('undefined'), false);
});

test('locked vault lists only reference names without edit or delete actions', () => {
  const vaultEntries = fakeElement();
  const ctx = load({
    document: fakeDocument(), vaultStatusCard: fakeElement(), vaultControls: fakeElement(), vaultEntries,
    vaultEditingRef: '', formatTimestamp: () => 'n/d', ...vaultHandlers(),
    vaultState: {initialized: true, unlocked: false, entry_count: 1, entries: [{ref: 'vault://db.dev.main', name: 'db.dev.main'}], ref_usage: {}}
  }, ['escapeHtml', 'formatVaultRefUsage', 'renderVaultPanel']);
  ctx.renderVaultPanel();
  const markup = renderedMarkup(vaultEntries);
  assert.ok(markup.includes('vault://db.dev.main'));
  assert.equal(markup.includes('data-vault-delete'), false);
  assert.equal(markup.includes('Aggiornato'), false);
});

test('formatVaultRefUsage supports both service options and DB targets', () => {
  const ctx = load({}, ['formatVaultRefUsage']);
  assert.equal(ctx.formatVaultRefUsage({service_id: 'svc', option_id: 'opt'}), 'svc.opt');
  assert.equal(ctx.formatVaultRefUsage({target_id: 'prod-main', field_id: 'connection'}), 'DB target prod-main');
  assert.equal(ctx.formatVaultRefUsage({target_id: 'prod-main', field_id: 'password'}), 'DB target prod-main.password');
  assert.equal(ctx.formatVaultRefUsage({}), 'n/d');
});

function apiContext(responses) {
  const calls = [];
  const ctx = {
    Headers, calls,
    DASHBOARD_REQUESTED_WITH: 'mcp-dashboard',
    UNSAFE_HTTP_METHODS: new Set(['POST', 'PUT', 'PATCH', 'DELETE']),
    dashboardSessionToken: '', dashboardSessionTokenRequest: null,
    fetch: async (url, options = {}) => {
      calls.push({url, headers: new Headers(options.headers || {}), method: options.method || 'GET'});
      const next = responses.shift();
      return {ok: next.status < 400, status: next.status, json: async () => next.body};
    }
  };
  return load(ctx, ['fetchDashboardSessionToken', 'dashboardRequestOptions', 'apiJson']);
}

test('apiJson marks every request and sends the session token on unsafe methods', async () => {
  const ctx = apiContext([
    {status: 200, body: {services: []}},
    {status: 200, body: {token: 'tok-1'}},
    {status: 200, body: {ok: true}}
  ]);
  await ctx.apiJson('/api/services');
  await ctx.apiJson('/api/control/kill-all', {method: 'POST'});

  assert.equal(ctx.calls[0].headers.get('X-Requested-With'), 'mcp-dashboard');
  assert.equal(ctx.calls[0].headers.get('X-Dashboard-Token'), null);
  assert.equal(ctx.calls[1].url, '/api/session');
  assert.equal(ctx.calls[1].headers.get('X-Requested-With'), 'mcp-dashboard');
  assert.equal(ctx.calls[2].headers.get('X-Dashboard-Token'), 'tok-1');
  assert.equal(ctx.calls[2].headers.get('X-Requested-With'), 'mcp-dashboard');
});

test('apiJson refreshes a stale session token once', async () => {
  const ctx = apiContext([
    {status: 200, body: {token: 'old'}},
    {status: 403, body: {code: 'csrf_token_invalid', detail: 'bad token'}},
    {status: 200, body: {token: 'new'}},
    {status: 200, body: {ok: true}}
  ]);
  const payload = await ctx.apiJson('/api/vault/lock', {method: 'POST', headers: {'Content-Type': 'application/json'}});

  assert.equal(payload.ok, true);
  assert.equal(ctx.calls[3].headers.get('X-Dashboard-Token'), 'new');
  assert.equal(ctx.calls[3].headers.get('Content-Type'), 'application/json');
});

test('every network call goes through the shared request helpers', () => {
  const allowed = new Set(['fetchDashboardSessionToken', 'apiJson']);
  const fetchCalls = [...source.matchAll(/\bfetch\(/g)];
  assert.ok(fetchCalls.length > 0);
  for (const call of fetchCalls) {
    const before = source.slice(0, call.index);
    const owner = [...before.matchAll(/\n(?:async )?function ([A-Za-z0-9_]+)\(/g)].pop()[1];
    assert.ok(allowed.has(owner), `fetch() used directly in ${owner}`);
  }
  assert.equal(/\bfetch\(/.test(sqlSource), false);
  assert.equal(/XMLHttpRequest/.test(source + sqlSource), false);
});

test('all frontend scripts are cache-busted', () => {
  const scripts = [...html.matchAll(/<script src="([^"]+)"/g)].map(match => match[1]);
  assert.ok(scripts.length >= 2);
  for (const src of scripts) assert.match(src, /\?v=/);
});
