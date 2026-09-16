const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../frontend/app.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '../frontend/index.html'), 'utf8');
function element() {
  const classes = new Set();
  return {value:'temporary-password', attributes:{}, classList:{
    add:x=>classes.add(x), remove:x=>classes.delete(x), contains:x=>classes.has(x),
    toggle(x, value) { if (value) classes.add(x); else classes.delete(x); }
  }, setAttribute(k,v) {this.attributes[k]=v;}};
}
function context(service) {
  const ctx = {advancedServiceId:service, supportsInspector:()=>false, supportsMemoryAdmin:()=>false};
  for (const name of ['tabOptionsBtn','advancedOptionsView','tabLogsBtn','advancedLogsView','tabInspectorBtn','advancedInspectorView','tabMemoryBtn','advancedMemoryView','tabDbTargetsBtn','advancedDbTargetsView','settingsServicesTabBtn','settingsDashboardTabBtn','settingsVaultTabBtn','settingsServicesView','settingsDashboardView','settingsVaultView']) ctx[name]=element();
  ctx.password=element();ctx.document={getElementById:()=>ctx.password};
  vm.createContext(ctx);
  vm.runInContext(source.slice(source.indexOf('function setAdvancedTab('), source.indexOf('function toDisplayText(')),ctx);
  vm.runInContext(source.slice(source.indexOf('function setSettingsTab('), source.indexOf('async function copyToClipboard(')),ctx);
  return ctx;
}
test('SQL target tab opens only for the SQL service and clears passwords on departure',()=>{
  const c=context('llm-sql-db-mcp');c.setAdvancedTab('db-targets');
  assert.equal(c.advancedDbTargetsView.classList.contains('hidden'),false);
  assert.equal(c.tabDbTargetsBtn.attributes['aria-selected'],'true');
  c.setAdvancedTab('logs');assert.equal(c.password.value,'');
  c.advancedServiceId='llm-bitbucket-mcp';c.setAdvancedTab('db-targets');
  assert.equal(c.advancedDbTargetsView.classList.contains('hidden'),true);
  assert.equal(c.tabDbTargetsBtn.classList.contains('hidden'),true);
  assert.equal(c.advancedOptionsView.classList.contains('hidden'),false);
});
test('opening the global vault does not hide the SQL target view',()=>{
  const c=context('llm-sql-db-mcp');c.setAdvancedTab('db-targets');c.setSettingsTab('vault');
  assert.equal(c.settingsVaultView.classList.contains('hidden'),false);
  assert.equal(c.advancedDbTargetsView.classList.contains('hidden'),false);
});
test('target markup belongs to advanced section, with one form and local feedback',()=>{
  assert.equal(html.includes('settingsDbTargetsTabBtn'),false);
  assert.equal(html.includes('settingsDbTargetsView'),false);
  assert.ok(html.indexOf('id="advancedDbTargetsView"') < html.indexOf('id="settingsPanel"'));
  for(const id of ['dbTargetEditorForm','dbConnectionPanel','dbTargetsFlash']) assert.equal(html.split(`id="${id}"`).length,2);
});