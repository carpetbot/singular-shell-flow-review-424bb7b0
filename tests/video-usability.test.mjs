import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const ui=await import('../js/video-ui.js');
test('video money always uses two decimals without rounding the numeric quote',()=>{
 for(const [n,label] of [[1.583334,'$1.58'],[.001,'$0.00'],[0,'$0.00'],[null,'unknown / unsettled']]) assert.equal(ui.videoMoney(n),label);
});
const {VideoSession}=await import('../js/video.js');
const memory=()=>{let value='[]';return {getItem:()=>value,setItem:(_,v)=>value=v};};
const locks={tail:Promise.resolve(),request(_,__,fn){const p=this.tail.then(fn);this.tail=p.catch(()=>{});return p;}};
test('clear finished atomically rereads all 20 refs, preserves every unresolved state and new work',async()=>{
 const storage=memory(),s=new VideoSession({key:'key',storage,locks});
 const {createHash}=await import('node:crypto');const keyHash=createHash('sha256').update('key').digest('hex');
 const terminal=Array.from({length:20},(_,i)=>({token:'done'+i,keyHash,status:['completed','failed','rejected'][i%3]}));
 storage.setItem('',JSON.stringify(terminal));s.refresh();await s.clearFinished();assert.deepEqual(s.records,[]);assert.equal(s.record,null);
 const pending=['creating','queued','processing','uncertain','unknown','alien'].map((status,i)=>({token:'pending'+i,status,keyHash:'wrong-account'}));
 storage.setItem('',JSON.stringify([...terminal,...pending]));s.refresh();s.record=s.records[0];
 // Another tab persists new work after this observer read.
 storage.setItem('',JSON.stringify([...terminal,...pending,{token:'new',status:'processing'}]));
 await s.clearFinished();assert.deepEqual(s.records.map(r=>r.token),[...pending.map(r=>r.token),'new']);assert.ok(s.record&&s.record.status==='processing');
 assert.deepEqual(JSON.parse(storage.getItem('')),s.records);
 await assert.rejects(s.newVersion(),/pending|uncertain/);
});
test('video platform labels and customer copy are plain language',()=>{
 const view=readFileSync(new URL('../js/video-ui.js',import.meta.url),'utf8');
 for(const label of ['X','Instagram Reels','YouTube Shorts'])assert.ok(view.includes('>'+label+'</option>'));
 for(const name of ['../js/video-ui.js','../js/video.js']){
  const text=readFileSync(new URL(name,import.meta.url),'utf8');
  assert.doesNotMatch(text,/(?:Release gate|explicit generation|creating key|idempotency token|uncertain submission)/i);
 }
});
const source=name=>readFileSync(new URL(name,import.meta.url),'utf8');
test('video test catalog lives in source fixture and all readers are location relative',()=>{
 for(const name of ['video.test.mjs','video-cross-tab.test.mjs','test_video_browser.py']) assert.doesNotMatch(source(name),/\/home\/orangepi|motion-trimmer-video-pricing\.json/);
 assert.ok(JSON.parse(source('fixtures/video-pricing.json')).models.length);
});
