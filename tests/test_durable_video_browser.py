"""A2 integration: real Chromium/IndexedDB, loopback fixtures only."""
from test_video_browser import VideoBrowser
import unittest

class DurableVideoBrowser(VideoBrowser):
 # Reuse fixture setup, not the inherited legacy acceptance cases.
 def test_durable_saved_before_post_and_plan_before_chat(self):
  self.open();self.plan()
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
 def rows(self):
  return self.page.evaluate("async()=>{const a=await(await import('/js/run-store.js')).openRunStore({key:'offline-not-real-key'});try{return await a.list();}finally{a.close();}}")
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
