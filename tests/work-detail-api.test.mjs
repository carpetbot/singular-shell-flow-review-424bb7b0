import test from 'node:test';
import assert from 'node:assert/strict';
import {get} from '../js/store.js';
import {fetchVideoJob,listVideos} from '../js/work-api.js';
test('gateway detail uses one fixed authenticated job path and preserves validated recorded metadata',async()=>{
 const original=globalThis.fetch;get().settings.apiKey='offline-status-unit';let calls=0;
 try{globalThis.fetch=async(url,opts)=>{calls++;assert.equal(url,'/v1/videos/unit_job');assert.equal(opts.headers.Authorization,'Bearer offline-status-unit');assert.equal(opts.credentials,'omit');assert.equal(opts.redirect,'error');assert.equal(opts.cache,'no-store');assert.ok(opts.signal instanceof AbortSignal);return Response.json({id:'unit_job',status:'completed',model:'fixture/model',cost_usd:.75,params:{prompt:'Recorded fixture'},created_at:1793100000});};
 const job=await fetchVideoJob('unit_job');assert.equal(calls,1);assert.equal(job.cost_usd,.75);assert.equal(job.params.prompt,'Recorded fixture');assert.equal(job.created_at,1793100000);
 }finally{globalThis.fetch=original;}
});
test('gateway detail rejects mismatched identities and keeps malformed money unknown',async()=>{
 const original=globalThis.fetch;
 try{for(const id of ['../escape','has space',{},null])await assert.rejects(fetchVideoJob(id));
 globalThis.fetch=async()=>Response.json({id:'another_job',status:'completed'});await assert.rejects(fetchVideoJob('unit_job'),/identity/);
 for(const cost of ['0',-1,null,{},true]){globalThis.fetch=async()=>Response.json({id:'unit_job',status:'queued',cost_usd:cost,model:{bad:1},params:{prompt:{bad:1}},created_at:{bad:1}});const job=await fetchVideoJob('unit_job');assert.equal(job.cost_usd,null);assert.equal(job.params.prompt,'Prompt saved on another device');assert.equal(job.created_at,null);}
 }finally{globalThis.fetch=original;}
});
test('video list retains known cost without inventing missing cost or prompt',async()=>{
 const original=globalThis.fetch;
 try{globalThis.fetch=async()=>Response.json({items:[{id:'known',cost_usd:0,params:{prompt:'Recorded'}},{id:'unknown',cost_usd:'0'}]});const {items}=await listVideos();assert.equal(items[0].cost_usd,0);assert.equal(items[1].cost_usd,null);assert.equal(items[1].params.prompt,'Prompt saved on another device');
 }finally{globalThis.fetch=original;}
});
