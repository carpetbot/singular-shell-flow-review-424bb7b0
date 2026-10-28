import test from 'node:test';
import assert from 'node:assert/strict';
import {get} from '../js/store.js';
import {listVideos,fetchVideo,MAX_MEDIA_BYTES} from '../js/work-api.js';

test('list rejects malformed job identity and cursor rather than guessing fields',async()=>{
 const original=globalThis.fetch;
 try{
  for(const data of [{items:[{}]},{items:[{id:123}]},{items:[{id:'valid'}],next_cursor:123},{items:[{id:'../bad'}]},{videos:[]}]){
   globalThis.fetch=async()=>Response.json(data);await assert.rejects(listVideos(null));
  }
 }finally{globalThis.fetch=original;}
});
test('list uses existing settings key, fixed same-origin route, encoded cursor and no persistence',async()=>{
 const original=globalThis.fetch;get().settings.apiKey='offline-unit';
 try{
  globalThis.fetch=async(url,opts)=>{assert.equal(url,'/v1/videos?limit=50&cursor=abc%3D');assert.equal(opts.headers.Authorization,'Bearer offline-unit');assert.equal(opts.redirect,'error');assert.ok(opts.signal instanceof AbortSignal);assert.equal(opts.cache,'no-store');return Response.json({items:[{id:'video_ok'}],next_cursor:null});};
  assert.equal((await listVideos('abc=')).items[0].id,'video_ok');
 }finally{globalThis.fetch=original;}
});
test('media download rejects declared oversize, streamed overflow and incomplete content before Blob',async()=>{
 const original=globalThis.fetch;
 try{
  globalThis.fetch=async()=>new Response('x',{headers:{'Content-Length':String(MAX_MEDIA_BYTES+1)}});await assert.rejects(fetchVideo('vid_a'),/100 MB/);
  globalThis.fetch=async()=>new Response('x',{headers:{'Content-Length':'2'}});await assert.rejects(fetchVideo('vid_a'),/Incomplete/);
  let canceled=false;globalThis.fetch=async()=>new Response(new ReadableStream({start(c){const chunk=new Uint8Array(1024*1024);for(let i=0;i<101;i++)c.enqueue(chunk);},cancel(){canceled=true;}}));
  await assert.rejects(fetchVideo('vid_a'),/100 MB/);assert.equal(canceled,true);
 }finally{globalThis.fetch=original;}
});
test('media error body is canceled without buffering and upstream URL is never followed',async()=>{
 const original=globalThis.fetch;let canceled=false;
 try{
  globalThis.fetch=async(url,opts)=>{assert.equal(url,'/v1/videos/vid_a/content');assert.ok(opts.signal instanceof AbortSignal);assert.equal(opts.redirect,'error');return new Response(new ReadableStream({cancel(){canceled=true;}}),{status:502});};
  await assert.rejects(fetchVideo('vid_a'),/unavailable/);assert.equal(canceled,true);
 }finally{globalThis.fetch=original;}
});
