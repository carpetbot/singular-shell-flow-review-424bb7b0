"""A2 integration: real Chromium/IndexedDB, loopback fixtures only."""
from test_video_browser import VideoBrowser
import unittest

class DurableVideoBrowser(VideoBrowser):
 # Reuse fixture setup, not the inherited legacy acceptance cases.
 def test_durable_saved_before_post_and_plan_before_chat(self):
  self.open();self.page.route('**/v1/chat/completions',self.check_chat);self.plan()
  rows=self.rows()
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]['status'],'done')
  self.assertEqual(rows[0]['inputs']['topic'],'An offline paper boat')
  self.assertTrue(rows[0]['receipts'])
  self.page.route('**/v1/videos',self.check_post)
  self.checked=False
  self.page.locator('#video-quote').click()
  self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.locator('#video-generate').click()
  self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.assertTrue(self.checked)
  render=[r for r in self.rows() if r['idempotency_key']][0]
  self.assertEqual(render['status'],'done');self.assertEqual(render['video_job_id'],'vid_offline')
  self.assertEqual(render['prompt'],'A paper boat drifts on a calm pond.')
 def test_interrupted_planner_reload_allows_new_render(self):
  self.open()
  orphan=self.page.evaluate("async()=>{return await(await import('/js/video-runtime.js')).saveVideoPlan({topic:'Interrupted plan',duration:5});}")
  self.page.reload();self.open();self.plan()
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click()
  self.page.wait_for_timeout(700)
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
  old=next(r for r in self.rows() if r['id']==orphan['id'])
  self.assertEqual(old['status'],'failed');self.assertEqual(old['outputs']['planner_state'],'abandoned')
  self.assertIn('interrupted',old['error'].lower())
 def test_interrupted_planner_account_replacement_is_abandoned(self):
  self.open()
  orphan=self.page.evaluate("async()=>{return await(await import('/js/video-runtime.js')).saveVideoPlan({topic:'Account interrupted plan',duration:5});}")
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-replacement-account'});}")
  self.page.wait_for_function("!document.querySelector('.modal')")
  self.page.wait_for_timeout(150)
  old=next(r for r in self.rows() if r['id']==orphan['id'])
  self.assertEqual(old['status'],'failed');self.assertEqual(old['outputs']['planner_state'],'abandoned')
  self.open();self.page.wait_for_function("document.querySelector('#toasts').textContent.includes('saved as abandoned')");self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
 def test_active_cross_tab_planner_is_not_abandoned(self):
  self.open()
  orphan=self.page.evaluate("async()=>await(await import('/js/video-runtime.js')).saveVideoPlan({topic:'Active plan',duration:5})")
  other=self.ctx.new_page();other.goto(self.url+'/#/settings');other.wait_for_selector('#view')
  other.wait_for_selector('#apikey')
  other.evaluate("async()=>{await(await import('/js/video-runtime.js')).videoContext();}")
  self.assertEqual(next(r for r in self.rows() if r['id']==orphan['id'])['status'],'running')
  other.close()
 def test_old_planning_rows_abandoned_but_tokenless_render_still_blocks(self):
  self.open()
  ids=self.page.evaluate("""async()=>{const {videoContext,VIDEO_FLOW}=await import('/js/video-runtime.js');const c=await videoContext();const old=await c.store.create({flow_id:VIDEO_FLOW,inputs:{topic:'Old interrupted planner'},status:'running'});const render=await c.store.create({flow_id:VIDEO_FLOW,status:'rendering',video_status:'creating'});return [old.id,render.id];}""")
  self.page.reload();self.open();self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('pending')")
  rows={r['id']:r for r in self.rows()}
  self.assertEqual(rows[ids[0]]['outputs']['planner_state'],'abandoned');self.assertEqual(rows[ids[1]]['status'],'rendering')
  self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls))
 def test_storage_abort_retry_preserves_draft_before_post(self):
  self.abort_retry(False)
 def test_storage_abort_reload_recovers_edited_draft_before_post(self):
  self.abort_retry(True)
 def abort_retry(self,reload):
  self.open();self.plan();self.page.locator('#video-prompt').fill('Edited retry boat prompt')
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.evaluate("""()=>{window.originalAdd=IDBObjectStore.prototype.add;IDBObjectStore.prototype.add=function(){this.transaction.abort();throw new DOMException('fixture abort','QuotaExceededError');};}""")
  self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('fixture abort')")
  self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls))
  token=self.page.evaluate("JSON.parse(localStorage.getItem('motion-video.v1'))[0].token")
  self.page.evaluate("()=>{IDBObjectStore.prototype.add=window.originalAdd;}")
  if reload:
   self.page.evaluate("""async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();const source=(await c.store.list()).find(r=>r.outputs?.request&&!r.idempotency_key);const decoy={...source,id:'0000-decoy',inputs:{topic:'Unrelated plan with same body'},receipts:[]};delete decoy.outputs.render_identity;const db=await new Promise(resolve=>{const r=indexedDB.open('singular-runs.v1');r.onsuccess=()=>resolve(r.result);});await new Promise((resolve,reject)=>{const t=db.transaction('runs','readwrite');t.objectStore('runs').add(decoy);t.oncomplete=resolve;t.onabort=reject;});db.close();}""")
   self.page.reload();self.open()
   self.assertEqual(self.page.locator('#video-prompt').input_value(),'Edited retry boat prompt')
   self.assertIn('shotbeats',self.page.locator('#video-plan-json').input_value())
   self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  observed=[]
  def check(r):
   observed.extend(x for x in self.rows() if x['idempotency_key']==token)
   self.route(r)
  self.page.route('**/v1/videos',check)
  self.page.locator('#video-generate').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.assertEqual(len(observed),1);row=observed[0]
  self.assertEqual(row['prompt'],'Edited retry boat prompt')
  self.assertEqual(row['inputs']['topic'],'An offline paper boat');self.assertTrue(row['receipts']);self.assertIn('plan',row['outputs'])
  self.assertEqual(row['outputs']['plan']['prompt'],'Edited retry boat prompt')
  submits=[c for c in self.calls if c['path']=='/v1/videos']
  self.assertEqual(row['outputs']['request'],submits[0]['body'])
  self.assertEqual([c['token'] for c in submits],[token])
 def test_wrong_retry_cannot_replace_reload_recovery_draft(self):
  self.open();self.plan();self.page.locator('#video-prompt').fill('Original edited prompt')
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.evaluate("""()=>{window.originalAdd=IDBObjectStore.prototype.add;IDBObjectStore.prototype.add=function(){this.transaction.abort();throw new DOMException('fixture abort','QuotaExceededError');};}""")
  self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('fixture abort')")
  self.page.evaluate("()=>{IDBObjectStore.prototype.add=window.originalAdd;}")
  self.page.locator('#video-prompt').fill('Wrong retry prompt');self.page.locator('#video-generate').click()
  self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('identical prompt')")
  self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls))
  self.page.reload();self.open();self.assertEqual(self.page.locator('#video-prompt').input_value(),'Original edited prompt')
 def start_pending(self):
  self.state='processing';self.open();self.plan()
  self.page.evaluate("async()=>{const s=await import('/js/store.js');s.setSettings({apiKey:'offline-not-real-key'});}")
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('processing')")
 def test_route_independent_ready_notice_and_open(self):
  self.start_pending();self.assertEqual(self.page.locator('[data-nav="work"]').first.evaluate("e=>getComputedStyle(e,'::after').content"),'""');self.page.locator('.close-modal').click();self.page.evaluate("location.hash='#/settings'")
  self.state='completed'
  self.page.wait_for_selector('[data-video-ready]',timeout=15000)
  self.assertEqual([r for r in self.rows() if r['idempotency_key']][0]['status'],'done')
  self.assertIn('Your video is ready',self.page.locator('[data-video-ready]').inner_text())
  self.page.locator('[data-video-ready] button').click()
  self.page.wait_for_selector('#work-player[src^="blob:"]')
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
 def test_reload_resumes_without_post_and_single_cross_tab_owner(self):
  self.start_pending();before=self.polls
  self.page.reload();self.page.wait_for_function("document.documentElement.dataset.videoRendering==='true'")
  self.page.wait_for_timeout(800)
  self.assertGreater(self.polls,before)
  other=self.ctx.new_page();other.goto(self.url+'/#/settings');other.wait_for_selector('#view')
  self.page.wait_for_timeout(800);before=self.polls
  self.page.wait_for_timeout(6000)
  self.assertLessEqual(self.polls-before,1,'one origin-wide owner, not one poller per tab')
  self.state='completed';self.page.wait_for_selector('[data-video-ready]',timeout=40000)
  self.assertEqual([r for r in self.rows() if r['idempotency_key']][0]['status'],'done')
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
 def test_uncertain_no_id_reload_never_resubmits_and_idb_blocks_without_legacy(self):
  self.lost=True;self.open();self.plan();self.page.evaluate("async()=>{(await import('/js/store.js')).touch();}")
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click()
  self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('uncertain')")
  self.page.reload();self.page.wait_for_selector('.skill-card');self.page.wait_for_timeout(6000)
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1);self.assertEqual(self.polls,0)
  self.page.evaluate("localStorage.removeItem('motion-video.v1')")
  result=self.page.evaluate("""async()=>{const {durableVideoSession}=await import('/js/video-runtime.js');const s=await durableVideoSession();try{await s.create({model:'alibaba/wan-3.0/text-to-video',duration:5,prompt:'Different'},0.527778);return false;}catch(e){return e.message;}}""")
  self.assertIn('pending',result);self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
 def test_storage_abort_blocks_paid_plan_and_render(self):
  self.open()
  self.page.evaluate("""()=>{window.addOriginal=IDBObjectStore.prototype.add;IDBObjectStore.prototype.add=function(){this.transaction.abort();throw new DOMException('fixture abort','QuotaExceededError');};}""")
  self.page.locator('#video-topic').fill('Fixture');self.page.locator('#video-plan').click()
  self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('fixture abort')")
  self.assertEqual(self.calls,[])
  self.page.evaluate("()=>{IDBObjectStore.prototype.add=window.addOriginal;}")
  self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.evaluate("""()=>{IDBObjectStore.prototype.add=function(){this.transaction.abort();throw new DOMException('fixture abort','QuotaExceededError');};}""")
  self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('fixture abort')")
  self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls))
 def test_key_change_discards_modal_and_stale_ready_notice(self):
  self.start_pending()
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-different-account'});}")
  self.page.wait_for_timeout(300)
  self.assertEqual(self.page.locator('.modal').count(),0)
  self.assertEqual(self.page.locator('#layout[inert]').count(),0)
  before=self.polls;self.state='completed';self.page.wait_for_timeout(6000)
  self.assertEqual(self.polls,before);self.assertEqual(self.page.locator('[data-video-ready]').count(),0)
  rows=self.page.evaluate("async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();return c.store.list();}")
  self.assertEqual(rows,[])
 def test_immediate_completed_create_announces_ready(self):
  self.open();self.plan()
  self.page.route('**/v1/videos',lambda r:r.fulfill(status=200,json={'id':'vid_offline','status':'completed'}))
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click()
  self.page.wait_for_selector('[data-video-ready]',timeout=4000)
  self.assertEqual(self.polls,0)
 def test_gateway_timeout_stops_observing_without_resubmission(self):
  self.page.clock.install();self.start_pending();self.page.clock.fast_forward(86400000)
  self.page.clock.run_for(60000);self.page.wait_for_timeout(200)
  row=[r for r in self.rows() if r['idempotency_key']][0]
  self.assertTrue(row['outputs'].get('polling_timeout'));before=self.polls
  self.page.clock.run_for(60000);self.page.wait_for_timeout(100)
  self.assertEqual(self.polls,before);self.assertEqual(row['status'],'rendering')
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
 def test_reopen_restores_durable_plan_prompt_and_receipts(self):
  self.open();self.plan();self.page.locator('#video-prompt').fill('Edited prompt before approval')
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.page.reload();self.open()
  self.page.wait_for_function("document.querySelector('#video-prompt')?.value==='Edited prompt before approval'")
  self.assertIn('shotbeats',self.page.locator('#video-plan-json').input_value())
  self.assertEqual(self.page.locator('#video-topic').input_value(),'An offline paper boat')
  self.assertIn('anthropic/claude-sonnet-5.5',self.page.locator('#video-receipts').inner_text())
 def rows(self):
  return self.page.evaluate("async()=>{const a=await(await import('/js/run-store.js')).openRunStore({key:'offline-not-real-key'});try{return await a.list();}finally{a.close();}}")
 def check_chat(self,r):
  rows=self.rows();self.assertEqual(len(rows),1);self.assertEqual(rows[0]['status'],'running')
  self.assertEqual(rows[0]['inputs']['topic'],'An offline paper boat');self.route(r)
 def test_my_work_merges_fresh_gateway_terminal_and_local_prompt(self):
  self.start_pending();self.page.locator('.close-modal').click()
  self.page.route('**/v1/videos?*',lambda r:r.fulfill(json={'items':[{'id':'vid_offline','status':'completed','params':{'prompt':'Gateway prompt'}},{'id':'vid_elsewhere','status':'completed','params':{'prompt':'Other device'}}],'next_cursor':None}))
  self.page.evaluate("location.hash='#/work'");self.page.wait_for_function("document.querySelectorAll('.work-card').length===2")
  card=self.page.locator('.work-card').filter(has_text='vid_offline')
  self.assertIn('completed',card.inner_text());self.assertIn('A paper boat drifts on a calm pond.',card.inner_text())
  self.assertIn('Other device',self.page.locator('#work-list').inner_text())
 def check_post(self,r):
  rows=self.rows();row=[x for x in rows if x['idempotency_key']==r.request.headers.get('idempotency-key')][0]
  self.assertEqual(row['video_status'],'creating');self.assertEqual(row['status'],'rendering')
  self.assertEqual(row['prompt'],r.request.post_data_json['prompt']);self.checked=True
  r.fulfill(status=202,json={'id':'vid_offline','status':'queued'})

# Exclude inherited tests, whose modal-owned polling expectations are superseded.
for name in list(vars(VideoBrowser)):
 if name.startswith('test_') and name not in vars(DurableVideoBrowser):
  setattr(DurableVideoBrowser,name,None)
del VideoBrowser
if __name__=='__main__':unittest.main()
