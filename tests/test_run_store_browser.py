"""A2 durable store acceptance in real Chromium; no gateway/inference traffic."""
import functools
import http.server
import threading
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class Handler(http.server.SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path == '/probe':
   self.send_response(200); self.end_headers(); self.wfile.write(b'<!doctype html><title>Store probe</title>')
  else: super().do_GET()
 def log_message(self, *args): pass

class RunStoreBrowser(unittest.TestCase):
 def setUp(self):
  self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(ROOT)))
  threading.Thread(target=self.server.serve_forever, daemon=True).start()
  self.pw = sync_playwright().start()
  self.browser = self.pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
  self.ctx = self.browser.new_context()
  self.url = 'http://127.0.0.1:' + str(self.server.server_port)
  self.ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(self.url) else r.abort())
  self.page = self.ctx.new_page(); self.page.goto(self.url + '/probe')
 def tearDown(self):
  self.browser.close(); self.pw.stop(); self.server.shutdown(); self.server.server_close()
 def runjs(self, body):
  return self.page.evaluate("async()=>{const {openRunStore}=await import('/js/run-store.js');" + body + "}")
 def test_legacy_enrichment_is_hash_bound_atomic_and_one_time(self):
  result=self.runjs("""
   const a=await openRunStore({key:'offline-account-one'}),b=await openRunStore({key:'offline-account-two'});
   const body={model:'fixture-model',prompt:'Edited boat',resolution:'720p'};
   const bodyHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(body))))].map(b=>b.toString(16).padStart(2,'0')).join('');
   const source={token:'enrichment-token',planId:'version',bodyHash,keyHash:a.account_id,status:'creating',id:null,quote:{model:'fixture-model',price:1}};
   localStorage.setItem('motion-video.v1',JSON.stringify([source]));await a.migrateLegacy();
   const row=(await a.list())[0],data={inputs:{topic:'Boat'},outputs:{request:body,plan:{prompt:'Edited boat'}},prompt:body.prompt,model_ids:[body.model],receipts:[{model:'planner',estCost:0.01}],idempotency_key:source.token,plan_id:source.planId,body_hash:bodyHash,quote:source.quote};
   const errors=[];
   for(const change of [{body_hash:'wrong'},{plan_id:'wrong'},{idempotency_key:'wrong'},{quote:{price:99}},{prompt:'Wrong prompt'},{inputs:{apiKey:'unsafe'}}]){
    try{await a.enrichLegacy(row.id,{...data,...change});errors.push(false);}catch{errors.push(true);}
   }
   try{await b.enrichLegacy(row.id,data);errors.push(false);}catch{errors.push(true);}
   const put=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(){this.transaction.abort();throw new DOMException('fixture abort','QuotaExceededError');};
   try{await a.enrichLegacy(row.id,data);errors.push(false);}catch{errors.push(true);}finally{IDBObjectStore.prototype.put=put;}
   const before=await a.get(row.id);await a.enrichLegacy(row.id,data);await a.enrichLegacy(row.id,data);
   for(const change of [{inputs:{topic:'Different'}},{model_ids:['different-model']}]){
    try{await a.enrichLegacy(row.id,{...data,...change});errors.push(false);}catch{errors.push(true);}
   }
   try{await a.update(row.id,{prompt:'Changed'});errors.push(false);}catch{errors.push(true);}
   await a.migrateLegacy();return {errors,before,row:await a.get(row.id),count:(await a.list()).length};
  """)
  self.assertEqual(result['errors'],[True]*11)
  self.assertEqual(result['before']['prompt'],'');self.assertTrue(result['before']['recovery_metadata_missing'])
  self.assertEqual(result['count'],1);self.assertFalse(result['row']['recovery_metadata_missing'])
  self.assertEqual(result['row']['prompt'],'Edited boat');self.assertEqual(result['row']['inputs'],{'topic':'Boat'})
  self.assertEqual(result['row']['receipts'],[{'model':'planner','estCost':0.01}])

 def test_pre_fix_migration_placeholder_can_recover_metadata(self):
  result=self.runjs("""
   const a=await openRunStore({key:'offline-account-one'});
   const body={model:'fixture',prompt:'Saved boat',resolution:'720p'};
   const bodyHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(body))))].map(b=>b.toString(16).padStart(2,'0')).join('');
   const source={token:'old-placeholder',planId:'old-version',bodyHash,keyHash:a.account_id,status:'creating',id:null,quote:{model:'fixture',price:1}};
   localStorage.setItem('motion-video.v1',JSON.stringify([source]));await a.migrateLegacy();
   const row=(await a.list())[0];delete row.recovery_metadata_missing;
   const db=await new Promise(resolve=>{const r=indexedDB.open('singular-runs.v1');r.onsuccess=()=>resolve(r.result);});
   await new Promise((resolve,reject)=>{const t=db.transaction('runs','readwrite');t.objectStore('runs').put(row);t.oncomplete=resolve;t.onabort=reject;});db.close();
   await a.migrateLegacy();await a.enrichLegacy(row.id,{inputs:{topic:'Recovered'},outputs:{request:body},prompt:body.prompt,model_ids:[body.model],receipts:[],idempotency_key:source.token,plan_id:source.planId,body_hash:bodyHash,quote:source.quote});
   return await a.get(row.id);
  """)
  self.assertEqual(result['prompt'],'Saved boat');self.assertFalse(result['recovery_metadata_missing'])

 def test_create_update_reload_account_isolation(self):
  result = self.runjs("""
   const a=await openRunStore({key:'offline-account-one'});
   const run=await a.create({flow_id:'motion-video',title:'Boat',inputs:{topic:'Boat'},prompt:'A boat',model_ids:['fixture-model'],idempotency_key:'logical-token'});
   await a.update(run.id,{outputs:{text:'Saved output'},receipts:[{model:'fixture-model',estCost:0.1}],cost:0.1,status:'done'});
   const other=await openRunStore({key:'offline-account-two'});
   const hidden=await other.get(run.id), list=await other.list();
   a.close();other.close(); return {id:run.id,hidden,list};
  """)
  self.assertIsNone(result['hidden']); self.assertEqual(result['list'], [])
  self.page.reload()
  saved = self.runjs("const a=await openRunStore({key:'offline-account-one'});const rows=await a.list();a.close();return rows;")
  self.assertEqual(len(saved), 1); row = saved[0]
  self.assertEqual(row['id'], result['id']); self.assertEqual(row['outputs'], {'text':'Saved output'})
  self.assertEqual(row['cost'], 0.1); self.assertEqual(row['status'], 'done')
  self.assertEqual(len(row['account_id']), 64); self.assertNotIn('offline-account-one', str(row))
  self.assertTrue(all(k in row for k in ['created_at','video_job_id','idempotency_key','receipts','model_ids','inputs','prompt']))

 def test_legacy_migration_preserves_versions_pending_receipts_and_unscoped(self):
  result = self.runjs("""
   const a=await openRunStore({key:'offline-account-one'});
   const legacy=[
    {token:'request-first',keyHash:a.account_id,planId:'version-first',bodyHash:'body-first',id:'vid_first',status:'completed',quote:{model:'fixture-model',price:1.5},settled:1.25},
    {token:'request-next',keyHash:a.account_id,planId:'version-next',bodyHash:'body-next',id:null,status:'uncertain',quote:{model:'fixture-model',price:1.5},settled:null},
    {token:'request-older',id:'vid_older',status:'queued',quote:{price:2},settled:null}
   ];
   const raw=JSON.stringify(legacy);localStorage.setItem('motion-video.v1',raw);
   const first=await a.migrateLegacy(),second=await a.migrateLegacy();
   const rows=await a.list(),pending=await a.pending();
   const b=await openRunStore({key:'offline-account-two'});await b.migrateLegacy();
   return {first,second,rows,pending,other:await b.list(),retained:localStorage.getItem('motion-video.v1')===raw,legacy};
  """)
  self.assertEqual(result['first'], {'imported':2,'unscoped':1})
  self.assertEqual(result['second'], {'imported':0,'unscoped':1})
  self.assertTrue(result['retained']); self.assertEqual(result['other'], [])
  self.assertEqual(len(result['pending']), 1)
  self.assertEqual(result['pending'][0]['video_status'], 'uncertain')
  self.assertIsNone(result['pending'][0]['video_job_id'])
  by_token = {r['idempotency_key']:r for r in result['rows']}
  for old in result['legacy'][:2]:
   row = by_token[old['token']]
   self.assertEqual(row['legacy'], old)
   self.assertEqual(row['plan_id'], old['planId']); self.assertEqual(row['body_hash'], old['bodyHash'])
   self.assertEqual(row['settled'], old['settled']); self.assertEqual(row['quote'], old['quote'])
  self.assertEqual(by_token['request-first']['cost'], 1.25)
  self.assertIsNone(by_token['request-next']['cost'])

 def test_two_tabs_merge_monotonically_and_reimport_progress(self):
  self.runjs("""
   window.a=await openRunStore({key:'offline-account-one'});
   localStorage.setItem('motion-video.v1',JSON.stringify([{token:'request',keyHash:a.account_id,planId:'version',bodyHash:'body',id:'vid_pending',status:'queued',settled:null,quote:{price:2}}]));
   await a.migrateLegacy();window.id=(await a.list())[0].id;
  """)
  other = self.ctx.new_page(); other.goto(self.url + '/probe')
  other.evaluate("async()=>{window.b=await (await import('/js/run-store.js')).openRunStore({key:'offline-account-one'});window.id=(await b.list())[0].id;}")
  # Both contexts race writes of distinct fields; read/merge/write must be atomic.
  self.page.evaluate("()=>{window.write=a.update(id,{title:'Edited title'});}")
  other.evaluate("async()=>{await b.update(id,{outputs:{text:'Output'},receipts:[{step:'video',cost:1.5}],status:'done',settled:1.5,cost:1.5,video_status:'completed'});}")
  self.page.evaluate("async()=>{await window.write;await a.update(id,{status:'rendering',video_status:'processing',settled:null,cost:null,receipts:[]});await a.migrateLegacy();}")
  row = self.page.evaluate("async()=>(await a.get(id))")
  self.assertEqual(row['status'], 'done'); self.assertEqual(row['video_status'], 'completed')
  self.assertEqual(row['settled'], 1.5); self.assertEqual(row['cost'], 1.5)
  self.assertEqual(row['receipts'], [{'step':'video','cost':1.5}]); self.assertEqual(row['title'], 'Edited title')
  bad = other.evaluate("async()=>{try{await b.update(id,{video_job_id:'vid_wrong'});return false;}catch{return true;}}")
  self.assertTrue(bad)
  # A legacy tab may settle a different request after the first migration.
  progressed = self.page.evaluate("""async()=>{
   const old=JSON.parse(localStorage.getItem('motion-video.v1'));
   old.push({token:'second',keyHash:a.account_id,planId:'v2',bodyHash:'b2',id:null,status:'uncertain',settled:null,quote:{price:2}});
   localStorage.setItem('motion-video.v1',JSON.stringify(old));await a.migrateLegacy();
   old[1].id='vid_second';old[1].status='completed';old[1].settled=1.75;
   localStorage.setItem('motion-video.v1',JSON.stringify(old));await a.migrateLegacy();
   return (await a.list()).find(r=>r.idempotency_key==='second');
  }""")
  self.assertEqual(progressed['status'], 'done'); self.assertEqual(progressed['settled'], 1.75)
  self.assertEqual(progressed['video_job_id'], 'vid_second')

 def test_create_is_idempotent_and_blocks_unresolved_same_flow_atomically(self):
  result = self.runjs("""
   const a=await openRunStore({key:'offline-account-one'}),b=await openRunStore({key:'offline-account-one'});
   const spec={flow_id:'video',prompt:'A boat',idempotency_key:'logical-token',status:'rendering'};
   const both=await Promise.all([a.create(spec),b.create(spec)]);
   const errors=[];
   for(const change of [{prompt:'Different body'},{idempotency_key:'new-version'}]){
    try{await b.create({...spec,...change});errors.push(false);}catch{errors.push(true);}
   }
   const row=both[0];await a.update(row.id,{status:'done'});
   const next=await b.create({...spec,idempotency_key:'new-version'});
   return {same:both[0].id===both[1].id,errors,count:(await a.list()).length,next:next.id!==row.id};
  """)
  self.assertTrue(result['same']); self.assertEqual(result['errors'], [True,True])
  self.assertEqual(result['count'], 2); self.assertTrue(result['next'])

 def test_update_token_assignment_is_account_unique_and_transactional(self):
  result = self.runjs("""
   const a=await openRunStore({key:'offline-account-one'});
   const owner=await a.create({flow_id:'video',idempotency_key:'shared-token'});
   const candidate=await a.create({flow_id:'video'});
   let refused=false;
   try{await a.update(candidate.id,{idempotency_key:'shared-token',title:'Must roll back'});}catch{refused=true;}
   const b=await openRunStore({key:'offline-account-two'});
   const foreign=await b.create({flow_id:'video'});
   await b.update(foreign.id,{idempotency_key:'shared-token'});
   window.a=a;
   window.candidates=[await a.create({flow_id:'race-one'}),await a.create({flow_id:'race-two'})];
   return {refused,candidate:await a.get(candidate.id),foreign:await b.get(foreign.id)};
  """)
  self.assertTrue(result['refused'])
  self.assertIsNone(result['candidate']['idempotency_key'])
  self.assertEqual(result['candidate']['title'], 'Untitled run')
  self.assertEqual(result['foreign']['idempotency_key'], 'shared-token')
  other = self.ctx.new_page(); other.goto(self.url + '/probe')
  other.evaluate("async()=>{window.b=await (await import('/js/run-store.js')).openRunStore({key:'offline-account-one'});}")
  ids = self.page.evaluate("()=>candidates.map(r=>r.id)")
  self.page.evaluate("id=>{window.assign=a.update(id,{idempotency_key:'race-token'}).then(()=>true,()=>false);}", ids[0])
  second = other.evaluate("async id=>{try{await b.update(id,{idempotency_key:'race-token'});return true;}catch{return false;}}", ids[1])
  first = self.page.evaluate("async()=>await assign")
  self.assertEqual(sorted([first,second]), [False,True])
  rows = self.page.evaluate("async()=>await a.list()")
  self.assertEqual(len([r for r in rows if r['idempotency_key']=='race-token']), 1)

 def test_missing_key_credentials_failure_and_atomic_rollback(self):
  result = self.runjs("""
   const errors=[];let network=0;
   for(const key of [undefined,'','   ']){try{await openRunStore({key});errors.push(false);}catch{errors.push(true);}}
   try{await openRunStore({key:'offline-account-one',indexedDB:null});network++;}catch{errors.push(true);}
   const a=await openRunStore({key:'offline-account-one'});
   for(const payload of [{inputs:{apiKey:'credential'}},{outputs:{text:'offline-account-one'}},{outputs:{nested:{Authorization:'Bearer secret'}}}]){
    try{await a.create({flow_id:'test',...payload});errors.push(false);}catch{errors.push(true);}
   }
   // Real transaction, injected quota/abort failure, not an in-memory IDB shim.
   const add=IDBObjectStore.prototype.add;
   IDBObjectStore.prototype.add=function(...args){this.transaction.abort();throw new DOMException('offline quota fixture','QuotaExceededError');};
   try{await a.create({flow_id:'test'});network++;}catch{errors.push(true);}finally{IDBObjectStore.prototype.add=add;}
   const empty=(await a.list()).length===0;
   const source=[{token:'request',keyHash:a.account_id,id:'vid_new',status:'queued'}, {token:'request',keyHash:a.account_id,id:'vid_conflict',status:'queued'}];
   localStorage.setItem('motion-video.v1',JSON.stringify(source));
   try{await a.migrateLegacy();errors.push(false);}catch{errors.push(true);}
   const rollback=(await a.list()).length===0;
   localStorage.setItem('motion-video.v1','malformed');
   try{await a.migrateLegacy();errors.push(false);}catch{errors.push(true);}
   return {errors,network,empty,rollback,retained:localStorage.getItem('motion-video.v1')==='malformed'};
  """)
  self.assertTrue(all(result['errors'])); self.assertEqual(len(result['errors']), 10)
  self.assertEqual(result['network'], 0); self.assertTrue(result['empty']); self.assertTrue(result['rollback']); self.assertTrue(result['retained'])

 def test_database_scan_has_no_credentials_and_other_account_cannot_write(self):
  result = self.runjs("""
   const a=await openRunStore({key:'offline-account-one'}),b=await openRunStore({key:'offline-account-two'});
   const row=await a.create({flow_id:'email',outputs:{text:'Private output'}});
   let denied=false;try{await b.update(row.id,{outputs:{text:'Intrusion'}});}catch{denied=true;}
   const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('singular-runs.v1');r.onsuccess=()=>resolve(r.result);r.onerror=reject;});
   const dump={};for(const name of db.objectStoreNames){dump[name]=await new Promise((resolve,reject)=>{const tx=db.transaction(name),r=tx.objectStore(name).getAll();r.onsuccess=()=>resolve(r.result);r.onerror=reject;});}db.close();
   return {denied,dump,hidden:await b.get(row.id)};
  """)
  self.assertTrue(result['denied']); self.assertIsNone(result['hidden'])
  dump = str(result['dump'])
  for forbidden in ['offline-account-one','offline-account-two','apiKey','Authorization','Bearer ']: self.assertNotIn(forbidden, dump)

 def test_migration_merges_existing_durable_identity_without_duplicate(self):
  result = self.runjs("""
   const a=await openRunStore({key:'offline-account-one'});
   const row=await a.create({flow_id:'claw__motion-trimmer-video',prompt:'Boat',inputs:{topic:'Boat'},idempotency_key:'shared-token',plan_id:'shared-plan',body_hash:'shared-body',receipts:[{step:'plan',cost:0.01}]});
   localStorage.setItem('motion-video.v1',JSON.stringify([{token:'shared-token',keyHash:a.account_id,planId:'shared-plan',bodyHash:'shared-body',id:'vid_shared',status:'completed',settled:1.5}]));
   await a.migrateLegacy();
   let refused=false;try{await a.update(row.id,{prompt:'Changed logical request'});}catch{refused=true;}
   return {rows:await a.list(),id:row.id,refused};
  """)
  self.assertEqual(len(result['rows']), 1); self.assertTrue(result['refused'])
  row = result['rows'][0]
  self.assertEqual(row['id'], result['id']); self.assertEqual(row['prompt'], 'Boat')
  self.assertEqual(row['receipts'], [{'step':'plan','cost':0.01}]); self.assertEqual(row['video_job_id'], 'vid_shared')

 def test_invalid_records_fail_without_corrupting_recovery(self):
  result = self.runjs("""
   const a=await openRunStore({key:'offline-account-one'});const refused=[];
   const cyclic={};cyclic.self=cyclic;
   for(const change of [{receipts:{}},{cost:NaN},{video_job_id:'../../bad'},{idempotency_key:42},{inputs:new Map([['apiKey','hidden']])},{inputs:cyclic}]){
    try{await a.create({flow_id:'test',...change});refused.push(false);}catch{refused.push(true);}
   }
   return {refused,count:(await a.list()).length};
  """)
  self.assertEqual(result['refused'], [True]*6); self.assertEqual(result['count'], 0)

 def test_migration_validates_normalized_fields_before_atomic_import(self):
  result = self.runjs("""
   const a=await openRunStore({key:'offline-account-one'}),cases=[];
   const existing=await a.create({flow_id:'claw__motion-trimmer-video',idempotency_key:'existing-token',status:'rendering'});
   const before=await a.list();
   for(const invalid of [
    {planId:42,bodyHash:[],settled:-3},
    {planId:42},{planId:''},{bodyHash:[]},{bodyHash:''},
    {settled:-3},{settled:'1.5'},{settled:{}},{id:42}
   ]){
    const source=[
     {token:'existing-token',keyHash:a.account_id,id:'vid_existing',status:'completed',settled:1},
     {token:'valid-token',keyHash:a.account_id,id:'vid_valid',status:'completed',settled:0},
     {token:'legacy-bad',keyHash:a.account_id,id:'vid_bad',status:'completed',...invalid}
    ];
    const raw=JSON.stringify(source);localStorage.setItem('motion-video.v1',raw);
    let refused=false;try{await a.migrateLegacy();}catch{refused=true;}
    cases.push({invalid,refused,unchanged:JSON.stringify(await a.list())===JSON.stringify(before),retained:localStorage.getItem('motion-video.v1')===raw});
   }
   const valid=[
    {token:'historical',keyHash:a.account_id,id:'vid_history',status:'completed',planId:'v1',bodyHash:'b1',quote:{price:2},settled:0,extra:{historical:true}},
    {token:'unknown',keyHash:a.account_id,id:null,status:'uncertain'},
    {token:'null-settlement',keyHash:a.account_id,id:null,status:'queued',planId:null,bodyHash:null,settled:null}
   ];
   localStorage.setItem('motion-video.v1',JSON.stringify(valid));
   const migration=await a.migrateLegacy();
   return {cases,migration,rows:(await a.list()).filter(r=>r.id!==existing.id),valid};
  """)
  for case in result['cases']:
   with self.subTest(invalid=case['invalid']):
    self.assertTrue(case['refused'])
    self.assertTrue(case['unchanged']); self.assertTrue(case['retained'])
  self.assertEqual(result['migration'], {'imported':3,'unscoped':0})
  by_token = {r['idempotency_key']:r for r in result['rows']}
  for source in result['valid']:
   self.assertEqual(by_token[source['token']]['legacy'], source)
  self.assertEqual(by_token['historical']['cost'], 0)
  self.assertIsNone(by_token['unknown']['cost']); self.assertIsNone(by_token['unknown']['settled'])
  self.assertIsNone(by_token['null-settlement']['cost'])

 def test_concurrent_migration_tabs_and_reload_pending_discovery(self):
  self.runjs("""
   window.a=await openRunStore({key:'offline-account-one'});
   localStorage.setItem('motion-video.v1',JSON.stringify([{token:'shared',keyHash:a.account_id,planId:'version',bodyHash:'body',id:'vid_pending',status:'processing',settled:null}]));
  """)
  other = self.ctx.new_page(); other.goto(self.url + '/probe')
  other.evaluate("async()=>{window.b=await (await import('/js/run-store.js')).openRunStore({key:'offline-account-one'});}")
  self.page.evaluate("()=>{window.migrating=a.migrateLegacy();}")
  other.evaluate("async()=>{await b.migrateLegacy();}")
  self.page.evaluate("async()=>{await window.migrating;}")
  self.page.reload()
  rows = self.runjs("const a=await openRunStore({key:'offline-account-one'});await a.migrateLegacy();return a.pending();")
  self.assertEqual(len(rows), 1); self.assertEqual(rows[0]['video_job_id'], 'vid_pending')
  self.assertEqual(rows[0]['video_status'], 'processing')

if __name__ == '__main__': unittest.main()
