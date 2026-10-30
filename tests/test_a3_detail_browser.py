"""A3 c3: OFFLINE FIXTURE, real Chromium/IDB; server denies upstream."""
import json
import unittest
from pathlib import Path
from test_video_browser import VideoBrowser, ROOT

EVIDENCE=ROOT/'reports/a3/c3-detail'

class Detail(VideoBrowser):
 def setUp(self):
  super().setUp()
  # Parent owns production static allowlist. Only these new static modules are
  # served here, from actual disk, never a fabricated implementation response.
  def module(r):
   file=ROOT/'js'/r.request.url.rsplit('/',1)[-1]
   if file.exists():r.fulfill(body=file.read_bytes(),content_type='text/javascript')
   else:r.fulfill(status=404,body='Missing implementation')
  self.ctx.route('**/js/media-cache.js',module)
  self.ctx.route('**/js/views/work-detail.js',lambda r:r.fulfill(body=(ROOT/'js/views/work-detail.js').read_bytes(),content_type='text/javascript') if (ROOT/'js/views/work-detail.js').exists() else r.fulfill(status=404,body='Missing implementation'))
  self.page.goto(self.url+'/#/settings');self.page.wait_for_selector('#apikey')
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-not-real-key'});}")
  self.ids=self.page.evaluate("""async()=>{
   const c=await(await import('/js/video-runtime.js')).videoContext();
   const a=await c.store.create({flow_id:'claw__motion-trimmer-video',title:'OFFLINE FIXTURE boat',prompt:'Recorded blue boat prompt',status:'done',video_status:'completed',video_job_id:'vid_offline',inputs:{topic:'Fixture boat',duration:5},model_ids:['fixture/video'],cost:0.53,receipts:[{model:'fixture/planner',tokens:80,cost:0.001,fallback:false}],created_at:'2026-10-27T12:00:00Z'});
   const b=await c.store.create({flow_id:'impossibuild__prospect-to-cold-email',title:'OFFLINE FIXTURE email',prompt:'Find lighthouse',status:'done',outputs:{text:'Full fixture email <script>not markup</script>'},created_at:'2026-10-26T12:00:00Z'});
   return [a.id,b.id];
  }""")
 def mount(self,which='work-detail',identity=None):
  self.page.evaluate("""async({which,id})=>{
   window.c3module?.destroy();const m=await import('/js/views/'+which+'.js');
   window.c3module=m;let host=document.querySelector('#c3-host');if(!host){host=document.createElement('main');host.id='c3-host';document.body.append(host);}
   if(id)history.replaceState(null,'','#/work/'+encodeURIComponent(id));host.innerHTML=m.view();m.bind(host);
  }""",{'which':which,'id':identity})
 def media_count(self):return len([c for c in self.calls if '/content' in c['path']])
 def test_detail_durable_identity_output_actions_and_cache_reuse(self):
  self.mount(identity=self.ids[0]);self.page.wait_for_selector('#work-player[src^="blob:"]')
  self.assertIn('Recorded blue boat prompt',self.page.locator('#work-detail').inner_text())
  self.assertEqual(self.media_count(),1)
  with self.page.expect_download() as d:self.page.get_by_role('link',name='Download MP4',exact=True).click()
  self.assertEqual(Path(d.value.path()).read_bytes(),(ROOT/'tests/fixtures/offline-video.mp4').read_bytes())
  self.assertTrue(self.page.locator('#detail-receipts').is_hidden())
  self.page.evaluate("document.documentElement.dataset.mode='pro'")
  self.assertIn('fixture/planner',self.page.locator('#detail-receipts').inner_text())
  self.page.evaluate("window.addEventListener('singular:run-again',e=>window.capturedPrefill=e.detail,{once:true})")
  self.page.get_by_role('button',name='Run again with changes',exact=True).click()
  payload=self.page.evaluate('window.capturedPrefill')
  self.assertEqual(payload['inputs'],{'topic':'Fixture boat'})
  self.assertEqual(payload['flow_id'],'claw__motion-trimmer-video')
  self.page.wait_for_function("document.querySelector('#video-topic')?.value==='Fixture boat'")
  self.assertIsNone(self.page.evaluate("sessionStorage.getItem('singular:run-again.v1')"))
  self.mount(identity=self.ids[0]);self.page.wait_for_selector('#work-player[src^="blob:"]');self.assertEqual(self.media_count(),1)
  self.assertEqual(self.errors,[])
 def test_group_filters_search_and_canonical_links_no_prefetch(self):
  self.mount('work');self.page.wait_for_selector('.work-card')
  self.page.wait_for_function("document.querySelector('#work-status').textContent.includes('loaded')")
  self.assertEqual(self.page.locator('#work-status').inner_text(),'2 runs loaded.')
  self.assertEqual(self.page.locator('#c3-host .work-card').count(),2)
  self.assertEqual(self.page.locator('#c3-host .work-day').count(),2)
  self.assertEqual(self.media_count(),0)
  self.assertEqual(self.page.locator('#c3-host .work-card a').first.get_attribute('href'),'#/work/'+self.ids[0])
  self.page.locator('#work-filter').select_option('Emails');self.assertEqual(self.page.locator('#c3-host .work-card').count(),1)
  self.page.locator('#work-search').fill('lighthouse');self.assertEqual(self.page.locator('#c3-host .work-card').count(),1)
  self.page.locator('#work-search').fill('no such prompt');self.assertEqual(self.page.locator('#c3-host .work-card').count(),0)
  self.assertIn('Email and comparison capture comes next.',self.page.locator('#c3-host').inner_text())
  self.page.locator('#work-search').fill('');self.page.locator('#work-filter').select_option('All')
  self.page.evaluate("""async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();await c.store.create({flow_id:'impossibuild__model-jury',status:'done',title:'Live fixture comparison'});window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));}""")
  self.page.wait_for_function("document.querySelectorAll('#c3-host .work-card').length===3")
  self.assertEqual(self.page.locator('#work-status').inner_text(),'3 runs loaded.')
 def test_media_cache_global_byte_bound_and_account_isolation(self):
  self.mount(identity=self.ids[1]);self.page.wait_for_selector('#detail-output')
  result=self.page.evaluate("""async()=>{
   const m=await import('/js/media-cache.js'),a='a'.repeat(64),b='b'.repeat(64),blob=new Blob([new Uint8Array(m.MAX_CACHE_BYTES/2+1)],{type:'video/mp4'});
   await m.saveMedia(a,'first',blob);await m.saveMedia(b,'second',blob);
   const old=await m.readMedia(a,'first'),hidden=await m.readMedia(a,'second'),own=await m.readMedia(b,'second');
   return {evicted:old===null,hidden:hidden===null,size:own?.size,limit:m.MAX_CACHE_BYTES};
  }""")
  self.assertTrue(result['evicted']);self.assertTrue(result['hidden']);self.assertLessEqual(result['size'],result['limit'])
  self.assertIn('Full fixture email <script>not markup</script>',self.page.locator('#detail-output').inner_text())
  self.assertEqual(self.page.locator('#detail-output script').count(),0)

 def test_gateway_namespace_recorded_prompt_and_missing_metadata_are_honest(self):
  self.ctx.route('**/v1/videos/vid_offline',lambda r:r.fulfill(json={'id':'vid_offline','status':'completed','model':'fixture/gateway','params':{}}))
  self.ctx.route('**/v1/videos/other_device',lambda r:r.fulfill(json={'id':'other_device','status':'processing','params':{'prompt':'Actual gateway params prompt'}}))
  self.mount(identity='vid_offline');self.page.wait_for_function("document.querySelector('#detail-status').textContent.includes('Run not found')")
  self.assertEqual(self.media_count(),0)
  self.mount(identity='gateway:vid_offline');self.page.wait_for_selector('#work-player')
  self.assertIn('Prompt saved on another device',self.page.locator('#detail-body').inner_text())
  self.assertTrue(self.page.get_by_role('button',name='Run again with changes',exact=True).is_disabled())
  self.assertEqual(self.page.get_by_role('button',name='Copy prompt',exact=True).count(),0)
  self.mount(identity='gateway:other_device');self.page.wait_for_function("document.querySelector('#detail-body')?.textContent.includes('Actual gateway params prompt')")
  self.assertIn('still rendering',self.page.locator('#detail-output').inner_text())
  self.assertEqual(self.page.locator('#work-player').count(),0)
 def test_account_change_aborts_delayed_media_and_rejects_completion(self):
  pending=[];self.ctx.route('**/v1/videos/vid_offline/content',lambda r:pending.append(r))
  self.mount(identity=self.ids[0]);self.page.wait_for_function("document.querySelector('#detail-output')?.textContent.includes('Loading video')")
  self.page.wait_for_timeout(150)
  self.assertEqual(len(pending),1)
  self.page.evaluate("async()=>{(await import('/js/store.js')).setSettings({apiKey:'offline-other-account'});}")
  self.assertEqual(self.page.locator('#detail-body').inner_text(),'')
  pending[0].fulfill(body=(ROOT/'tests/fixtures/offline-video.mp4').read_bytes(),content_type='video/mp4')
  self.page.wait_for_function("document.querySelector('#detail-status').textContent.includes('Run not found')")
  self.assertEqual(self.page.locator('#work-player').count(),0)
  self.assertNotIn('Recorded blue boat prompt',self.page.locator('#detail-body').inner_text())
 def test_cross_tab_settings_removal_revokes_player_and_listener_cleanup(self):
  self.page.add_script_tag(content="window.revoked=[];const revoke=URL.revokeObjectURL;URL.revokeObjectURL=u=>{revoked.push(u);revoke(u)}")
  self.mount(identity=self.ids[0]);self.page.wait_for_selector('#work-player')
  src=self.page.locator('#work-player').get_attribute('src')
  other=self.ctx.new_page();other.goto(self.url+'/js/store.js');other.evaluate('localStorage.clear()')
  self.page.wait_for_function("!document.querySelector('#work-player')")
  self.assertIn(src,self.page.evaluate('revoked'))
  self.page.wait_for_function("document.querySelector('#detail-status').textContent.includes('Connect your Singular key')")
  self.assertEqual(self.page.locator('#detail-body').inner_text(),'')
  self.page.evaluate('c3module.destroy()');other.close()
  self.assertEqual(self.errors,[])
 def test_live_update_preserves_player_and_terminal_monotonicity(self):
  self.mount(identity=self.ids[0]);self.page.wait_for_selector('#work-player')
  self.page.evaluate('window.selected=document.querySelector("#work-player");window.source=selected.src')
  self.page.evaluate("""async id=>{const c=await(await import('/js/video-runtime.js')).videoContext();await c.store.update(id,{status:'rendering',video_status:'processing',cost:0});window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));}""",self.ids[0])
  self.page.wait_for_timeout(200)
  self.assertTrue(self.page.evaluate('selected===document.querySelector("#work-player")&&source===selected.src'))
  self.assertIn('Saved',self.page.locator('.detail-meta').inner_text());self.assertEqual(self.media_count(),1)
 def test_destroy_rejects_queued_read_and_removes_listeners(self):
  self.mount(identity=self.ids[1]);self.page.wait_for_selector('#detail-output')
  self.page.evaluate("""async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();const original=c.store.get;c.store.get=async id=>{const row=await original(id);window.waiting=true;await new Promise(r=>window.releaseRead=r);return row;};window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));}""")
  self.page.wait_for_function('window.waiting===true');self.page.evaluate('c3module.destroy();releaseRead()');self.page.wait_for_timeout(100)
  self.assertEqual(self.page.locator('#detail-body').inner_text(),'')
  self.assertEqual(self.page.locator('#work-player').count(),0)
 def test_media_cache_failure_keeps_playback_and_poster_pixels(self):
  self.page.evaluate("""()=>{const open=indexedDB.open.bind(indexedDB);indexedDB.open=(name,...args)=>{if(name==='singular-media.v1')throw new Error('OFFLINE FIXTURE cache failure');return open(name,...args);};}""")
  self.mount(identity=self.ids[0]);self.page.wait_for_selector('#work-player')
  self.page.wait_for_function("async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();return (await(await import('/js/poster-cache.js')).readPosters(c.store.account_id)).has('vid_offline');}")
  pixel=self.page.evaluate("""async()=>{const c=await(await import('/js/video-runtime.js')).videoContext(),image=new Image();image.src=(await(await import('/js/poster-cache.js')).readPosters(c.store.account_id)).get('vid_offline');await image.decode();const canvas=document.createElement('canvas');canvas.width=1;canvas.height=1;const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0,1,1);return [...ctx.getImageData(0,0,1,1).data];}""")
  self.assertGreater(pixel[2],100);self.assertLess(pixel[0],70)
  self.assertEqual(self.page.get_by_role('link',name='Download MP4',exact=True).count(),1)
  EVIDENCE.mkdir(parents=True,exist_ok=True)
  self.page.evaluate("()=>{const b=document.createElement('div');b.textContent='OFFLINE FIXTURE · synthetic video, not a live render';b.style='background:#ffed8a;color:#111;padding:10px';document.querySelector('#c3-host').prepend(b);for(const e of [...document.body.children])if(e.id!=='c3-host')e.remove();}")
  self.page.set_viewport_size({'width':390,'height':844});self.page.locator('#c3-host').screenshot(path=str(EVIDENCE/'detail-mobile-OFFLINE-FIXTURE.png'))
 def test_all_filters_and_gateway_links(self):
  self.ctx.route('**/v1/videos?*',lambda r:r.fulfill(json={'items':[{'id':'gateway_only','status':'queued','created_at':1793100000,'params':{'prompt':'Gateway search phrase'}}],'next_cursor':None}))
  self.page.evaluate("""async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();await c.store.create({flow_id:'impossibuild__model-jury',title:'OFFLINE FIXTURE comparison',prompt:'Judge this',status:'done'});}""")
  self.mount('work');self.page.wait_for_function("document.querySelector('#work-status').textContent.includes('loaded')")
  self.assertEqual(self.media_count(),0)
  self.page.set_viewport_size({'width':390,'height':844})
  self.page.evaluate("()=>{const b=document.createElement('div');b.textContent='OFFLINE FIXTURE · mixed local/gateway history';b.style='background:#ffed8a;color:#111;padding:10px';document.querySelector('#c3-host').prepend(b);for(const e of [...document.body.children])if(e.id!=='c3-host')e.remove();}")
  EVIDENCE.mkdir(parents=True,exist_ok=True);self.page.locator('#c3-host').screenshot(path=str(EVIDENCE/'work-mobile-OFFLINE-FIXTURE.png'))
  self.page.locator('#work-filter').select_option('Rendering');self.assertEqual(self.page.locator('#c3-host .work-card').count(),1)
  href=self.page.locator('#c3-host .work-card a').get_attribute('href');self.assertEqual(href,'#/work/gateway%3Agateway_only')
  self.page.locator('#work-filter').select_option('Comparisons');self.assertEqual(self.page.locator('#c3-host .work-card').count(),1)
  self.page.locator('#work-filter').select_option('Videos');self.assertEqual(self.page.locator('#c3-host .work-card').count(),2)
  self.page.locator('#work-search').fill('GATEWAY SEARCH');self.assertEqual(self.page.locator('#c3-host .work-card').count(),1)

 def test_gateway_live_refresh_during_download_keeps_selected_request(self):
  pending=[]
  self.ctx.route('**/v1/videos/vid_offline',lambda r:r.fulfill(json={'id':'vid_offline','status':'completed','params':{'prompt':'Recorded gateway prompt'}}))
  self.ctx.route('**/v1/videos/vid_offline/content',lambda r:pending.append(r))
  self.mount(identity='gateway:vid_offline');self.page.wait_for_function("document.querySelector('#detail-output')?.textContent.includes('Loading video')")
  self.page.wait_for_timeout(100);self.assertEqual(len(pending),1)
  self.page.evaluate("async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));}")
  self.page.wait_for_timeout(150)
  pending[0].fulfill(body=(ROOT/'tests/fixtures/offline-video.mp4').read_bytes(),content_type='video/mp4')
  self.page.wait_for_selector('#work-player[src^="blob:"]')
  self.assertEqual(len(pending),1)

 def test_gateway_stale_processing_cannot_reverse_completed_detail(self):
  state={'status':'completed','params':{'prompt':'Gateway recorded original'}}
  self.ctx.route('**/v1/videos/vid_offline',lambda r:r.fulfill(json={'id':'vid_offline',**state}))
  self.mount(identity='gateway:vid_offline');self.page.wait_for_selector('#work-player')
  self.page.evaluate('window.selected=document.querySelector("#work-player")')
  state.update(status='processing',params={})
  self.page.get_by_role('button',name='Refresh status',exact=True).click()
  self.page.evaluate("async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));}")
  self.page.wait_for_timeout(250)
  self.assertTrue(self.page.evaluate('selected===document.querySelector("#work-player")'))
  self.assertIn('Saved',self.page.locator('.detail-meta').inner_text())
  self.assertIn('Gateway recorded original',self.page.locator('.detail-meta').inner_text())

 def test_render_bound_planner_is_not_a_second_video_and_plan_has_no_media_action(self):
  self.page.evaluate("""async id=>{const c=await(await import('/js/video-runtime.js')).videoContext();await c.store.update(id,{idempotency_key:'offline-fixture-render-token'});await c.store.create({flow_id:'claw__motion-trimmer-video-plan',title:'Submitted planner snapshot',status:'done',outputs:{render_identity:{token:'offline-fixture-render-token'}}});await c.store.create({flow_id:'claw__motion-trimmer-video-plan',title:'Standalone plan',status:'done',prompt:'Plan not submitted'});}""",self.ids[0])
  self.mount('work');self.page.wait_for_selector('.work-card')
  self.page.locator('#work-filter').select_option('Videos')
  self.assertEqual(self.page.locator('#c3-host .work-card').count(),2)
  plan=self.page.locator('.work-card').filter(has_text='Plan not submitted')
  self.assertEqual(plan.get_by_role('button',name='Open video',exact=False).count(),0)
  self.assertEqual(self.media_count(),0)

 def test_planner_run_again_targets_the_video_flow_not_internal_plan_id(self):
  identity=self.page.evaluate("""async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();return (await c.store.create({flow_id:'claw__motion-trimmer-video-plan',title:'Offline plan',status:'done',inputs:{topic:'Original planner brief'}})).id;}""")
  self.mount(identity=identity);self.page.wait_for_selector('#detail-output')
  self.page.get_by_role('button',name='Run again with changes',exact=True).click()
  self.assertEqual(self.page.evaluate('location.hash'),'#/flow/claw__motion-trimmer-video')
  self.page.wait_for_function("document.querySelector('#video-topic')?.value==='Original planner brief'")
  self.assertIsNone(self.page.evaluate("sessionStorage.getItem('singular:run-again.v1')"))
 def test_media_cache_row_bound_validation_and_parallel_writes(self):
  result=self.page.evaluate("""async()=>{
   const m=await import('/js/media-cache.js'),a='a'.repeat(64),b='b'.repeat(64),blob=new Blob(['OFFLINE FIXTURE bytes'],{type:'video/mp4'});
   await Promise.all(Array.from({length:m.MAX_MEDIA_ROWS+4},(_,i)=>m.saveMedia(i%2?a:b,'row_'+String(i).padStart(3,'0'),blob)));
   const db=await new Promise((res,rej)=>{const r=indexedDB.open(m.MEDIA_DB);r.onsuccess=()=>res(r.result);r.onerror=rej;});
   const rows=await new Promise(res=>{const t=db.transaction('media'),r=t.objectStore('media').getAll();t.oncomplete=()=>res(r.result)});db.close();
   let rejects=0;for(const args of [['raw-key','job',blob],[a,'../job',blob]]){try{await m.saveMedia(...args)}catch{rejects++}}
   const wrong=await m.saveMedia(a,'wrong',new Blob(['text'],{type:'text/plain'}));
   return {count:rows.length,max:m.MAX_MEDIA_ROWS,scopes:rows.every(x=>[a,b].includes(x.account)),fields:Object.keys(rows[0]).sort(),rejects,wrong};
  }""")
  self.assertEqual(result['count'],result['max']);self.assertTrue(result['scopes']);self.assertEqual(result['rejects'],2);self.assertFalse(result['wrong'])
  self.assertEqual(result['fields'],['account','blob','created_at','id','job'])

 def test_copy_actions_use_recorded_full_text_and_prompt(self):
  self.ctx.grant_permissions(['clipboard-read','clipboard-write'],origin=self.url)
  self.mount(identity=self.ids[1]);self.page.wait_for_selector('#detail-output')
  self.page.get_by_role('button',name='Copy output',exact=True).click()
  self.page.wait_for_function("document.querySelector('#detail-status').textContent==='Copied.'")
  self.assertEqual(json.loads(self.page.evaluate('navigator.clipboard.readText()')),{'text':'Full fixture email <script>not markup</script>'})
  self.page.get_by_role('button',name='Copy prompt',exact=True).click()
  self.assertEqual(self.page.evaluate('navigator.clipboard.readText()'),'Find lighthouse')
 def test_cross_tab_durable_removal_closes_selected_player(self):
  self.mount(identity=self.ids[0]);self.page.wait_for_selector('#work-player')
  other=self.ctx.new_page();other.goto(self.url+'/js/store.js')
  other.evaluate("""async id=>{const db=await new Promise((res,rej)=>{const r=indexedDB.open('singular-runs.v1');r.onsuccess=()=>res(r.result);r.onerror=rej;});await new Promise((res,rej)=>{const t=db.transaction('runs','readwrite');t.objectStore('runs').delete(id);t.oncomplete=res;t.onabort=rej;});db.close();}""",self.ids[0])
  self.page.wait_for_function("document.querySelector('#detail-status').textContent.includes('Run not found')",timeout=10000)
  self.assertEqual(self.page.locator('#work-player').count(),0)
  other.close()

for name in list(vars(VideoBrowser)):
 if name.startswith('test_'):setattr(Detail,name,None)
del VideoBrowser
if __name__=='__main__':unittest.main()
