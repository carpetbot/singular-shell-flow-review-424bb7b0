"""Real Chromium / IndexedDB; explicit OFFLINE FIXTURE catalog only."""
import unittest
from pathlib import Path
from test_video_browser import VideoBrowser, ROOT

class CreateBrowser(unittest.TestCase):
 setUp=VideoBrowser.setUp
 tearDown=VideoBrowser.tearDown
 route=VideoBrowser.route
 def home(self):
  self.page.goto(self.url);self.page.wait_for_selector('.skill-card')
 def test_default_navigation_refresh_back_and_modes(self):
  self.home();self.assertEqual(self.page.locator('h1').inner_text(),'What do you want to make?')
  self.assertEqual(self.page.evaluate('location.hash'),'#/create')
  self.page.locator('#rail a[data-nav="work"]').click();self.page.wait_for_selector('#work-list',state='attached')
  self.page.reload();self.page.wait_for_selector('#work-list',state='attached');self.page.go_back();self.page.wait_for_selector('h1')
  self.assertEqual(self.page.locator('h1').inner_text(),'What do you want to make?')
  self.page.goto(self.url+'/#/skills');self.page.wait_for_selector('.skill-card');self.assertIn('Flows',self.page.locator('#view').inner_text())
  self.page.goto(self.url+'/#/create');self.page.wait_for_selector('h1')
  self.assertFalse(self.page.locator('#rail [data-nav="chat"]').is_visible())
  self.page.locator('[data-mode-choice="pro"]').click();self.assertTrue(self.page.locator('#rail [data-nav="chat"]').is_visible())
  self.page.locator('#rail [data-nav="chat"]').click();self.page.wait_for_selector('#chatlog')
  self.page.locator('[data-mode-choice="lite"]').click();self.page.wait_for_selector('h1');self.assertEqual(self.page.locator('h1').inner_text(),'What do you want to make?')
 def test_catalog_prices_change_and_unknown_is_not_zero(self):
  self.home();card=self.page.locator('[data-create-id="claw__motion-trimmer-video"]');self.assertIn('$0.53',card.inner_text())
  self.page.evaluate("async()=>{const s=await import('/js/store.js');const c=structuredClone(s.get().catalog);c.models.find(m=>m.id==='alibaba/wan-3.0/text-to-video').videoPricing.configs.forEach(p=>p.priceUsd=1.25);s.set({catalog:c});}")
  self.page.wait_for_function("document.querySelector('[data-create-id=claw__motion-trimmer-video]').textContent.includes('$1.25')")
  self.page.evaluate("async()=>{const s=await import('/js/store.js');s.set({catalog:{models:[]}})}")
  self.page.wait_for_function("document.querySelector('[data-create-id=claw__motion-trimmer-video]').textContent.includes('Price unavailable')")
 def test_pickups_scoped_limit_and_account_removal(self):
  self.home();self.page.evaluate("""async()=>{const s=await import('/js/store.js');s.setSettings({apiKey:'offline-create-account'});const {videoContext}=await import('/js/video-runtime.js');const c=await videoContext('offline-create-account');for(let i=0;i<3;i++)await c.store.create({flow_id:'claw__motion-trimmer-video',title:'OFFLINE FIXTURE pickup '+i,status:i===2?'rendering':'done',created_at:new Date(Date.now()+i*1000).toISOString(),inputs:{topic:'fictional'},outputs:{},prompt:'OFFLINE FIXTURE pickup '+i});window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));}""")
  self.page.wait_for_function("document.querySelectorAll('.pickup-card').length===2")
  self.assertIn('pickup 2',self.page.locator('#create-pickups').inner_text());self.assertNotIn('pickup 0',self.page.locator('#create-pickups').inner_text())
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-other-account'})}");self.page.wait_for_function("document.querySelectorAll('.pickup-card').length===0")
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:''})}");self.assertNotIn('pickup',self.page.locator('#create-pickups').inner_text())
 def test_mobile_reference_no_overflow(self):
  self.page.set_viewport_size({'width':390,'height':844});self.home()
  self.assertTrue(self.page.locator('#tabbar [data-nav="create"]').is_visible());self.assertFalse(self.page.locator('#rail').is_visible())
  self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  self.assertTrue(self.page.locator('#create-grid').evaluate("e=>e.scrollWidth<=e.clientWidth"),'Create must not hide outcomes in an internal horizontal carousel')
  boxes=self.page.locator('#create-grid .skill-card').evaluate_all("els=>els.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,right:r.right,y:r.y};})")
  self.assertTrue(all(b['x']>=0 and b['right']<=390 for b in boxes));self.assertTrue(all(boxes[i]['y']>boxes[i-1]['y'] for i in range(1,len(boxes))))
  self.page.evaluate("document.querySelector('h1').before(Object.assign(document.createElement('p'),{textContent:'OFFLINE FIXTURE — no live inference'}))")
  out=ROOT/'reports/a3/c2';out.mkdir(parents=True,exist_ok=True);self.page.screenshot(path=str(out/'create-390-OFFLINE-FIXTURE.png'),full_page=True)
  self.page.set_viewport_size({'width':1280,'height':900});self.page.screenshot(path=str(out/'create-desktop-OFFLINE-FIXTURE.png'),full_page=True)
del VideoBrowser
if __name__=='__main__':unittest.main()
