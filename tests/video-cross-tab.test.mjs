import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {VideoSession} from '../js/video.js';
const catalog=JSON.parse(readFileSync('/home/orangepi/.hermes/profiles/slack/cache/scratch/motion-trimmer-video-pricing.json'));
const fields={duration:'fixture_duration',aspectRatio:null,audio:null};
const spec={model:'alibaba/wan-3.0/text-to-video',duration:15,prompt:'Private boat.'};
function fixtures(){
 const data=new Map(),posts=[];
 const storage={getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v)};
 const locks={tail:Promise.resolve(),request(name,opts,fn){assert.equal(opts.mode,'exclusive');assert.equal(name,'motion-video.v1');const p=this.tail.then(fn);this.tail=p.catch(()=>{});return p;}};
 let lost=false;
 const fetcher=async(path,opts={})=>{if(path==='/pricing.json')return Response.json(catalog);if(opts.method==='POST'){posts.push(opts);if(lost)throw Error('lost fixture');return Response.json({id:'vid_'+posts.length,status:'queued'});}return Response.json({id:'vid_1',status:'completed',cost_usd:1.58});};
 return {storage,locks,fetcher,fields,key:'offline-private-key',posts,setLost:x=>lost=x};
}
test('two already-open sessions serialize creation, refresh storage, preserve history',async()=>{
 const f=fixtures(),a=new VideoSession(f),b=new VideoSession(f);
 await Promise.allSettled([a.create(spec,1.583334),b.create(spec,1.583334)]);
 assert.equal(f.posts.length,1,'stale tabs must not create independent paid jobs');
 await a.resume();await a.newVersion();await a.create({...spec,prompt:'Explicit next version'},1.583334);
 assert.equal(JSON.parse(f.storage.getItem('motion-video.v1')).length,2);
 await assert.rejects(b.create(spec,1.583334),/existing/);
 assert.equal(f.posts.length,2);
 assert.equal(JSON.parse(f.storage.getItem('motion-video.v1')).length,2);
});
test('stale tab retries uncertain creation with persisted token and identical body only',async()=>{
 const f=fixtures(),a=new VideoSession(f),b=new VideoSession(f);f.setLost(true);
 await assert.rejects(a.create(spec,1.583334));f.setLost(false);
 await assert.rejects(b.create({...spec,prompt:'Changed'},1.583334),/identical/);
 await b.create(spec,1.583334);
 assert.equal(f.posts.length,2);assert.equal(f.posts[0].body,f.posts[1].body);
 assert.equal(f.posts[0].headers['Idempotency-Key'],f.posts[1].headers['Idempotency-Key']);
 assert.equal(JSON.parse(f.storage.getItem('motion-video.v1')).length,1);
});
test('all saved same-account pending jobs block new versions even when old completed job selected',async()=>{
 for(const status of ['queued','processing','creating','uncertain']){
  const f=fixtures(),s=new VideoSession(f);await s.create(spec,1.583334);await s.resume();
  const completed=structuredClone(s.record);
  const pending={...completed,token:'pending-'+status,id:status==='uncertain'||status==='creating'?null:'vid_pending',status};
  // Pending need not be newest: selection and latest alone are both insufficient.
  f.storage.setItem('motion-video.v1',JSON.stringify([pending,completed]));
  const reopened=new VideoSession(f);reopened.record=reopened.records[1];
  await assert.rejects(reopened.newVersion(),/pending|uncertain/);
  reopened.record=null;
  await assert.rejects(reopened.create({...spec,prompt:'Must not create'},1.583334),/pending|uncertain/);
  assert.equal(f.posts.length,1);
 }
});

test('idempotency token binds canonical logical request and persisted shared plan identity',async()=>{
 const f=fixtures(),a=new VideoSession(f),b=new VideoSession(f);
 await a.create(spec,1.583334);
 const first=structuredClone(a.record);
 assert.equal(typeof first.planId,'string');
 const {createHash}=await import('node:crypto');
 const expected=createHash('sha256').update(JSON.stringify({planId:first.planId,model:spec.model,prompt:spec.prompt,duration:spec.duration,resolution:'720p'})).digest('hex');
 assert.equal(first.token,expected);
 await a.resume();await Promise.all([a.newVersion(),b.newVersion()]);
 await Promise.allSettled([a.create(spec,1.583334),b.create(spec,1.583334)]);
 const history=JSON.parse(f.storage.getItem('motion-video.v1'));
 assert.equal(f.posts.length,2);assert.equal(history.length,2);
 assert.notEqual(history[1].planId,first.planId);assert.notEqual(history[1].token,first.token);
});

for(const terminal of ['completed','failed'])test(`delayed processing poll cannot regress persisted ${terminal} or its receipt`,async()=>{
 const f=fixtures(),a=new VideoSession(f);await a.create(spec,1.583334);
 let release,started;const waiting=new Promise(resolve=>{started=resolve;});
 a.fetcher=async()=>{started();await new Promise(resolve=>{release=resolve;});return Response.json({id:'vid_1',status:'processing'});};
 const b=new VideoSession({...f,fetcher:async()=>Response.json({id:'vid_1',status:terminal,cost_usd:1.58,error:'fixture_failure'})});
 const changes=[];a.onChange=r=>changes.push(structuredClone(r));
 const delayed=a.resume({sleep:async()=>{a.dispose();}});await waiting;
 await b.resume();const authoritative=JSON.parse(f.storage.getItem('motion-video.v1'))[0];release();const result=await delayed;
 assert.equal(result?.status,terminal,'poll must return reconciled terminal instead of continuing stale processing');
 assert.deepEqual(JSON.parse(f.storage.getItem('motion-video.v1'))[0],authoritative);
 assert.deepEqual(a.record,authoritative,'caller must adopt persisted terminal for UI and download');
 assert.deepEqual(changes.at(-1),authoritative);
 assert.equal(a.record.settled,terminal==='completed'?1.58:0);
 const reopened=new VideoSession(f);await reopened.newVersion();assert.equal(reopened.record,null);
 if(terminal==='completed'){
  a.fetcher=async path=>{assert.equal(path,'/v1/videos/vid_1/content');return new Response('offline video',{headers:{'Content-Type':'video/mp4'}});};
  a.stopped=false;a.urlAPI={createObjectURL:()=> 'blob:offline',revokeObjectURL:()=>{}};
  assert.equal(await a.download(),'blob:offline');
 }else await assert.rejects(a.download(),/Complete/);
 assert.equal(f.posts.length,1);
});

test('same-job stale save preserves settled receipt, quote and recovery metadata',async()=>{
 const f=fixtures(),a=new VideoSession(f);await a.create(spec,1.583334);
 const b=new VideoSession(f);await b.resume();
 const persisted=JSON.parse(f.storage.getItem('motion-video.v1'));
 persisted[0].recoveryNote='retained reference';f.storage.setItem('motion-video.v1',JSON.stringify(persisted));
 a.record.status='completed';a.record.settled=null;a.record.quote={...a.record.quote,price:999};await a.save();
 assert.equal(a.record.settled,1.58);assert.deepEqual(a.record.quote,persisted[0].quote);assert.equal(a.record.recoveryNote,'retained reference');
});

test('same-token mismatched job, key or version identity never overwrites recovery',async()=>{
 for(const field of ['id','keyHash','planId','bodyHash']){
  const f=fixtures(),a=new VideoSession(f);await a.create(spec,1.583334);
  const saved=f.storage.getItem('motion-video.v1');a.record[field]='different_identity';
  await assert.rejects(a.save(),/identity mismatch/);assert.equal(f.storage.getItem('motion-video.v1'),saved);
 }
});

test('late old-version poll preserves a distinct new-version identity and history',async()=>{
 const f=fixtures(),a=new VideoSession(f);await a.create(spec,1.583334);
 const b=new VideoSession(f);await b.resume();await b.newVersion();await b.create({...spec,prompt:'New version'},1.583334);
 const saved=JSON.parse(f.storage.getItem('motion-video.v1'));a.record.status='processing';await a.save();
 assert.deepEqual(JSON.parse(f.storage.getItem('motion-video.v1')),saved);
 assert.equal(a.record.token,saved[0].token);assert.equal(a.record.status,'completed');
 assert.notEqual(saved[0].token,saved[1].token);assert.notEqual(saved[0].id,saved[1].id);
});

test('creation fails closed without safe origin locks',async()=>{
 const f=fixtures(),s=new VideoSession({...f,locks:null});
 await assert.rejects(s.create(spec,1.583334),/lock/i);assert.equal(f.posts.length,0);
});
