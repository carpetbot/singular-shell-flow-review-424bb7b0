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

test('creation fails closed without safe origin locks',async()=>{
 const f=fixtures(),s=new VideoSession({...f,locks:null});
 await assert.rejects(s.create(spec,1.583334),/lock/i);assert.equal(f.posts.length,0);
});
