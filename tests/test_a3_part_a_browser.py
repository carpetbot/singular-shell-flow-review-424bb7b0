"""Part A integration: canonical run routing, prefill, notices, cache; OFFLINE FIXTURE."""
import json,unittest
import test_video_browser as fixture
class PartA(unittest.TestCase):
 setUp=fixture.VideoBrowser.setUp
 tearDown=fixture.VideoBrowser.tearDown
 route=fixture.VideoBrowser.route
 plan=fixture.VideoBrowser.plan
 def seed(self):
  self.page.goto(self.url+'/#/settings');self.page.wait_for_selector('#apikey')
  return self.page.evaluate("""async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-not-real-key'});const c=await(await import('/js/video-runtime.js')).videoContext();return (await c.store.create({flow_id:'claw__motion-trimmer-video',title:'OFFLINE FIXTURE saved boat',status:'done',video_status:'completed',video_job_id:'vid_offline',prompt:'Recorded fixture boat prompt',inputs:{topic:'Original fixture brief',context:'Saved creative context',platform:'instagram-reels',duration:5},cost:.53,model_ids:['fixture/video']})).id;}""")
 def test_canonical_detail_reload_back_and_prefill_no_paid_identity(self):
  identity=self.seed();self.page.goto(self.url+'/#/work/'+identity);self.page.wait_for_selector('#work-detail');self.page.wait_for_selector('#work-player')
  self.assertIn('Recorded fixture boat prompt',self.page.locator('.detail-meta').inner_text());self.assertIn('$0.53',self.page.locator('.detail-meta').inner_text())
  self.page.reload();self.page.wait_for_selector('#work-player');self.assertEqual(len([c for c in self.calls if '/content' in c['path']]),1)
  self.page.get_by_role('button',name='Run again with changes',exact=True).click();self.page.wait_for_selector('[data-video-page]');self.page.wait_for_function("document.querySelector('#video-topic').value==='Original fixture brief'")
  self.assertEqual(self.page.locator('#video-context').input_value(),'Saved creative context');self.assertEqual(self.page.locator('#video-platform').input_value(),'instagram-reels');self.assertTrue(self.page.locator('#video-generate').is_disabled())
  self.assertIsNone(self.page.evaluate("sessionStorage.getItem('singular:run-again.v1')"));self.assertEqual([c for c in self.calls if c['path']=='/v1/videos'],[])
  self.page.go_back();self.page.wait_for_selector('#work-detail');self.page.wait_for_selector('#work-player');self.assertEqual(self.errors,[])
 def test_pickup_and_mywork_links_reach_same_durable_identity_without_prefetch(self):
  identity=self.seed();self.page.goto(self.url+'/#/create');self.page.wait_for_selector('.pickup-card');self.assertEqual(self.page.locator('.pickup-card').first.get_attribute('href'),'#/work/'+identity)
  self.page.locator('.pickup-card').first.click();self.page.wait_for_selector('#work-detail');self.page.wait_for_selector('#work-player')
  self.page.locator('#rail [data-nav=work]').click();self.page.wait_for_selector('.work-card');link=self.page.locator('.work-card a').first;self.assertEqual(link.get_attribute('href'),'#/work/'+identity)
  self.assertEqual(len([c for c in self.calls if '/content' in c['path']]),1);link.click();self.page.wait_for_selector('#work-player');self.assertEqual(len([c for c in self.calls if '/content' in c['path']]),1)
 def test_ready_notice_open_is_canonical_detail_not_job_as_run_id(self):
  self.state='processing';self.seed();self.page.goto(self.url+'/#/flow/claw__motion-trimmer-video');self.page.wait_for_selector('#video-topic');self.plan();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click()
  self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('processing')")
  identity=self.page.evaluate("async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();return (await c.store.list()).find(r=>r.idempotency_key).id;}")
  self.page.locator('#rail [data-nav=create]').click();self.state='completed';self.page.wait_for_selector('[data-video-ready]',timeout=18000);self.page.locator('[data-video-ready] button').click();self.page.wait_for_selector('#work-detail');self.page.wait_for_selector('#work-player')
  self.assertTrue(self.page.url.endswith('#/work/'+identity));self.assertNotEqual(identity,'vid_offline')
 def test_foreign_or_credential_prefill_is_discarded_without_form_or_network(self):
  self.seed();self.page.evaluate("""()=>sessionStorage.setItem('singular:run-again.v1',JSON.stringify({v:1,account_id:'a'.repeat(64),flow_id:'claw__motion-trimmer-video',inputs:{topic:'Foreign account draft'},created_at:Date.now()}))""")
  self.page.goto(self.url+'/#/flow/claw__motion-trimmer-video');self.page.wait_for_selector('#video-topic');self.assertEqual(self.page.locator('#video-topic').input_value(),'');self.assertIsNone(self.page.evaluate("sessionStorage.getItem('singular:run-again.v1')"))
  self.assertEqual(self.calls,[])
 def test_optional_poster_store_unavailable_does_not_block_work_or_playback(self):
  identity=self.seed();self.page.evaluate("""()=>{const open=indexedDB.open.bind(indexedDB);indexedDB.open=(name,...args)=>name==='singular-posters.v1'?{}:open(name,...args);}""")
  self.page.evaluate("location.hash='#/work'");self.page.wait_for_selector('.work-card',timeout=5000);self.page.locator('.work-card a').first.click();self.page.wait_for_selector('#work-player',timeout=5000)
 def test_work_and_detail_actual_routes_desktop_phone_screenshots(self):
  identity=self.seed();out=fixture.ROOT/'reports/a3/c4';out.mkdir(parents=True,exist_ok=True)
  self.page.goto(self.url+'/#/work/'+identity);self.page.wait_for_selector('#work-player');self.page.wait_for_function("document.querySelector('#work-player').readyState>=2")
  self.page.evaluate("document.querySelector('#work-detail').prepend(Object.assign(document.createElement('p'),{textContent:'OFFLINE FIXTURE — synthetic blue video, no live render'}))")
  for width in [1280,390]:
   self.page.set_viewport_size({'width':width,'height':900});self.page.evaluate('scrollTo(0,0)');self.page.wait_for_timeout(100);self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   if width==1280:self.assertGreater(self.page.locator('.detail-meta').bounding_box()['x'],self.page.locator('#detail-output').bounding_box()['x'])
   self.page.screenshot(path=str(out/(f'detail-{width}-OFFLINE-FIXTURE.png')),full_page=True)
  self.page.locator('#tabbar [data-nav=work]').click();self.page.wait_for_selector('.work-card');self.page.wait_for_function("document.querySelector('#work-status').textContent.includes('loaded')")
  self.page.evaluate("document.querySelector('.work-page').prepend(Object.assign(document.createElement('p'),{textContent:'OFFLINE FIXTURE — saved video history'}))")
  for width in [1280,390]:
   self.page.set_viewport_size({'width':width,'height':900});self.page.evaluate('scrollTo(0,0)');self.page.wait_for_timeout(100);self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'));self.page.screenshot(path=str(out/(f'work-{width}-OFFLINE-FIXTURE.png')),full_page=True)
  self.page.evaluate("async()=>(await import('/js/store.js')).setSettings({apiKey:''})");self.page.wait_for_selector('#inline-key')
  for width in [1280,390]:
   self.page.set_viewport_size({'width':width,'height':900});self.page.evaluate('scrollTo(0,0)');self.page.wait_for_timeout(100);self.assertFalse(self.page.locator('#work-refresh').is_visible());self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'));self.page.screenshot(path=str(out/(f'work-empty-{width}-OFFLINE-FIXTURE.png')),full_page=True)
 def account_event(self):
  self.page.evaluate("""async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();const entry=Object.entries(localStorage).find(([k,v])=>{try{return JSON.parse(v).settings?.apiKey==='offline-not-real-key'}catch{return false}});const next=JSON.parse(entry[1]);next.settings.apiKey='offline-race-other-account';localStorage.setItem(entry[0],JSON.stringify(next));window.dispatchEvent(new StorageEvent('storage',{key:entry[0],oldValue:entry[1],newValue:JSON.stringify(next)}));window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));}""")
 def test_no_old_work_reappears_during_cross_tab_hydration_window(self):
  self.seed();self.page.goto(self.url+'/#/work');self.page.wait_for_selector('.work-card');self.account_event();self.page.wait_for_timeout(90)
  self.assertEqual(self.page.locator('.work-card').count(),0,'Old-account event must not redisplay old work while settings hydrate')
  self.page.wait_for_timeout(250);self.assertEqual(self.page.locator('.work-card').count(),0)
 def test_no_old_video_draft_reappears_during_cross_tab_hydration_window(self):
  self.seed();self.page.goto(self.url+'/#/flow/claw__motion-trimmer-video');self.page.wait_for_selector('#video-topic');self.plan();self.account_event();self.page.wait_for_timeout(90)
  self.assertFalse(self.page.evaluate("document.querySelector('#video-prompt')?.value.includes('paper boat')||false"),'Old-account draft must stay removed during hydration')
  self.page.wait_for_timeout(250);self.assertEqual(self.page.locator('#video-prompt').input_value(),'')
if __name__=='__main__':unittest.main()
