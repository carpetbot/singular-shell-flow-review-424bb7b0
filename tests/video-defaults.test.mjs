import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as v from '../js/video.js';
const catalog=JSON.parse(readFileSync(new URL('./fixtures/video-pricing.json',import.meta.url)));
const now=Date.parse(catalog.as_of)+1000;
const model=v.MODELS[0].id;
const spec={model,duration:5,prompt:'A boat drifts.'};
const locks={request:async(_,__,fn)=>fn()};
const memory=()=>{let value='[]';return {getItem:()=>value,setItem:(_,v)=>value=v};};
test('approved five second default mode validates exact defaults and sends only documented fields',async()=>{
 assert.equal(typeof v.quoteDefaultVideo,'function');
 for(const [i,price] of [[0,.527778],[1,.211111]]){
  const quote=v.quoteDefaultVideo(catalog,v.MODELS[i].id,5,now);assert.equal(quote.price,price);
 }
 let body;const session=new v.VideoSession({key:'offline',locks,storage:memory(),now:()=>now,fetcher:async(path,o)=>path==='/pricing.json'?Response.json(catalog):(body=JSON.parse(o.body),Response.json({id:'safe',status:'queued'}))});
 await session.create(spec,.527778);assert.deepEqual(body,{model,prompt:spec.prompt,resolution:'720p'});assert.deepEqual(v.FIELDS,{duration:null,aspectRatio:null,audio:null});
});
test('default generation refuses missing, stale, mismatched, unroutable or nonexact catalog before POST',async()=>{
 for(const change of [c=>delete c.models.find(m=>m.id===model).videoPricing.defaults,c=>c.models.find(m=>m.id===model).videoPricing.defaults.duration=15,c=>c.models.find(m=>m.id===model).videoPricing.defaults.resolution='1080p',c=>c.models.find(m=>m.id===model).routable=false,c=>c.models.find(m=>m.id===model).videoPricing.exact=false,c=>c.as_of='2000-01-01T00:00:00Z',c=>c.models.find(m=>m.id===model).videoPricing.configs=[]]){
  const copy=structuredClone(catalog);change(copy);let posts=0;
  const session=new v.VideoSession({key:'offline',locks,storage:memory(),now:()=>now,fetcher:async(path)=>path==='/pricing.json'?Response.json(copy):(posts++,Response.json({}))});
  await assert.rejects(session.create(spec,.527778));assert.equal(posts,0);
 }
 for(const duration of [10,15])assert.throws(()=>v.quoteDefaultVideo(catalog,model,duration,now));
});
test('default audio label is backed by catalog and history capacity recovers after clearing 20 finished refs',async()=>{
 const changed=structuredClone(catalog);changed.models.find(m=>m.id===model).videoPricing.defaults.audio=false;
 assert.throws(()=>v.quoteDefaultVideo(changed,model,5,now));
 const {createHash}=await import('node:crypto');const keyHash=createHash('sha256').update('offline').digest('hex');
 const storage=memory();storage.setItem('',JSON.stringify(Array.from({length:20},(_,i)=>({token:'done'+i,status:'completed',keyHash}))));let posts=0;
 const s=new v.VideoSession({key:'offline',locks,storage,now:()=>now,fetcher:async(path)=>path==='/pricing.json'?Response.json(catalog):(posts++,Response.json({id:'new',status:'queued'}))});
 await s.clearFinished();await s.create(spec,.527778);assert.equal(posts,1);assert.equal(s.records.length,1);
});
