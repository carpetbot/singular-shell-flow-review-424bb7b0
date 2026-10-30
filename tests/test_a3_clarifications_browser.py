"""Approved A3 clarification behavior; explicit OFFLINE FIXTURE only."""
import unittest,json
import test_video_browser as fixture
from pathlib import Path

class Clarifications(unittest.TestCase):
 setUp=fixture.VideoBrowser.setUp
 tearDown=fixture.VideoBrowser.tearDown
 plan=fixture.VideoBrowser.plan
 route=fixture.VideoBrowser.route
 def mount(self,module,key='offline-not-real-key'):
  self.page.goto(self.url+'/#/settings');self.page.wait_for_selector('#apikey')
  self.page.evaluate("async key=>(await import('/js/store.js')).setSettings({apiKey:key})",key)
  self.page.evaluate("""async module=>{const m=await import('/js/views/'+module+'.js');window.mounted=m;document.querySelector('#view').innerHTML=m.view();await m.bind(document.querySelector('#view'));}""",module)
 def test_lite_actual_copy_auto_quote_and_pro_caveats(self):
  self.mount('video-flow');self.page.wait_for_selector('#video-topic')
  self.assertEqual(self.page.locator('#video-plan').inner_text(),'Plan my video')
  self.assertEqual(self.page.locator('#video-lite-summary').inner_text(),'5-second clip · landscape for now · you approve the price first')
  self.assertFalse(self.page.locator('#video-quote').is_visible())
  self.assertFalse(self.page.locator('#video-defaults').is_visible())
  for old in ['not an exact editing timeline','Platform is creative context only','No image uploads','No aspect ratio']:
   self.assertNotIn(old,self.page.locator('[data-video-page]').inner_text())
  self.assertIn('Planning uses a separately billed text call',self.page.locator('#video-plan-charge').inner_text())
  self.plan();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.assertEqual(self.page.locator('#video-generate').inner_text(),'Generate · $0.53')
  self.assertEqual(self.page.locator('#video-charge-note').inner_text(),'charged only if it renders')
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),0)
  self.page.locator('[data-mode-choice=pro]').click();self.assertTrue(self.page.locator('#video-quote').is_visible());self.assertTrue(self.page.locator('#video-defaults').is_visible())
 def test_inline_video_connect_does_not_validate_or_generate(self):
  self.mount('video-flow','')
  self.assertTrue(self.page.locator('#inline-key').is_visible(),'Inline usable key input, not a Settings link')
  self.assertTrue(self.page.evaluate("!!(document.querySelector('#video-key').compareDocumentPosition(document.querySelector('#video-topic')) & Node.DOCUMENT_POSITION_FOLLOWING)"))
  self.page.locator('#inline-key').fill('offline-inline-connect');self.page.locator('#inline-connect').click()
  self.page.wait_for_function("document.querySelector('#video-key').textContent.includes('Key connected')")
  self.page.wait_for_function("!document.querySelector('#video-plan').disabled");self.assertFalse(self.page.locator('#video-plan').is_disabled());self.assertEqual(self.calls,[])
  self.assertNotIn('offline-inline-connect',self.page.url)
  rows=self.page.evaluate("async()=>(await (await import('/js/video-runtime.js')).videoContext()).store.list()")
  self.assertNotIn('offline-inline-connect',json.dumps(rows))
 def test_auto_quote_ignores_stale_responses_and_new_version(self):
  self.mount('video-flow');self.plan();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  held=[];self.page.route('**/pricing.json',lambda r:held.append(r))
  self.page.locator('#video-model').select_option('minimax/h3-max-turbo');self.page.wait_for_timeout(150)
  self.assertTrue(self.page.locator('#video-generate').is_disabled());self.assertEqual(len(held),1)
  self.page.locator('#video-model').select_option('alibaba/wan-3.0/text-to-video');self.page.wait_for_timeout(150);self.assertEqual(len(held),2)
  held[1].fulfill(json=self.catalog);self.page.wait_for_function("document.querySelector('#video-generate').textContent==='Generate · $0.53'")
  held[0].fulfill(json=self.catalog);self.page.wait_for_timeout(100)
  self.assertEqual(self.page.locator('#video-generate').inner_text(),'Generate · $0.53')
  self.page.locator('#video-prompt').fill('Edited OFFLINE FIXTURE prompt');self.assertTrue(self.page.locator('#video-generate').is_disabled());self.page.wait_for_timeout(150);held[2].fulfill(json=self.catalog)
  self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),0)
  self.page.unroute('**/pricing.json');self.page.route('**/pricing.json',lambda r:r.fulfill(json=self.catalog))
  self.page.locator('#video-generate').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
  self.page.locator('#video-new').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.assertEqual(self.page.locator('#video-generate').inner_text(),'Generate · $0.53');self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
if __name__=='__main__':unittest.main()
