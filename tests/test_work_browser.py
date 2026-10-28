"""A1 Chromium acceptance; synthetic list and MP4, all public traffic blocked."""
import http.server, importlib.util, json, os, threading, unittest
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
APP=Path(os.environ.get('VIDEO_APP_ROOT',str(ROOT)))

class WorkBrowser(unittest.TestCase):
 def setUp(self):
  spec=importlib.util.spec_from_file_location('work_proxy',APP/'proxy.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),p.Handler);threading.Thread(target=self.server.serve_forever,daemon=True).start()
  self.pw=sync_playwright().start();self.browser=self.pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  self.ctx=self.browser.new_context(accept_downloads=True,viewport={'width':390,'height':844});self.ctx.route('**/*',self.route)
  self.page=self.ctx.new_page();self.page.set_default_timeout(5000);self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.calls=[];self.mode='normal';self.url='http://127.0.0.1:'+str(self.server.server_port)
 def tearDown(self):
  self.browser.close();self.pw.stop();self.server.shutdown();self.server.server_close()
 def route(self,r):
  u=urlsplit(r.request.url)
  if u.path=='/pricing.json':r.fulfill(json={'models':[]})
  elif u.path=='/v1/videos':
   self.calls.append((u.path,u.query,r.request.headers.get('authorization')))
   if self.mode=='error':r.fulfill(status=401,json={'error_message':'private diagnostic'});return
   if self.mode=='empty':r.fulfill(json={'items':[],'next_cursor':None});return
   if parse_qs(u.query).get('cursor'):r.fulfill(json={'items':[{'id':'vid_second','status':'processing','model':'fixture-model'}],'next_cursor':None})
   else:r.fulfill(json={'items':[{'id':'vid_first','status':'completed','model':'fixture-model','created_at':1700000000,'params':{'prompt':'<img src=x onerror=alert(1)> Offline boat'},'result_url':'https://untrusted.invalid/secret'}],'next_cursor':'page_2='})
  elif u.path.endswith('/content'):
   self.calls.append((u.path,u.query,r.request.headers.get('authorization')))
   r.fulfill(body=(ROOT/'tests/fixtures/offline-video.mp4').read_bytes(),content_type='video/mp4')
  elif u.hostname=='127.0.0.1':r.continue_()
  else:r.abort()
 def open(self):
  self.page.goto(self.url+'/#/skills');self.page.wait_for_selector('.skill-card')
  self.page.evaluate("async()=>{const s=await import('/js/store.js');s.setSettings({apiKey:'offline-work-fixture'});}")
  self.page.locator('#tabbar a[href="#/work"]').click()
 def test_empty_error_retry_and_disconnect(self):
  self.mode='empty';self.open();self.page.get_by_text('No video jobs found for this key.',exact=True).wait_for()
  self.mode='error';self.page.get_by_role('button',name='Refresh videos').click();self.page.get_by_text('Key not accepted. Check Settings and retry.',exact=True).wait_for()
  self.assertNotIn('private diagnostic',self.page.locator('#view').inner_text())
  self.mode='normal';self.page.get_by_role('button',name='Refresh videos').click();self.page.get_by_text('vid_first',exact=True).wait_for()
  self.page.evaluate("async()=>{const s=await import('/js/store.js');s.setSettings({apiKey:''});}")
  self.page.get_by_text('Connect your Singular key in Settings to recover videos.',exact=True).wait_for()
  self.assertEqual(self.page.locator('.work-card').count(),0)
 def test_account_change_revokes_media_ignores_stale_list_and_media(self):
  self.open();self.page.get_by_text('vid_first',exact=True).wait_for()
  self.page.get_by_role('button',name='Open video vid_first').click();self.page.wait_for_selector('#work-player[src^="blob:"]')
  self.page.evaluate('''()=>{window.revoked=[];const revoke=URL.revokeObjectURL.bind(URL);URL.revokeObjectURL=u=>{window.revoked.push(u);revoke(u);};window.nativeFetch=fetch;window.pending=[];window.fetch=(url,opts)=>String(url).startsWith('/v1/videos')?new Promise(resolve=>window.pending.push({url,resolve})):window.nativeFetch(url,opts);}''')
  self.page.get_by_role('button',name='Open video vid_first').click();self.page.wait_for_function('window.pending.length===1')
  self.page.get_by_role('button',name='Refresh videos').click();self.page.wait_for_function('window.pending.length===2')
  self.page.evaluate("async()=>{const s=await import('/js/store.js');s.setSettings({apiKey:'offline-new-account'});}")
  self.page.wait_for_function('window.pending.length===3')
  self.assertEqual(self.page.locator('.work-card').count(),0);self.assertEqual(self.page.locator('#work-player').count(),0)
  self.page.evaluate('''()=>{window.pending[2].resolve(Response.json({items:[{id:'vid_new',status:'queued'}],next_cursor:null}));window.pending[1].resolve(Response.json({items:[{id:'vid_stale',status:'completed'}],next_cursor:null}));window.pending[0].resolve(new Response(new Uint8Array([1,2]),{headers:{'Content-Type':'video/mp4'}}));}''')
  self.page.get_by_text('vid_new',exact=True).wait_for();self.assertEqual(self.page.locator('#work-player').count(),0);self.assertNotIn('vid_stale',self.page.locator('#view').inner_text())
  self.assertEqual(self.page.evaluate('window.revoked.length'),1)
  self.page.locator('#tabbar a[href="#/settings"]').click();self.assertEqual(self.page.locator('#work-list').count(),0)
 def test_cross_tab_account_change_clears_immediately(self):
  self.open();self.page.get_by_text('vid_first',exact=True).wait_for()
  self.page.evaluate('''()=>{const entry=Object.entries(localStorage).find(([k,v])=>{try{return JSON.parse(v).settings?.apiKey==='offline-work-fixture';}catch{return false;}});const data=JSON.parse(entry[1]);data.settings.apiKey='';localStorage.setItem(entry[0],JSON.stringify(data));window.dispatchEvent(new StorageEvent('storage',{key:entry[0],newValue:JSON.stringify(data)}));}''')
  self.assertEqual(self.page.locator('.work-card').count(),0,'old account must disappear synchronously on account notification')
  self.page.get_by_text('Connect your Singular key in Settings to recover videos.',exact=True).wait_for()
 def test_list_pagination_playback_download_mobile(self):
  self.open();self.page.get_by_role('heading',name='My work',exact=True).wait_for()
  self.page.get_by_text('vid_first',exact=True).wait_for()
  self.assertEqual(len(self.calls),1);self.assertEqual(self.calls[0][2],'Bearer offline-work-fixture')
  self.assertEqual(self.page.locator('#work-list img').count(),0)
  self.page.get_by_role('button',name='Load more',exact=True).click();self.page.get_by_text('vid_second',exact=True).wait_for()
  self.assertIn('cursor=page_2%3D',self.calls[1][1]);self.assertEqual(len(self.calls),2)
  self.page.get_by_role('button',name='Open video vid_first',exact=True).click()
  self.page.wait_for_selector('#work-player[src^="blob:"]');self.page.wait_for_function("document.querySelector('#work-player').readyState>=1")
  self.page.locator('#work-player').evaluate('async e=>{e.muted=true;await e.play();}')
  self.page.wait_for_function("document.querySelector('#work-player').currentTime>0.1");self.page.locator('#work-player').evaluate('e=>e.pause()')
  self.assertEqual(self.calls[-1][0],'/v1/videos/vid_first/content');self.assertEqual(self.calls[-1][2],'Bearer offline-work-fixture')
  with self.page.expect_download() as d:self.page.get_by_role('link',name='Download MP4',exact=True).click()
  self.assertEqual(Path(d.value.path()).read_bytes(),(ROOT/'tests/fixtures/offline-video.mp4').read_bytes())
  self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  evidence=ROOT/'reports/a1';evidence.mkdir(parents=True,exist_ok=True);self.page.screenshot(path=str(evidence/'work-mobile-offline.png'))
  self.assertEqual(self.errors,[])
