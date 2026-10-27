import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const v=await import('../js/video.js').catch(()=>({}));
const catalog=JSON.parse(readFileSync('/home/orangepi/.hermes/profiles/slack/cache/scratch/motion-trimmer-video-pricing.json'));
test('exact catalog quote, documented body, duration release gate',()=>{
 assert.equal(typeof v.quoteVideo,'function','video quote feature missing');
 for(const [model,res,prices] of [['alibaba/wan-3.0/text-to-video','720p',[.527778,1.055556,1.583334]],['minimax/h3-max-turbo','768p',[.211111,.422222,.633334]]]){
  for(const [i,duration] of [5,10,15].entries())assert.equal(v.quoteVideo(catalog,model,duration).price,prices[i]);
  assert.deepEqual(v.videoBody({model,prompt:'Boat',duration:15}),{model,prompt:'Boat',resolution:res});
 }
 assert.throws(()=>v.quoteVideo(catalog,'invented',15));
 assert.throws(()=>v.quoteVideo(catalog,v.MODELS[0].id,60));
 assert.throws(()=>v.quoteVideo({models:[]},v.MODELS[0].id,15));
 assert.equal(v.releaseReady(),false);
 assert.deepEqual(v.FIELDS,{duration:null,aspectRatio:null,audio:null});
 const confirmed={duration:'fixture_duration',aspectRatio:null,audio:null};
 assert.equal(v.releaseReady(confirmed),true);
 assert.equal(v.videoBody({model:v.MODELS[0].id,prompt:'Boat',duration:10},confirmed).fixture_duration,10);
});
const planFixture={shotbeats:[{duration_s:15,description:'Boat drifts'}],prompt:'A paper boat drifts on a calm pond, slowly tracking the ripples.',overlays:[{at_s:0,text:'Hello'}],dropped:['Exact brand logo requires editor assets']};
test('one structured planner call; typed edits; 5xx-only backup and honest receipts',async()=>{
 assert.equal(typeof v.planVideo,'function','planner feature missing');
 let calls=[];const chat=async(msg,opts)=>{calls.push({msg,opts});return {content:JSON.stringify(planFixture),receipt:{estCost:.001}};};
 const result=await v.planVideo({topic:'Boat',duration:15,platform:'x'},{chat,catalog});
 assert.equal(calls.length,1);assert.equal(calls[0].opts.model,'anthropic/claude-sonnet-5.5');
 assert.match(calls[0].msg[0].content,/Do not.*text/i);assert.deepEqual(result.plan,planFixture);
 assert.equal(result.receipts[0].estCost,.001);
 for(const change of [{shotbeats:[{duration_s:'15',description:'bad'}]},{shotbeats:[{duration_s:10,description:'bad'}]},{overlays:[{at_s:15,text:'late'}]},{overlays:[{at_s:'0',text:'bad'}]},{dropped:'not array'},{prompt:''}])assert.throws(()=>v.validatePlan({...planFixture,...change},15));
 for(const status of [401,402,429,500]){
  calls=[];const bad=async(msg,opts)=>{calls.push(opts.model);if(calls.length===1)throw Object.assign(new Error('offline gateway failure'),{status});return chat(msg,opts);};
  if(status===500){await v.planVideo({topic:'Boat',duration:15},{chat:bad,catalog});assert.equal(calls[1],'deepseek/deepseek-v4.1-flash-1017');}
  else {await assert.rejects(v.planVideo({topic:'Boat',duration:15},{chat:bad,catalog}),e=>e.receipts.length===1&&e.receipts[0].estCost===null);assert.equal(calls.length,1);}
 }
 await assert.rejects(v.planVideo({topic:'Boat',duration:15},{chat,catalog:{models:[]}}));
});

const memory=()=>{const m=new Map();return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k),dump:()=>[...m.values()].join('')};};
// Deterministic Web Locks fixture: shared across sessions, like one origin.
const locks={tail:Promise.resolve(),request(name,options,fn){const task=this.tail.then(fn);this.tail=task.catch(()=>{});return task;}};
const confirmed={duration:'fixture_duration',aspectRatio:null,audio:null};
const spec={model:'alibaba/wan-3.0/text-to-video',duration:15,prompt:'A private paper boat.'};
test('explicit fresh-priced submit deduplicates; uncertain retry and reload keep identical key/body',async()=>{
 assert.equal(typeof v.VideoSession,'function','video submission feature missing');
 const storage=memory();const calls=[];let lose=true;
 const fetcher=async(path,opts={})=>{if(path==='/pricing.json')return Response.json(catalog);calls.push({path,...opts});if(lose)throw new TypeError('offline network lost after acceptance');return Response.json({id:'vid_fixture',status:'queued'},{status:202});};
 const s=new v.VideoSession({locks,key:'fixture-secret',fetcher,storage,fields:confirmed});
 await Promise.allSettled([s.create(spec,1.583334),s.create(spec,1.583334)]);assert.equal(calls.length,1);
 assert.equal(s.record.status,'uncertain');assert.equal(s.record.settled,null);
 assert.ok(!storage.dump().includes('fixture-secret'));assert.ok(!storage.dump().includes(spec.prompt));
 const token=calls[0].headers['Idempotency-Key'];lose=false;
 const reloaded=new v.VideoSession({locks,key:'fixture-secret',fetcher,storage,fields:confirmed});
 await assert.rejects(reloaded.create({...spec,prompt:'edited'},1.583334),/identical/);
 await reloaded.create(spec,1.583334);assert.equal(calls.length,2);assert.equal(calls[1].headers['Idempotency-Key'],token);assert.equal(calls[1].body,calls[0].body);
 const again=new v.VideoSession({locks,key:'fixture-secret',fetcher,storage,fields:confirmed});assert.equal(again.record.id,'vid_fixture');
 await assert.rejects(again.create(spec,1.583334),/existing/);assert.equal(calls.length,2);
 const wrong=new v.VideoSession({locks,key:'different-key',fetcher,storage,fields:confirmed});await assert.rejects(wrong.resume(),/creating key/);assert.equal(calls.length,2);
 const locked=new v.VideoSession({locks,key:'fixture-secret',fetcher,storage:memory()});await assert.rejects(locked.create(spec,1.583334),/Release gate/);
 const priced=new v.VideoSession({locks,key:'fixture-secret',fetcher,storage:memory(),fields:confirmed});await assert.rejects(priced.create(spec,0),/Price changed/);assert.equal(calls.length,2);
});

test('reload polls bounded states then retries only safe authenticated content; blob lifecycle',async()=>{
 assert.equal(typeof v.VideoSession.prototype.download,'function','inline authenticated download missing');
 const storage=memory(),calls=[],urls={created:[],revoked:[],createObjectURL(blob){this.created.push(blob);return 'blob:fixture-'+this.created.length;},revokeObjectURL(url){this.revoked.push(url);}};
 let polls=0,contentFails=true;
 const fetcher=async(path,opts={})=>{calls.push({path,...opts});
  if(path==='/pricing.json')return Response.json(catalog);
  if(opts.method==='POST')return Response.json({id:'vid_safe',status:'queued'},{status:202});
  if(path.endsWith('/content'))return contentFails?Response.json({code:'video_result_unavailable'},{status:502}):new Response(new Uint8Array([0,1,2]),{headers:{'Content-Type':'video/mp4'}});
  return Response.json({id:'vid_safe',status:++polls===1?'processing':'completed',cost_usd:polls===1?0:1.58,result_url:polls===1?null:'https://api.impossi.build/v1/videos/vid_safe/content'});
 };
 let s=new v.VideoSession({locks,key:'fixture-key',fetcher,storage,fields:confirmed,urlAPI:urls});await s.create(spec,1.583334);
 s=new v.VideoSession({locks,key:'fixture-key',fetcher,storage,fields:confirmed,urlAPI:urls});const states=[];s.onChange=r=>states.push([r.status,r.settled]);
 await s.resume({sleep:async()=>{},deadlineMs:1000});assert.deepEqual(states.slice(0,2),[['processing',null],['completed',1.58]]);
 await assert.rejects(s.download(),e=>e.status===502);assert.equal(s.record.status,'completed');assert.equal(s.record.settled,1.58);
 contentFails=false;await s.download();assert.equal(s.blobURL,'blob:fixture-1');
 assert.equal(calls.filter(c=>c.method==='POST').length,1);assert.ok(calls.filter(c=>c.path.endsWith('/content')).every(c=>c.path==='/v1/videos/vid_safe/content'&&c.headers.Authorization==='Bearer fixture-key'));
 await s.download();assert.deepEqual(urls.revoked,['blob:fixture-1']);s.dispose();assert.deepEqual(urls.revoked,['blob:fixture-1','blob:fixture-2']);
 for(const bad of ['https://evil.test/v1/videos/vid_safe/content','//evil.test/a','/v1/videos/other/content','/v1/videos/vid_safe/content?key=x','/v1/videos/vid_safe/content#secret'])assert.throws(()=>v.safeContentPath('vid_safe',bad));
 assert.throws(()=>v.safeContentPath('../bad',null));
});

test('poll requests carry bounded abort signals; pause never cancels job; terminal and HTTP errors differ',async()=>{
 const storage=memory();let mode='queued',status=200,count=0,clock=0,signals=[];
 const fetcher=async(path,opts={})=>{
  if(path==='/pricing.json')return Response.json(catalog);
  if(opts.method==='POST')return Response.json({id:'vid_stop',status:'queued'},{status:202});
  count++;signals.push(opts.signal);return Response.json(status===200?{id:'vid_stop',status:mode,cost_usd:0,error:mode==='failed'?'content_policy_violation':null}:{code:'failure'},{status});
 };
 const s=new v.VideoSession({locks,key:'fixture',fetcher,storage,fields:confirmed});await s.create(spec,1.583334);
 await assert.rejects(s.resume({deadlineMs:5000,now:()=>clock,sleep:async ms=>{clock+=ms;}}),/deadline/);
 assert.ok(signals.every(s=>s instanceof AbortSignal),'poll requests must be abortable');
 assert.equal(s.record.settled,null);const before=count;await s.resume({sleep:async()=>s.dispose()});assert.equal(count,before+1);assert.equal(s.record.status,'queued');
 mode='failed';await s.resume();assert.equal(s.record.settled,0);assert.equal(s.record.error,'content_policy_violation');
 await assert.rejects(s.download(),/Complete/);
 for(const code of [401,402,404,500]){status=code;await assert.rejects(s.resume(),e=>e.status===code);}
 await s.newVersion();assert.equal(s.record,null);assert.equal(storage.dump().includes('vid_stop'),true);
});

test('video price refusals and schema boundaries are never coerced',()=>{
 for(const bad of [null,'15',true,0,60])assert.throws(()=>v.validatePlan(planFixture,bad));
 for(const bad of [null,'0',false,-1,Infinity])assert.throws(()=>v.validatePlan({...planFixture,overlays:[{at_s:bad,text:'Hello'}]},15));
 const altered=structuredClone(catalog);const m=altered.models.find(m=>m.id===spec.model);m.videoPricing.configs.find(c=>c.duration===15&&c.resolution==='720p').priceUsd='1.583334';assert.throws(()=>v.quoteVideo(altered,spec.model,15));
 assert.throws(()=>v.validatePlan({...planFixture,prompt:'word '.repeat(121)},15));
 assert.equal(v.releaseReady({duration:'prompt'}),false);
});

test('new explicit generation changes token, retains prior job receipt; unknown completed cost is not zero',async()=>{
 const storage=memory(),tokens=[];let id=0;
 const fetcher=async(path,opts={})=>{if(path==='/pricing.json')return Response.json(catalog);if(opts.method==='POST'){tokens.push(opts.headers['Idempotency-Key']);return Response.json({id:'vid_'+(++id),status:'queued'},{status:202});}return Response.json({id:'vid_'+id,status:'completed',cost_usd:null});};
 const s=new v.VideoSession({locks,key:'fixture',fetcher,storage,fields:confirmed});await s.create(spec,1.583334);await s.resume();assert.equal(s.record.settled,null);await s.newVersion();await s.create({...spec,prompt:'An explicit edited version.'},1.583334);assert.equal(tokens.length,2);assert.notEqual(tokens[0],tokens[1]);assert.equal(s.records.length,2);assert.equal(s.records[0].id,'vid_1');
});

test('download byte mismatches and broken streams report exact incomplete retry message without Blob',async()=>{
 for(const response of [
  new Response(new Uint8Array([1,2,3]),{headers:{'Content-Type':'video/mp4','Content-Length':'4'}}),
  new Response(new Uint8Array([1,2,3]),{headers:{'Content-Type':'video/mp4','Content-Length':'2'}}),
  new Response(new ReadableStream({start(c){c.enqueue(new Uint8Array([1]));c.error(new Error('private network detail'));}}),{headers:{'Content-Type':'video/mp4'}})
 ]){
  let blobs=0;const s=new v.VideoSession({locks,key:'fixture',storage:memory(),fetcher:async()=>response,urlAPI:{createObjectURL(){blobs++;return 'blob:bad';}}});
  s.record={id:'vid_fixture',status:'completed'};s.sameKey=async()=>{};
  await assert.rejects(s.download(),{message:'Download incomplete, retry download'});assert.equal(blobs,0);assert.equal(s.record.status,'completed');
 }
});

test('definite create auth/credit rejection is not an uncertain held job and allows explicit recovery',async()=>{
 for(const status of [401,402]){
  const storage=memory();let posts=0;const fetcher=async(path)=>path==='/pricing.json'?Response.json(catalog):(posts++,Response.json({code:'failure'},{status}));
  const s=new v.VideoSession({locks,key:'fixture-rejected',fetcher,storage,fields:confirmed});await assert.rejects(s.create(spec,1.583334),e=>e.status===status);assert.equal(posts,1);assert.equal(s.record.status,'rejected');assert.equal(s.record.settled,0);await s.newVersion();assert.equal(s.record,null);
 }
});
