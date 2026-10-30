"""Production router acceptance, OFFLINE FIXTURE only."""
import unittest
import test_video_browser as fixture
from pathlib import Path
class VideoRoutes(unittest.TestCase):
 setUp=fixture.VideoBrowser.setUp
 tearDown=fixture.VideoBrowser.tearDown
 route=fixture.VideoBrowser.route
 plan=fixture.VideoBrowser.plan
 def connect(self):
  self.page.goto(self.url+'/#/settings');self.page.wait_for_selector('#apikey')
  self.page.evaluate("async()=>(await import('/js/store.js')).setSettings({apiKey:'offline-not-real-key'})")
 def test_direct_refresh_back_and_gallery_entry(self):
  self.connect();self.page.goto(self.url+'/#/flow/claw__motion-trimmer-video');self.page.wait_for_selector('[data-video-page]')
  self.assertEqual(self.page.locator('.modal,iframe').count(),0)
  self.page.reload();self.page.wait_for_selector('[data-video-page]');self.page.locator('#rail [data-nav=settings]').click();self.page.wait_for_selector('#apikey');self.page.go_back();self.page.wait_for_selector('[data-video-page]')
  self.page.goto(self.url+'/#/skills');self.page.wait_for_selector('.skill-card');self.page.locator('.skill-card').filter(has_text='Motion Trimmer → Video').click();self.page.wait_for_selector('[data-video-page]')
  self.assertTrue(self.page.url.endswith('#/flow/claw__motion-trimmer-video'));self.assertEqual(self.page.locator('.modal').count(),0)
  self.page.goto(self.url+'/#/create');self.page.wait_for_selector('[data-create-id]');self.page.locator('[data-create-id="claw__motion-trimmer-video"]').click();self.page.wait_for_selector('[data-video-page]')
  self.assertTrue(self.page.locator('#rail [data-nav=create]').evaluate('e=>e.classList.contains("active")'))
 def test_inline_cross_tab_remove_and_replace_clears_immediately(self):
  self.connect();self.page.goto(self.url+'/#/flow/claw__motion-trimmer-video');self.page.wait_for_selector('[data-video-page]');self.plan()
  other=self.ctx.new_page();other.goto(self.url+'/#/settings');other.wait_for_selector('#apikey')
  other.evaluate("async()=>(await import('/js/store.js')).setSettings({apiKey:'offline-route-replacement'})")
  self.page.wait_for_function("document.querySelector('#video-topic')?.value==='' && document.querySelector('#video-key')?.textContent.includes('Key connected')")
  self.assertEqual(self.page.locator('#video-prompt').input_value(),'');self.assertEqual(self.page.locator('#video-player[src]').count(),0)
  other.evaluate("async()=>(await import('/js/store.js')).setSettings({apiKey:''})")
  self.page.wait_for_selector('#inline-key');self.assertTrue(self.page.locator('#video-generate').is_disabled());self.assertEqual(self.calls and [c for c in self.calls if c['path']=='/v1/videos'],[])
  self.assertEqual(self.errors,[]);other.close()
 def test_real_page_lite_pro_desktop_phone_screenshots(self):
  self.connect();self.page.goto(self.url+'/#/flow/claw__motion-trimmer-video');self.page.wait_for_selector('[data-video-page]');self.plan();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.evaluate("document.querySelector('[data-video-page]').prepend(Object.assign(document.createElement('p'),{textContent:'OFFLINE FIXTURE — fictional plan, no live render'}))")
  out=fixture.ROOT/'reports/a3/c3-integration';out.mkdir(parents=True,exist_ok=True)
  for width,mode in [(1280,'lite'),(390,'lite'),(1280,'pro'),(390,'pro')]:
   self.page.set_viewport_size({'width':width,'height':900});self.page.locator('[data-mode-choice='+mode+']').click()
   self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   self.page.evaluate('scrollTo(0,0)');self.page.wait_for_timeout(100)
   self.page.screenshot(path=str(out/(f'video-{width}-{mode}-OFFLINE-FIXTURE.png')),full_page=True)
  self.assertEqual(self.errors,[])
if __name__=='__main__':unittest.main()
