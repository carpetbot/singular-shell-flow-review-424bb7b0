"""Checkpoint 1: real IDB + Chromium, server-denied offline gateway fixtures."""
from test_video_browser import VideoBrowser
import unittest

class Followups(VideoBrowser):
 def seed(self):
  self.state='processing'
  self.page.goto(self.url+'/#/settings');self.page.wait_for_selector('#apikey')
  self.page.evaluate("""async()=>{
   const key='offline-not-real-key',a=await(await import('/js/run-store.js')).openRunStore({key});
   localStorage.setItem('motion-video.v1',JSON.stringify([{token:'migrated',planId:'version',bodyHash:'body',keyHash:a.account_id,id:'vid_offline',status:'processing',quote:{model:'fixture-model',price:1},settled:null}]));a.close();
   window.notices=[];new MutationObserver(ms=>{for(const m of ms)for(const n of m.addedNodes)if(n.nodeType===1&&n.matches('[data-video-ready]'))notices.push(n.dataset.videoReady);}).observe(document.querySelector('#toasts'),{childList:true});
   const s=await import('/js/store.js');s.setSettings({apiKey:key});s.touch();
  }""")
  self.page.wait_for_function("document.documentElement.dataset.videoRendering==='true'")
 def rows(self):
  return self.page.evaluate("async()=>{const a=await(await import('/js/run-store.js')).openRunStore({key:'offline-not-real-key'});try{return await a.list();}finally{a.close();}}")
 def finish_legacy(self):
  # A real frozen engine in a second document; no app runtime/second notifier.
  self.state='completed';legacy=self.ctx.new_page();legacy.goto(self.url+'/js/video.js')
  status=legacy.evaluate("""async()=>{const {VideoSession}=await import('/js/video.js');const s=new VideoSession({key:'offline-not-real-key'});try{await s.resume();return s.record.status;}finally{s.dispose();}}""")
  self.assertEqual(status,'completed');legacy.close()

 def test_migrated_legacy_completion_import_announces_once(self):
  self.seed();self.page.wait_for_timeout(500)
  # Legacy engine can finish in another tab; durable watch imports it before its
  # own poll returns. Stop that response so only migration observes completion.
  self.page.route('**/v1/videos/vid_offline',lambda r:r.abort())
  self.finish_legacy()
  self.page.wait_for_function("async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();return (await c.store.list()).some(r=>r.status==='done');}",timeout=15000)
  self.page.wait_for_function('notices.length===1',timeout=7000)
  self.assertEqual(self.page.evaluate('notices'),['vid_offline'])

 def test_work_migration_completion_updates_without_refresh(self):
  self.seed();self.page.evaluate("location.hash='#/work'");self.page.wait_for_selector('.work-card')
  self.assertEqual(self.page.locator('.work-status').inner_text(),'Rendering')
  self.page.route('**/v1/videos/vid_offline',lambda r:r.abort())
  self.finish_legacy()
  self.page.wait_for_function("document.querySelector('.work-status')?.textContent==='Ready'",timeout=15000)
  self.assertFalse(any('/content' in c['path'] for c in self.calls))

 def test_cross_tab_work_updates_preserve_selected_media_and_prompt(self):
  self.seed();self.page.wait_for_timeout(500)
  self.ctx.route('**/v1/videos?*',lambda r:r.fulfill(json={'items':[{'id':'vid_offline','status':'processing','params':{'prompt':'Gateway saved boat prompt'}}],'next_cursor':None}))
  other=self.ctx.new_page();other.set_default_timeout(4000)
  nonowner_polls=[]
  def nonowner_poll(r):
   nonowner_polls.append(r.request.url);self.route(r)
  other.route('**/v1/videos/vid_offline',nonowner_poll)
  other.goto(self.url+'/#/work');other.wait_for_selector('.work-card')
  other.evaluate("""async()=>{
   const c=await(await import('/js/video-runtime.js')).videoContext();
   const rows=await c.store.list();await c.store.update(rows[0].id,{outputs:{...rows[0].outputs,fixture:true}});
  }""")
  self.state='completed'
  other.wait_for_function("document.querySelector('.work-status')?.textContent==='Ready'",timeout=15000)
  self.assertEqual(sum(p.locator('[data-video-ready]').count() for p in [self.page,other]),1)
  other.get_by_role('button',name='Open video vid_offline',exact=True).click();other.wait_for_selector('#work-player');other.wait_for_selector('.work-poster')
  before=len([c for c in self.calls if '/content' in c['path']])
  other.evaluate("()=>{window.selected=document.querySelector('#work-player');window.src=selected.src;window.poster=document.querySelector('.work-poster').src;}")
  # Late stale legacy state must not reverse terminal truth or replace the player.
  self.page.evaluate("()=>{const rows=JSON.parse(localStorage.getItem('motion-video.v1'));rows[0].status='processing';rows[0].settled=null;localStorage.setItem('motion-video.v1',JSON.stringify(rows));}")
  other.wait_for_timeout(5500)
  self.assertTrue(other.evaluate("selected===document.querySelector('#work-player')&&src===selected.src&&poster===document.querySelector('.work-poster').src"))
  self.assertEqual(other.locator('.work-status').inner_text(),'Ready')
  self.assertIn('Gateway saved boat prompt',other.locator('.work-card').inner_text())
  self.assertEqual(len([c for c in self.calls if '/content' in c['path']]),before)
  self.assertEqual(nonowner_polls,[],'card refresh must not require polling ownership')
  self.assertLessEqual(self.page.locator('[data-video-ready]').count()+other.locator('[data-video-ready]').count(),1)

 def test_same_tab_watcher_completion_updates_local_prompt_without_refresh(self):
  self.state='processing';self.open();self.plan()
  self.page.evaluate("async()=>{const s=await import('/js/store.js');s.setSettings({apiKey:'offline-not-real-key'});s.touch();}")
  self.page.locator('#video-quote').click();self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.locator('#video-generate').click();self.page.wait_for_function("document.querySelector('#video-receipts').textContent.includes('processing')")
  self.page.locator('.close-modal').click();self.page.evaluate("location.hash='#/work'");self.page.wait_for_selector('.work-card')
  self.assertEqual(self.page.locator('.work-status').inner_text(),'Rendering')
  self.state='completed'
  self.page.wait_for_function("document.querySelector('.work-status')?.textContent==='Ready'",timeout=15000)
  self.assertIn('A paper boat drifts on a calm pond.',self.page.locator('.work-card').inner_text())
  self.assertFalse(any('/content' in c['path'] for c in self.calls))
  self.assertEqual(self.errors,[])

 def test_foreign_notice_does_not_cancel_valid_pending_read(self):
  self.seed();self.page.evaluate("location.hash='#/work'");self.page.wait_for_selector('.work-card')
  self.page.route('**/v1/videos/vid_offline',lambda r:r.abort())
  self.page.evaluate("""async()=>{
   const c=await(await import('/js/video-runtime.js')).videoContext(),row=(await c.store.list())[0];await c.store.update(row.id,{status:'done',video_status:'completed'});
   const list=c.store.list;c.store.list=async()=>{c.store.list=list;const rows=await list();window.waiting=true;await new Promise(r=>window.releaseRead=r);return rows;};
   window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));
  }""")
  self.page.wait_for_function('window.waiting===true')
  self.page.evaluate("()=>{window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:'foreign'}}));}")
  self.page.wait_for_timeout(50);self.page.evaluate('releaseRead()');self.page.wait_for_timeout(150)
  self.assertEqual(self.page.locator('.work-status').inner_text(),'Ready')

 def test_account_change_rejects_queued_read_and_foreign_notification(self):
  self.seed();self.page.evaluate("location.hash='#/work'");self.page.wait_for_selector('.work-card')
  self.page.evaluate("""async()=>{
   const c=await(await import('/js/video-runtime.js')).videoContext();window.oldAccount=c.store.account_id;
   const list=c.store.list;c.store.list=async()=>{c.store.list=list;const rows=await list();window.readWaiting=true;await new Promise(r=>window.releaseRead=r);return rows;};
   window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:oldAccount}}));
  }""")
  self.page.wait_for_function('window.readWaiting===true')
  self.page.evaluate("""async()=>{const s=await import('/js/store.js');s.setSettings({apiKey:'offline-other-account'});releaseRead();}""")
  self.page.wait_for_timeout(500)
  self.assertEqual(self.page.locator('.work-card').count(),0)
  result=self.page.evaluate("""async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();let reads=0;const list=c.store.list;c.store.list=async()=>{reads++;return list();};window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:oldAccount}}));await new Promise(r=>setTimeout(r,50));c.store.list=list;return reads;}""")
  self.assertEqual(result,0)
  self.assertEqual(self.page.locator('[data-video-ready]').count(),0)
  self.assertEqual(self.errors,[])

 def test_route_leave_removes_notification_listener(self):
  self.page.add_init_script("""(()=>{const add=window.addEventListener,remove=window.removeEventListener;window.runListeners=new Set();window.addEventListener=function(type,fn,...args){if(type==='singular:runs')runListeners.add(fn);return add.call(this,type,fn,...args);};window.removeEventListener=function(type,fn,...args){if(type==='singular:runs')runListeners.delete(fn);return remove.call(this,type,fn,...args);};})();""")
  self.seed();self.page.evaluate("location.hash='#/work'");self.page.wait_for_selector('.work-card')
  self.assertEqual(self.page.evaluate('runListeners.size'),1)
  self.page.evaluate("location.hash='#/settings'");self.page.wait_for_selector('#apikey')
  self.assertEqual(self.page.evaluate('runListeners.size'),0)
  self.state='completed';self.page.wait_for_selector('[data-video-ready]',timeout=15000)
  self.assertEqual(self.page.locator('#work-list').count(),0)
  self.page.locator('[data-video-ready] button').click();self.page.wait_for_selector('#work-player')
  self.assertEqual(self.page.evaluate('runListeners.size'),1)
  self.assertEqual(self.errors,[])

 def test_ready_claim_is_atomic_account_scoped_and_survives_reopen(self):
  self.seed()
  self.page.route('**/v1/videos/vid_offline',lambda r:r.abort())
  result=self.page.evaluate("""async()=>{
   const {openRunStore}=await import('/js/run-store.js');
   const a=await openRunStore({key:'offline-not-real-key'}),b=await openRunStore({key:'offline-not-real-key'}),other=await openRunStore({key:'offline-other-account'});
   const row=(await a.list())[0];const premature=await a.claimVideoReady(row.video_job_id);
   await a.create({flow_id:'fixture-planner',status:'done'});const noJob=await a.claimVideoReady(null);
   await a.update(row.id,{status:'done',video_status:'completed'});
   const claims=await Promise.all([a.claimVideoReady(row.video_job_id),b.claimVideoReady(row.video_job_id)]);
   const hidden=await other.claimVideoReady(row.video_job_id);
   await other.create({flow_id:'fixture',video_job_id:row.video_job_id,status:'done'});
   const separate=await other.claimVideoReady(row.video_job_id);a.close();b.close();other.close();
   const reopened=await openRunStore({key:'offline-not-real-key'});const repeated=await reopened.claimVideoReady(row.video_job_id);reopened.close();return {noJob,premature,claims,hidden,separate,repeated};
  }""")
  self.assertFalse(result['noJob'])
  self.assertEqual(sorted(result['claims']),[False,True]);self.assertFalse(result['premature']);self.assertFalse(result['hidden']);self.assertTrue(result['separate']);self.assertFalse(result['repeated'])

 def test_migrated_completion_notice(self):
  self.seed();self.page.wait_for_timeout(300);self.state='completed'
  self.page.wait_for_function("async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();return (await c.store.list()).some(r=>r.status==='done');}",timeout=15000)
  self.page.wait_for_function("notices.length===1",timeout=15000)
  self.assertEqual(self.page.evaluate('notices'),['vid_offline'])
  self.page.locator('[data-video-ready] button').click();self.page.wait_for_selector('#work-player[src^="blob:"]')
  self.page.reload();self.page.wait_for_selector('#work-list');self.page.wait_for_timeout(5500)
  self.assertEqual(self.page.locator('[data-video-ready]').count(),0)
  self.assertFalse(any(c['path']=='/v1/videos' for c in self.calls))
  self.assertEqual(self.errors,[])

for name in list(vars(VideoBrowser)):
 if name.startswith('test_') and name not in vars(Followups):setattr(Followups,name,None)
del VideoBrowser
if __name__=='__main__':unittest.main()
