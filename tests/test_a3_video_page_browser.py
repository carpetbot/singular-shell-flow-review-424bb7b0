"""A3 c3: route-owned video page, real Chromium, offline fixtures only.
Before the page exists, mount the current runner on the target route: RED is a
visible modal/layout behavior failure, never a missing module/import failure.
"""
import json
import unittest
from pathlib import Path
from test_video_browser import VideoBrowser, ROOT, APP
from test_durable_video_browser import DurableVideoBrowser

REPORT=ROOT/'reports/a3/c3-video'
class VideoPageBrowser(unittest.TestCase):
 setUp=VideoBrowser.setUp
 tearDown=VideoBrowser.tearDown
 plan=VideoBrowser.plan
 rows=DurableVideoBrowser.rows
 def route(self,r):
  path=r.request.url.split('?')[0]
  if path.endswith('/js/views/video-flow.js') and (APP/'js/views/video-flow.js').exists():
   r.fulfill(body=(APP/'js/views/video-flow.js').read_bytes(),content_type='text/javascript');return
  VideoBrowser.route(self,r)
 def open(self,confirmed=False,prefill=None):
  self.page.goto(self.url+'/#/settings');self.page.wait_for_selector('#apikey')
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-not-real-key'});}")
  self.page.evaluate("location.hash='#/flow/claw__motion-trimmer-video'")
  self.page.wait_for_timeout(150)
  if (APP/'js/views/video-flow.js').exists():
   self.page.evaluate("""async inputs=>{const m=await import('/js/views/video-flow.js');m.destroy();window.videoPage=m;const root=document.querySelector('#view');root.innerHTML=m.view();await m.bind(root,{inputs});}""",prefill)
  else:
   self.page.evaluate("async()=>{(await import('/js/video-ui.js')).openVideoRunner();}")
  self.page.wait_for_selector('#video-topic')
  self.page.evaluate("document.documentElement.dataset.mode='pro'") # Explicit manual-price/recovery controls are Pro in A3.
 def assert_page(self):
  self.assertEqual(self.page.locator('.modal,.modal-backdrop,iframe').count(),0,'Video must be a route-owned page, not the legacy modal')
  self.assertEqual(self.page.locator('[data-video-page]').count(),1)
 def quote(self):
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
 def test_page_layout_sample_and_pro(self):
  self.open();self.assert_page();self.page.evaluate("document.documentElement.dataset.mode='lite'")
  self.assertIn('Key connected · runs save to My work',self.page.locator('#video-key').inner_text())
  self.assertTrue(self.page.evaluate("!!(document.querySelector('#video-key').compareDocumentPosition(document.querySelector('#video-topic')) & Node.DOCUMENT_POSITION_FOLLOWING)"))
  self.page.locator('#video-sample').click();self.assertTrue(self.page.locator('#video-topic').input_value())
  self.assertIn('Plan',self.page.locator('#video-progress').inner_text())
  self.plan();self.assertIn('Approve',self.page.locator('[aria-current="step"]').inner_text())
  self.assertIn('Offline editor overlay',self.page.locator('#video-shot-list').inner_text())
  self.assertFalse(self.page.locator('#video-plan-json').is_visible());self.assertFalse(self.page.locator('#video-nodes').is_visible())
  self.page.locator('#video-prompt').fill('Edited readable prompt');self.assertEqual(json.loads(self.page.locator('#video-plan-json').input_value())['prompt'],'Edited readable prompt')
  self.page.evaluate("document.documentElement.dataset.mode='pro'")
  self.assertTrue(self.page.locator('#video-plan-json').is_visible());self.assertTrue(self.page.locator('#video-nodes').is_visible())
  self.assertIn('alibaba/wan-3.0/text-to-video',self.page.locator('#video-nodes').inner_text())
  self.page.set_viewport_size({'width':1280,'height':900})
  left=self.page.locator('#video-inputs').bounding_box();right=self.page.locator('#video-result').bounding_box();self.assertGreater(right['x'],left['x']+left['width'])
  REPORT.mkdir(parents=True,exist_ok=True);self.page.screenshot(path=str(REPORT/'desktop-pro.png'),full_page=True)
  self.page.set_viewport_size({'width':390,'height':844})
  left=self.page.locator('#video-inputs').bounding_box();right=self.page.locator('#video-result').bounding_box();self.assertGreaterEqual(right['y'],left['y']+left['height'])
  self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  self.page.screenshot(path=str(REPORT/'phone-pro.png'),full_page=True);self.assertEqual(self.errors,[])
 def test_prefill_is_inputs_only_and_unconnected_notice(self):
  self.open(prefill={'topic':'Fictional rerun','context':'A quiet ending','platform':'youtube-shorts','prompt':'not approved'})
  self.assert_page();self.assertEqual(self.page.locator('#video-topic').input_value(),'Fictional rerun');self.assertEqual(self.page.locator('#video-prompt').input_value(),'')
  self.page.evaluate("async()=>{videoPage.destroy();(await import('/js/store.js')).setSettings({apiKey:''});const root=document.querySelector('#view');root.innerHTML=videoPage.view();await videoPage.bind(root);}")
  self.assertIn('Connect your Singular key',self.page.locator('#video-key').inner_text());self.assertTrue(self.page.locator('#video-plan').is_disabled());self.assertTrue(self.page.locator('#video-generate').is_disabled())
 def test_durable_plan_render_edited_prompt_and_saved_step(self):
  self.open();self.assert_page();self.page.route('**/v1/chat/completions',self.check_chat);self.plan();self.quote()
  self.assertIn('charged only if it renders',self.page.locator('#video-charge-note').inner_text())
  self.page.locator('#video-prompt').fill('Edited page boat prompt');self.checked=False;self.page.route('**/v1/videos',self.check_post)
  self.page.locator('#video-generate').click();self.page.wait_for_selector('#video-player[src^="blob:"]');self.assertTrue(self.checked)
  row=next(r for r in self.rows() if r['idempotency_key']);self.assertEqual(row['prompt'],'Edited page boat prompt');self.assertEqual(row['outputs']['plan']['prompt'],'Edited page boat prompt');self.assertTrue(row['receipts'])
  self.assertIn('Saved',self.page.locator('[aria-current="step"]').inner_text());self.assertTrue(self.page.locator('#video-plan').is_disabled())
  self.page.locator('#video-new').click();self.page.wait_for_function("!document.querySelector('#video-plan').disabled");self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.assertEqual(self.submissions,1)
 def test_destroy_leaves_app_watcher_alive(self):
  self.state='processing';self.open();self.assert_page();self.plan();self.quote();self.page.locator('#video-generate').click()
  self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('processing')")
  self.page.evaluate("videoPage.destroy();document.querySelector('#view').replaceChildren();location.hash='#/settings'")
  self.state='completed';self.page.wait_for_selector('[data-video-ready]',timeout=18000)
  self.assertEqual(next(r for r in self.rows() if r['idempotency_key'])['status'],'done');self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
 def test_leave_during_planning_saves_result_without_mutating_new_route(self):
  self.open();held=[];self.page.route('**/v1/chat/completions',lambda r:held.append(r))
  self.page.locator('#video-topic').fill('Leave during offline planning');self.page.locator('#video-plan').click()
  self.page.wait_for_timeout(200);self.assertEqual(len(held),1)
  self.page.evaluate("videoPage.destroy();document.querySelector('#view').innerHTML='<p id=next-route>Next route stays untouched</p>'")
  self.route(held[0]);self.page.wait_for_timeout(500)
  self.assertEqual(self.page.locator('#next-route').inner_text(),'Next route stays untouched')
  row=next(r for r in self.rows() if r['inputs'].get('topic')=='Leave during offline planning');self.assertEqual(row['status'],'done');self.assertIn('shotbeats',row['outputs']['plan']);self.assertEqual(self.errors,[])
 def test_completed_run_again_prefill_starts_clean_draft(self):
  self.open();self.plan();self.quote();self.page.locator('#video-generate').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.page.evaluate("""async()=>{videoPage.destroy();videoPage.prefillVideoInputs({topic:'Run again fictional changes',platform:'x'});const root=document.querySelector('#view');root.innerHTML=videoPage.view();await videoPage.bind(root);}""")
  self.assertEqual(self.page.locator('#video-topic').input_value(),'Run again fictional changes');self.assertEqual(self.page.locator('#video-prompt').input_value(),'');self.assertFalse(self.page.locator('#video-plan').is_disabled());self.assertTrue(self.page.locator('#video-generate').is_disabled())
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
 def test_pending_prefill_never_replaces_recovery(self):
  self.lost=True;self.open();self.plan();self.quote();original=self.page.locator('#video-prompt').input_value();self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('uncertain')")
  self.open(prefill={'topic':'Must not replace uncertain original'})
  self.assertEqual(self.page.locator('#video-topic').input_value(),'An offline paper boat');self.assertEqual(self.page.locator('#video-prompt').input_value(),original);self.assertTrue(self.page.locator('#video-plan').is_disabled())
 def test_account_removal_clears_page_without_foreign_draft(self):
  self.open();self.plan();self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:''});}")
  self.page.wait_for_function("document.querySelector('#video-key').textContent.includes('Connect your Singular key')")
  self.assertEqual(self.page.locator('#video-topic').input_value(),'');self.assertEqual(self.page.locator('#video-prompt').input_value(),'');self.assertTrue(self.page.locator('#video-generate').is_disabled());self.assertEqual(self.errors,[])
 def test_progress_visible_at_phone_width(self):
  self.open();self.page.set_viewport_size({'width':390,'height':844})
  self.assertTrue(self.page.locator('#video-progress').is_visible());self.assertGreater(self.page.locator('#video-progress').bounding_box()['height'],20)
 check_chat=DurableVideoBrowser.check_chat
 def check_post(self,r):
  self.submissions=getattr(self,'submissions',0)+1
  DurableVideoBrowser.check_post(self,r)
 # Existing strict IDB-abort and identity tests now exercise this page binding.
 test_storage_abort_blocks_paid_plan_and_render=DurableVideoBrowser.test_storage_abort_blocks_paid_plan_and_render
 test_same_session_replan_after_add_abort_preserves_bound_evidence=DurableVideoBrowser.test_same_session_replan_after_add_abort_preserves_bound_evidence
 test_wrong_retry_cannot_replace_reload_recovery_draft=DurableVideoBrowser.test_wrong_retry_cannot_replace_reload_recovery_draft
 def test_unknown_price_invalid_json_and_http_errors(self):
  self.open();self.plan();original=self.page.locator('#video-plan-json').input_value()
  self.page.locator('#video-plan-json').fill('{"shotbeats":[]}');self.page.wait_for_function("document.querySelector('#video-price').textContent.includes('Price unavailable')")
  self.assertTrue(self.page.locator('#video-generate').is_disabled());self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls))
  for model in self.catalog['models']:
   if model['id']=='alibaba/wan-3.0/text-to-video':model['videoPricing']['configs']=[]
  self.page.locator('#video-plan-json').fill(original);self.page.wait_for_function("document.querySelector('#video-price').textContent.includes('price unavailable')");self.assertTrue(self.page.locator('#video-generate').is_disabled())
  self.chat_status=401;self.page.locator('#video-plan').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('authentication')")
  self.chat_status=402;self.page.locator('#video-plan').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('credits')")
  self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls));self.assertEqual(self.errors,[])

def load_tests(loader,tests,pattern):
 # Imported compatibility classes supply fixtures, not duplicate acceptance tests.
 return loader.loadTestsFromTestCase(VideoPageBrowser)

if __name__=='__main__':unittest.main()
