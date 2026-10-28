"""A2 final cards: real offline Chromium and account-scoped poster persistence."""
from test_work_browser import WorkBrowser
import unittest

class WorkCards(WorkBrowser):
 def test_prompt_titles_plain_statuses_and_safe_truncation(self):
  prompt='  \n  <img src=x onerror=alert(1)> '+('boat '*60)+'\nNot the title'
  self.ctx.route('**/v1/videos?*',lambda r:r.fulfill(json={'items':[
   {'id':'vid_title','status':'completed','params':{'prompt':prompt}},
   {'id':'vid_render','status':'processing','created_at':1700000000},
   {'id':'vid_failed','status':'rejected','params':{'prompt':' \n '}},
   {'id':'vid_unknown','status':{}},
  ],'next_cursor':None}))
  self.open();self.page.get_by_text('4 video jobs loaded.',exact=True).wait_for()
  cards=self.page.locator('.work-card');title=cards.nth(0).locator('h2')
  self.assertEqual(title.inner_text(),prompt.splitlines()[1].strip()[:119]+'…')
  self.assertNotIn('vid_title',cards.nth(0).inner_text())
  self.assertEqual(self.page.locator('#work-list img').count(),0)
  self.assertEqual(self.page.locator('.work-status').all_inner_texts(),['Ready','Rendering','Failed','Rendering'])
  self.assertTrue(cards.nth(1).locator('h2').inner_text().startswith('Video from '))
  self.assertEqual(cards.nth(2).locator('h2').inner_text(),'Video')
  self.assertEqual(cards.nth(3).locator('h2').inner_text(),'Video')
  self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  self.assertEqual(self.errors,[])

 def test_presented_frame_before_loadeddata_still_caches_poster(self):
  self.open();self.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
  self.page.evaluate("""()=>{const frame=HTMLVideoElement.prototype.requestVideoFrameCallback;
   HTMLVideoElement.prototype.requestVideoFrameCallback=function(cb){return frame.call(this,(...args)=>{
    Object.defineProperty(this,'readyState',{configurable:true,value:1});
    try{cb(...args);}finally{delete this.readyState;queueMicrotask(()=>this.dispatchEvent(new Event('loadeddata')));}
   });};
  }""")
  self.page.get_by_role('button',name='Open video vid_first').click();self.page.wait_for_selector('.work-poster')
  self.assertEqual(self.errors,[])

 def test_canvas_security_failure_leaves_video_and_download_usable(self):
  self.open();self.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
  self.page.evaluate("()=>{HTMLCanvasElement.prototype.toDataURL=function(){window.captureAttempted=true;throw new DOMException('fixture taint','SecurityError');};}")
  self.page.get_by_role('button',name='Open video vid_first').click()
  self.page.wait_for_function('window.captureAttempted===true')
  self.assertEqual(self.page.locator('.work-poster').count(),0)
  self.page.locator('#work-player').evaluate('async e=>{e.muted=true;await e.play();}')
  self.page.wait_for_function("document.querySelector('#work-player').currentTime>0.1")
  with self.page.expect_download() as d:self.page.get_by_role('link',name='Download MP4',exact=True).click()
  self.assertTrue(d.value.path());self.assertEqual(self.errors,[])

 def test_failed_decode_keeps_normal_video_without_invented_poster(self):
  self.ctx.route('**/content',lambda r:r.fulfill(body=b'not a video',content_type='video/mp4'))
  self.open();self.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
  self.page.get_by_role('button',name='Open video vid_first').click()
  self.page.wait_for_function("document.querySelector('#work-player')?.error!=null")
  self.assertEqual(self.page.locator('.work-poster').count(),0)
  self.assertTrue(self.page.get_by_role('link',name='Download MP4',exact=True).is_visible())
  self.assertEqual(self.errors,[])

 def test_real_poster_cache_bounds_eviction_and_validation(self):
  self.open();self.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
  result=self.page.evaluate("""async()=>{
   const m=await import('/js/poster-cache.js');const a='a'.repeat(64),b='b'.repeat(64);
   const image='data:image/jpeg;base64,'+'A'.repeat(100000);
   for(let i=0;i<25;i++)await m.savePoster(a,'vid_'+String(i).padStart(3,'0'),image);
   const saved=await m.readPosters(a);const other=await m.readPosters(b);let rejected=0;
   for(const args of [[a,'vid_bad','https://untrusted.invalid'],[a,'vid_bad','data:image/jpeg;base64,'+'A'.repeat(m.MAX_POSTER_BYTES)],['raw-key','vid_bad',image]]){
    try{await m.savePoster(...args);}catch{rejected++;}
   }
   // Replacing an entry does not consume a second slot, newest content survives.
   await m.savePoster(a,'vid_024',image);const replaced=await m.readPosters(a);
   return {count:saved.size,bytes:[...saved.values()].reduce((n,s)=>n+s.length,0),max:m.MAX_CACHE_BYTES,first:saved.has('vid_000'),last:saved.has('vid_024'),other:other.size,rejected,replaced:replaced.size};
  }""")
  self.assertLess(result['count'],25);self.assertLessEqual(result['bytes'],result['max'])
  self.assertFalse(result['first']);self.assertTrue(result['last']);self.assertEqual(result['other'],0)
  self.assertEqual(result['rejected'],3);self.assertEqual(result['replaced'],result['count'])

 def test_server_fixture_blocks_upstream_even_without_browser_routes(self):
  import http.client
  from unittest.mock import patch
  with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')) as upstream:
   c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
   c.request('GET','/pricing.json',headers={'Authorization':'Bearer offline-private-value'})
   r=c.getresponse();body=r.read();c.close()
   self.assertEqual(r.status,503)
   self.assertEqual(body,b'{"error":"offline fixture: unhandled gateway request"}')
   upstream.assert_not_called()
  self.assertEqual(self.server.unexpected_upstream,[('GET','/pricing.json')])
  self.server.unexpected_upstream.clear() # This one request is intentional.

 def test_poster_only_after_open_persists_and_is_account_scoped(self):
  self.open();self.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
  self.assertEqual(self.page.locator('.work-poster').count(),0)
  self.assertFalse(any('/content' in c[0] for c in self.calls))
  self.page.evaluate("""()=>{const src=Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype,'src'),frame=HTMLVideoElement.prototype.requestVideoFrameCallback;
   HTMLVideoElement.prototype.requestVideoFrameCallback=function(cb){this.posterFrameRegistered=true;return frame.call(this,cb);};
   Object.defineProperty(HTMLMediaElement.prototype,'src',{...src,set(value){window.posterRegistrationBeforeSource=this.posterFrameRegistered===true;src.set.call(this,value);}});
  }""")
  self.page.get_by_role('button',name='Open video vid_first').click()
  self.page.wait_for_selector('#work-player')
  self.assertTrue(self.page.evaluate('window.posterRegistrationBeforeSource'),'register before src so a fast paused first frame cannot be missed')
  self.page.wait_for_selector('.work-poster')
  self.assertTrue(self.page.locator('.work-poster').get_attribute('src').startswith('data:image/jpeg;base64,'))
  pixel=self.page.locator('.work-poster').evaluate("async img=>{await img.decode();const c=document.createElement('canvas');c.width=320;c.height=180;const ctx=c.getContext('2d');ctx.drawImage(img,0,0);return [...ctx.getImageData(10,10,1,1).data];}")
  self.assertGreater(pixel[2],80,'poster must contain the decoded blue fixture frame, not an unpainted black surface')
  before=len([c for c in self.calls if '/content' in c[0]])
  self.page.reload();self.page.wait_for_selector('.work-poster')
  self.assertEqual(len([c for c in self.calls if '/content' in c[0]]),before)
  self.assertEqual(self.page.locator('#work-player').count(),0)
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-poster-other-account'});}")
  self.assertEqual(self.page.locator('.work-poster').count(),0)
  self.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
  self.page.reload();self.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
  self.assertEqual(self.page.locator('.work-poster').count(),0)
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-work-fixture'});}")
  self.page.wait_for_selector('.work-poster')
  raw=self.page.evaluate("""async()=>{const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('singular-posters.v1');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});try{return await new Promise(resolve=>{const r=db.transaction('posters').objectStore('posters').getAll();r.onsuccess=()=>resolve(JSON.stringify(r.result));});}finally{db.close();}}""")
  self.assertNotIn('offline-work-fixture',raw);self.assertNotIn('offline-poster-other-account',raw)
  self.assertEqual(self.errors,[])

for name in list(vars(WorkBrowser)):
 if name.startswith('test_') and name not in vars(WorkCards):setattr(WorkCards,name,None)
del WorkBrowser
if __name__=='__main__':unittest.main()
