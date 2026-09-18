const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../frontend/app.js'), 'utf8');
function setup() {
  const a={target_id:'a',connection_vault_ref:'vault://a',max_rows:10};
  const b={target_id:'b',connection_vault_ref:'vault://b',max_rows:20};
  const pending=[];
  const c={dbTargetsState:{selectedId:'a',draft:{...a},items:[a,b]},
    cloneValue:x=>JSON.parse(JSON.stringify(x)),normalizeDbTargetRecord:x=>x,normalizeDbTargetDraft:x=>x,
    renderDbTargetsPanel:()=>{},setDbTargetsFlash:()=>{},window:{alert:()=>{}},
    apiJson:(url, options)=>new Promise(resolve=>pending.push({url,options,resolve}))};
  c.collectDbTargetPayload=()=>({...c.dbTargetsState.draft});
  c.setDbTargetDraft=(draft,id)=>{c.dbTargetsState.draft=draft;c.dbTargetsState.selectedId=id;};
  vm.createContext(c);
  for (const [from,to] of [['function selectDbTarget(', 'function startNewDbTarget('],
    ['async function loadDbTargets(', 'async function syncDbTargetsRuntime('],
    ['async function saveDbTargetFromEditor(', 'async function disableSelectedDbTarget(']]) {
    vm.runInContext(source.slice(source.indexOf(from),source.indexOf(to)),c);
  }
  return {c,pending,a,b};
}
test('switching targets displays a separate draft and only saves selected target',async()=>{
  const {c,pending,a}=setup();c.selectDbTarget('b');
  assert.equal(c.dbTargetsState.draft.connection_vault_ref,'vault://b');
  c.dbTargetsState.draft.max_rows=99;
  const save=c.saveDbTargetFromEditor({preventDefault(){}});
  assert.equal(pending[0].url,'/api/db-targets/b');
  assert.equal(JSON.parse(pending[0].options.body).values.max_rows,99);
  assert.equal(a.max_rows,10);
  c.selectDbTarget('a');pending[0].resolve({target:{target_id:'b',max_rows:99}});await save;
  assert.equal(c.dbTargetsState.selectedId,'a');assert.equal(c.dbTargetsState.draft.max_rows,10);
});
test('late save never overwrites edits on the newly selected target',async()=>{
  const {c,pending}=setup();const save=c.saveDbTargetFromEditor({preventDefault(){}});
  c.selectDbTarget('b');c.dbTargetsState.draft.max_rows=42;
  pending[0].resolve({target:{target_id:'a',max_rows:10}});await save;
  assert.equal(c.dbTargetsState.selectedId,'b');assert.equal(c.dbTargetsState.draft.max_rows,42);
});
test('late reload preserves selection and draft changed during request',async()=>{
  const {c,pending,a,b}=setup();const reload=c.loadDbTargets();
  c.selectDbTarget('b');c.dbTargetsState.draft.max_rows=42;
  pending[0].resolve({targets:[a,b]});await reload;
  assert.equal(c.dbTargetsState.draft.max_rows,42);
});
test('out-of-order reloads cannot replace newer results',async()=>{
  const {c,pending}=setup();const first=c.loadDbTargets();const second=c.loadDbTargets();
  pending[1].resolve({targets:[{target_id:'a',max_rows:30}]});await second;
  pending[0].resolve({targets:[{target_id:'a',max_rows:1}]});await first;
  assert.equal(c.dbTargetsState.draft.max_rows,30);
});

test('actual normalization preserves Any, empty tools and distinct connection IDs',()=>{
  const c={TextEncoder, cloneValue:x=>JSON.parse(JSON.stringify(x))};
  vm.createContext(c);
  const start=source.indexOf('function normalizeDbTargetText(');
  const end=source.indexOf('function summarizeDbTargetBinding(');
  vm.runInContext(source.slice(start,end),c);
  const ids=['client-a','client_a','CLIENT-A'];
  assert.equal(new Set(ids.map(id=>c.buildDbTargetConnectionEnvVar(id))).size,3);
  for(const value of [null,'Any','any']) {
    const draft=c.normalizeDbTargetDraft({target_id:'one',max_result_bytes:value,allowed_tools:[]});
    assert.equal(draft.max_result_bytes,null);
    assert.equal(draft.allowed_tools.length,0);
  }
  assert.equal(c.normalizeDbTargetDraft({target_id:'two',limits:{max_result_bytes:null}}).max_result_bytes,null);
  assert.equal(c.normalizeDbTargetDraft({target_id:'two'}).max_result_bytes,131072);
});
