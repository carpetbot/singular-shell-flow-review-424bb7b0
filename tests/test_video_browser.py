"""Offline fake inference only. All non-loopback traffic is aborted."""
import http.server, importlib.util, json, os, threading, unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
APP=Path(os.environ.get('VIDEO_APP_ROOT',str(ROOT)))
EVIDENCE=Path(os.environ.get('VIDEO_EVIDENCE',str(ROOT/'reports/motion-video')))
class VideoBrowser(unittest.TestCase):
 def setUp(self):
  spec=importlib.util.spec_from_file_location('video_proxy',APP/'proxy.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),p.Handler);threading.Thread(target=self.server.serve_forever,daemon=True).start()
  self.pw=sync_playwright().start();self.browser=self.pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);self.ctx=self.browser.new_context(accept_downloads=True)
  self.calls=[];self.errors=[];self.content_fail=False;self.polls=0;self.state='completed';self.chat_status=200;self.video_status=202;self.lost=False
  self.catalog=json.loads(Path(ROOT/'tests/fixtures/video-pricing.json').read_text())
  self.catalog['as_of']=datetime.now(timezone.utc).isoformat() # explicit offline fresh response
  self.ctx.route('**/*',self.route);self.page=self.ctx.new_page();self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.set_default_timeout(4000)
  self.url='http://127.0.0.1:'+str(self.server.server_port)
 def tearDown(self):
  self.browser.close();self.pw.stop();self.server.shutdown();self.server.server_close()
 def route(self,r):
  path=urlsplit(r.request.url).path
  if path=='/pricing.json':r.fulfill(json=self.catalog)
  elif path=='/v1/chat/completions':
   b=r.request.post_data_json;self.calls.append({'path':path,'body':b})
   if self.chat_status!=200:r.fulfill(status=self.chat_status,json={'error':{'message':'Offline fixture error'}});return
   d=json.loads(b['messages'][1]['content'])['duration'];plan={'shotbeats':[{'duration_s':d,'description':'Offline fixture boat drift'}],'prompt':'A paper boat drifts on a calm pond.','overlays':[{'at_s':0,'text':'Offline editor overlay'}],'dropped':['Exact logo unsupported']}
   r.fulfill(json={'model':b['model'],'choices':[{'message':{'content':json.dumps(plan)}}],'usage':{'prompt_tokens':20,'completion_tokens':60}})
  elif path=='/v1/videos' and r.request.method=='GET':r.fulfill(json={'items':[],'next_cursor':None})
  elif path=='/v1/videos' and r.request.method=='POST':
   self.calls.append({'path':path,'body':r.request.post_data_json,'token':r.request.headers.get('idempotency-key')})
   if self.lost:r.abort();return
   r.fulfill(status=self.video_status,json={'id':'vid_offline','status':'queued'})
  elif path=='/v1/videos/vid_offline':
   self.polls+=1;r.fulfill(json={'id':'vid_offline','status':self.state,'cost_usd':.527778 if self.state=='completed' else 0,'result_url':'/v1/videos/vid_offline/content' if self.state=='completed' else None,'error':'content_policy_violation' if self.state=='failed' else None})
  elif path=='/v1/videos/vid_offline/content':
   self.calls.append({'path':path,'auth':r.request.headers.get('authorization')})
   if self.content_fail:r.fulfill(status=502,json={'code':'video_result_unavailable'})
   else:r.fulfill(body=(ROOT/'tests/fixtures/offline-video.mp4').read_bytes(),content_type='video/mp4')
  elif urlsplit(r.request.url).hostname=='127.0.0.1':r.continue_()
  else:r.abort()
 def open(self,confirmed=False):
  self.page.goto(self.url+'/#/skills');self.page.wait_for_selector('.skill-card')
  self.page.evaluate("async()=>{const {setSettings}=await import('/js/store.js');setSettings({apiKey:'offline-not-real-key'});}")
  if confirmed:self.page.evaluate("async()=>{const {openVideoRunner}=await import('/js/video-ui.js');openVideoRunner({fields:{duration:'fixture_duration',aspectRatio:null,audio:null}});}")
  else:self.page.locator('.skill-card').filter(has_text='Motion Trimmer → Video').click()
 def plan(self):
  self.page.locator('#video-topic').fill('An offline paper boat');self.page.locator('#video-plan').click();self.page.wait_for_function("document.querySelector('#video-plan-json')?.value.includes('shotbeats')")
 def test_clear_finished_selection_preserves_pending(self):
  self.state='queued';self.open(True)
  self.page.evaluate('''async()=>{const {VideoSession}=await import('/js/video.js');const s=new VideoSession({key:'offline-not-real-key',fields:{duration:'fixture_duration'}});await s.create({model:'alibaba/wan-3.0/text-to-video',duration:15,prompt:'Offline boat'},1.583334);const pending=structuredClone(s.record);localStorage.setItem('motion-video.v1',JSON.stringify([{...pending,token:'done',id:'old',status:'completed'},pending]));}''')
  self.open(True);self.page.locator('#video-history').select_option('0');self.page.locator('#video-clear').click()
  self.page.wait_for_function("document.querySelector('#video-history').options.length===1")
  self.assertIn('vid_offline',self.page.locator('#video-history').inner_text())
  self.assertTrue(self.page.locator('#video-new').is_disabled());self.assertFalse(self.page.locator('#video-resume').is_disabled())
  self.assertEqual(len(self.page.evaluate("JSON.parse(localStorage.getItem('motion-video.v1'))")),1)
 def test_lite_shot_list_pro_editor_and_prompt_stay_synchronized(self):
  self.open(True);self.plan()
  self.assertFalse(self.page.locator('#video-plan-json').is_visible())
  self.assertIn('0–5 s',self.page.locator('#video-shot-list').inner_text())
  self.assertIn('Offline editor overlay',self.page.locator('#video-shot-list').inner_text())
  self.assertIn('Exact logo unsupported',self.page.locator('#video-shot-list').inner_text())
  self.page.locator('#video-prompt').fill('Changed shared prompt')
  self.page.evaluate("document.documentElement.dataset.mode='pro'")
  self.assertTrue(self.page.locator('#video-plan-json').is_visible())
  p=json.loads(self.page.locator('#video-plan-json').input_value());self.assertEqual(p['prompt'],'Changed shared prompt')
  p['shotbeats'][0]['description']='<img src=x onerror=alert(1)>';p['prompt']='Edited in Pro'
  self.page.locator('#video-plan-json').fill(json.dumps(p))
  self.page.evaluate("document.documentElement.dataset.mode='lite'")
  self.assertEqual(self.page.locator('#video-prompt').input_value(),'Edited in Pro')
  self.assertIn('<img src=x onerror=alert(1)>',self.page.locator('#video-shot-list').inner_text())
  self.assertEqual(self.page.locator('#video-shot-list img').count(),0)
  EVIDENCE.mkdir(parents=True,exist_ok=True)
  self.page.screenshot(path=str(EVIDENCE/'lite-plan.png'))
  self.page.evaluate("document.documentElement.dataset.mode='pro'")
  self.page.screenshot(path=str(EVIDENCE/'pro-plan.png'))
  self.assertEqual(self.errors,[])
 def test_01_gallery_five_second_default_mode(self):
  self.open();self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.assertIn('$0.53',self.page.locator('#video-price').inner_text())
  self.assertEqual(self.page.locator('#video-duration').count(),0)
  self.assertIn('ratio not guaranteed',self.page.locator('.modal').inner_text())
  self.page.locator('#video-generate').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  body=[c['body'] for c in self.calls if c['path']=='/v1/videos'][0]
  self.assertEqual(set(body),{'model','prompt','resolution'})
  self.assertEqual(json.loads(self.page.locator('#video-plan-json').input_value())['shotbeats'][0]['duration_s'],5)
  self.page.locator('#video-new').click();self.page.locator('#video-model').select_option('minimax/h3-max-turbo');self.page.locator('#video-quote').click();self.page.wait_for_function("document.querySelector('#video-price').textContent.includes('$0.21')")
  self.assertIn('unspecified',self.page.locator('#video-defaults').inner_text())
  self.catalog['models'][next(i for i,m in enumerate(self.catalog['models']) if m['id']=='minimax/h3-max-turbo')]['videoPricing']['defaults']['duration']=15
  self.page.locator('#video-quote').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('defaults could not be confirmed')")
  self.assertTrue(self.page.locator('#video-generate').is_disabled())
  self.assertEqual(self.errors,[])
 def test_02_confirmed_offline_brief_player_download_retry(self):
  self.content_fail=True;self.open(True);self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.locator('#video-generate').dblclick();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('retry download')")
  self.assertIn('completed',self.page.locator('#video-receipts').inner_text());self.assertIn('$0.53',self.page.locator('#video-receipts').inner_text())
  self.content_fail=False;self.page.locator('#video-download-retry').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.page.wait_for_function("document.querySelector('#video-player').readyState>=1")
  self.page.locator('#video-player').evaluate('async e=>{e.muted=true;await e.play();}')
  self.page.wait_for_function("document.querySelector('#video-player').currentTime>0.1");self.page.locator('#video-player').evaluate('e=>e.pause()')
  self.assertLessEqual(self.page.locator('#video-download').bounding_box()['height'],64,'Download action must not stretch to player height')
  with self.page.expect_download() as d:self.page.locator('#video-download').click()
  out=EVIDENCE/'offline-download.mp4';EVIDENCE.mkdir(exist_ok=True);d.value.save_as(out);self.assertEqual(out.read_bytes(),(ROOT/'tests/fixtures/offline-video.mp4').read_bytes())
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1);self.assertEqual(self.errors,[])
  self.page.evaluate("()=>{const b=document.createElement('div');b.textContent='OFFLINE FAKE INFERENCE · synthetic 1-second fixture, not a model render';b.style='position:fixed;top:0;left:0;z-index:99999;background:#ffed8a;color:#111;padding:8px';document.body.append(b);}")
  self.page.screenshot(path=str(EVIDENCE/'offline-player.png'))
  (EVIDENCE/'video-wire.offline.json').write_text(json.dumps({'fixture':'Explicit offline fake inference; fixture_duration is not a documented production field','requests':[{k:(bool(value) if k=='auth' else value) for k,value in c.items()} for c in self.calls],'receipts':self.page.locator('#video-receipts').inner_text(),'recovery_refs':json.loads(self.page.evaluate("localStorage.getItem('motion-video.v1')"))},indent=2))
  self.assertNotIn('offline-not-real-key',self.page.locator('#video-player').get_attribute('src'))
  self.page.reload();self.page.wait_for_selector('.skill-card');self.open(True);self.page.locator('#video-resume').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)

 def test_03_unknown_price_invalid_json_and_http_errors_do_not_generate(self):
  self.open(True);self.plan()
  self.page.evaluate("document.documentElement.dataset.mode='pro'")
  self.page.locator('#video-plan-json').fill('{"shotbeats":[]}');self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('Invalid planner')")
  self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls))
  self.page.locator('#video-plan-json').fill('{"shotbeats":[]}')
  for model in self.catalog['models']:
   if model['id']=='alibaba/wan-3.0/text-to-video':model['videoPricing']['configs']=[]
  self.page.locator('#video-quote').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('price unavailable')");self.assertTrue(self.page.locator('#video-generate').is_disabled())
  self.chat_status=401;self.page.locator('#video-plan').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('authentication')")
  self.chat_status=402;self.page.locator('#video-plan').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('credits')")
  self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls));self.assertEqual(self.errors,[])
 def test_04_uncertain_reload_same_payload_token(self):
  self.lost=True;self.open(True);self.plan();prompt=self.page.locator('#video-prompt').input_value();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('uncertain')")
  saved=self.page.evaluate("localStorage.getItem('motion-video.v1')");self.assertNotIn(prompt,saved);self.assertNotIn('offline-not-real-key',saved)
  self.open(True);self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)
  self.page.locator('#video-prompt').fill(prompt);self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.lost=False;self.page.locator('#video-generate').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  submits=[c for c in self.calls if c['path']=='/v1/videos'];self.assertEqual(len(submits),2);self.assertEqual(submits[0],submits[1]);self.assertEqual(self.errors,[])
 def test_05_queued_processing_failed_stop_then_explicit_resume(self):
  self.state='queued';self.open(True);self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('vid_offline · queued')")
  self.state='processing';self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('processing')")
  self.page.locator('.close-modal').click();polls=self.polls;self.page.wait_for_timeout(2000);self.assertEqual(self.polls,polls)
  self.state='failed';self.open(True);self.page.locator('#video-resume').click();self.page.wait_for_function("document.querySelector('#video-message').textContent.includes('Generation failed')");self.assertIn('settled $0.00',self.page.locator('#video-receipts').inner_text());self.assertEqual(self.page.locator('#video-player[src]').count(),0)
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1);self.assertEqual(self.errors,[])
 def test_06_close_during_submission_app_watcher_continues(self):
  self.open(True);self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  held=[]
  def hold(r):held.append(r)
  self.page.route('**/v1/videos',hold);self.page.locator('#video-generate').click()
  for _ in range(80):
   if held:break
   self.page.wait_for_timeout(50)
  self.assertEqual(len(held),1);self.page.locator('.close-modal').click();held[0].fulfill(status=202,json={'id':'vid_offline','status':'queued'});self.page.wait_for_timeout(300)
  self.assertGreater(self.polls,0,'app watcher must discover a create that completes after the view closes')
 def test_app_watcher_polls_past_three_minutes_and_continues_after_close(self):
  self.state='processing';self.open();self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.clock.install();self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('processing')")
  for _ in range(20):self.page.clock.run_for(15000);self.page.wait_for_timeout(25)
  self.assertGreater(self.polls,8)
  self.assertNotIn('deadline',self.page.locator('#video-message').inner_text())
  self.page.locator('.close-modal').click();polls=self.polls;self.page.clock.run_for(30000);self.page.wait_for_timeout(100);self.assertGreater(self.polls,polls)
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)

 def test_07_mobile_review_no_overflow(self):
  self.page.set_viewport_size({'width':390,'height':844});self.open();self.plan();self.assertLessEqual(self.page.locator('.modal').evaluate('e=>e.scrollWidth'),self.page.locator('.modal').evaluate('e=>e.clientWidth')+1);self.assertEqual(self.errors,[])

 def test_incomplete_download_offers_retry_only_not_regeneration(self):
  self.open(True);self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.route('**/v1/videos/vid_offline/content',lambda r:r.fulfill(body=b'bad',headers={'Content-Type':'video/mp4','Content-Length':'4'}))
  self.page.locator('#video-generate').click()
  self.page.wait_for_function("document.querySelector('#video-message').textContent==='Download incomplete, retry download'")
  self.assertTrue(self.page.locator('#video-new').is_disabled());self.assertTrue(self.page.locator('#video-generate').is_disabled())
  self.assertFalse(self.page.locator('#video-download-retry').is_hidden());self.assertEqual(self.page.locator('#video-player[src]').count(),0)
  self.page.unroute('**/v1/videos/vid_offline/content');self.page.locator('#video-download-retry').click();self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)

 def test_two_browser_tabs_simultaneous_generate_one_job_and_live_storage_refresh(self):
  import time
  pages=[self.page,self.ctx.new_page()];self.state='queued'
  for page in pages:
   self.page=page;self.open(True);self.plan();page.locator('#video-quote').click();page.wait_for_function("!document.querySelector('#video-generate').disabled")
  target=int(time.time()*1000)+500
  for page in pages:page.evaluate("target=>{setTimeout(()=>document.querySelector('#video-generate').click(),Math.max(0,target-Date.now()));}",target)
  for page in pages:
   page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('vid_offline · queued')")
   self.assertTrue(page.locator('#video-generate').is_disabled());self.assertTrue(page.locator('#video-new').is_disabled())
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1,'two simultaneous UI approvals must create one gateway job')
  self.state='completed'
  for page in pages:page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('vid_offline · completed')",timeout=15000)

 def test_two_real_tabs_use_shared_locks_and_saved_retry_token(self):
  pages=[self.page,self.ctx.new_page()]
  for page in pages:
   page.goto(self.url)
   page.evaluate('''async()=>{const {VideoSession}=await import('/js/video.js');window.session=new VideoSession({key:'offline-cross-tab',fields:{duration:'fixture_duration'}});window.spec={model:'alibaba/wan-3.0/text-to-video',duration:15,prompt:'Offline private boat'};}''')
  # Start both promises without awaiting either in Python; the actual browser
  # navigator.locks serializes the two distinct documents, not a fixture mutex.
  self.lost=True
  for page in pages:page.evaluate("()=>{window.run=session.create(spec,1.583334).then(()=>true,()=>false);}")
  for page in pages:page.evaluate('window.run')
  posts=[c for c in self.calls if c['path']=='/v1/videos'];self.assertEqual(len(posts),2);self.assertEqual(posts[0],posts[1])
  self.lost=False;pages[1].evaluate('session.create(spec,1.583334)')
  pages[0].evaluate("()=>{window.run=session.create(spec,1.583334).then(()=>true,()=>false);}")
  self.assertFalse(pages[0].evaluate('window.run'))
  posts=[c for c in self.calls if c['path']=='/v1/videos'];self.assertEqual(len(posts),3);self.assertTrue(all(p==posts[0] for p in posts))
  for page in pages:self.assertEqual(len(page.evaluate("JSON.parse(localStorage.getItem('motion-video.v1'))")),1)

 def test_history_selection_cannot_bypass_pending_job(self):
  self.state='queued';self.open(True)
  self.page.evaluate('''async()=>{const {VideoSession}=await import('/js/video.js');const s=new VideoSession({key:'offline-not-real-key',fields:{duration:'fixture_duration'}});await s.create({model:'alibaba/wan-3.0/text-to-video',duration:15,prompt:'Offline boat'},1.583334);const pending=structuredClone(s.record);const complete={...pending,token:'old-completed',id:'vid_old',status:'completed'};localStorage.setItem('motion-video.v1',JSON.stringify([complete,pending]));}''')
  self.open(True);self.page.locator('#video-history').select_option('0')
  self.assertTrue(self.page.locator('#video-new').is_disabled(),'all-history pending guard must disable new generation')
  self.assertTrue(self.page.locator('#video-generate').is_disabled())
  self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),1)

 def test_08_video_auth_credit_rejection_is_distinct_and_recoverable(self):
  for status,word in [(401,'Authentication'),(402,'credits')]:
   self.open(True);self.plan();self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled");self.video_status=status;self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('rejected')")
   self.page.wait_for_function("word=>document.querySelector('#video-message').textContent.includes(word)",arg=word);self.assertIn(word,self.page.locator('#video-message').inner_text());self.assertFalse(self.page.locator('#video-new').is_disabled());self.assertIn('settled $0.00',self.page.locator('#video-receipts').inner_text());self.assertEqual(self.page.locator('#video-player[src]').count(),0)
   self.page.locator('.close-modal').click();self.page.evaluate("localStorage.removeItem('motion-video.v1')")
  self.assertEqual(self.errors,[])
