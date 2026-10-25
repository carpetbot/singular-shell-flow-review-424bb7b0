import test from 'node:test';
import assert from 'node:assert/strict';
import * as skills from '../js/views/skills.js';
import {readFile} from 'node:fs/promises';

test('supplied exact flow with public catalog snapshot completes four offline calls at default cap, blocks .001 before calls',async()=>{
 const {flowPreflight}=await import('../js/flow.js');
 const root=new URL('../skills/impossibuild__prospect-to-cold-email/',import.meta.url);
 const m=JSON.parse(await readFile(new URL('singular.flow.json',root),'utf8'));m.prompts={};
 for(const s of m.runtime.steps)for(const path of [s.system,s.user_template])m.prompts[path]=await readFile(new URL(path,root),'utf8');
 const live=JSON.parse(await readFile(new URL('../reports/catalog-live.json',import.meta.url),'utf8'));
 const vals={prospect_name:'Sample',company:'Sample',sender_name:'Sample',research_notes:'The team is hiring.',your_offer:'Help with hiring.'};
 let calls=0;
 const outputs=['{"signals":[]}','{"fit_score":4}','{"email":{"subject":"Hiring","body":"Can I help?"}}','{"verdict":"pass","issues":[]}'];
 const result=await skills.runFlow(m,vals,()=>{},{catalog:live,chat:async(_,opts)=>reply(outputs[calls++],.0001,opts.model)});
 assert.equal(result.status,'done',result.error);assert.equal(calls,4);
 assert.equal(result.preflightEstimate,flowPreflight(m,vals,live));assert.ok(result.preflightEstimate<.1);
 m.runtime.max_cost_per_run_usd=.001;calls=0;
 const blocked=await skills.runFlow(m,vals,()=>{},{catalog:live,chat:async()=>{calls++;return reply();}});
 assert.equal(blocked.status,'failed');assert.match(blocked.error,/Budget preflight/);assert.equal(calls,0);
});
const catalog={models:[{id:'vendor/one',promptPerMillionUsd:1,completionPerMillionUsd:2},{id:'vendor/two',promptPerMillionUsd:2,completionPerMillionUsd:3}]};
const step=(id,extra={})=>({id,model:'vendor/one',system:'inline:system {{name}}',user_template:'inline:{{name}} {{steps.first.output}}',response_format:'json',max_output_tokens:20,...extra});
const manifest=(steps=[step('first'),step('second')],extra={})=>({runtime:{steps,max_cost_per_run_usd:1,timeout_s:180,...extra}});
const reply=(content='{"ok":true}',cost=.00001,model='vendor/one')=>({content,receipt:{requested:model,prompt_tokens:10,completion_tokens:5,estCost:cost}});

test('flow defaults omitted or zero max_output_tokens to 2048 for estimates and requests',async()=>{
 const {flowPreflight}=await import('../js/flow.js');
 for(const value of [undefined,0]){
  const m=manifest([step('first',{max_output_tokens:value})]);let tokens;
  assert.equal(flowPreflight(m,{},catalog),flowPreflight(manifest([step('first',{max_output_tokens:2048})]),{},catalog));
  const result=await skills.runFlow(m,{},()=>{},{catalog,chat:async(_,opts)=>{tokens=opts.maxTokens;return reply();}});
  assert.equal(result.status,'done');assert.equal(tokens,2048);
 }
});
test('per-call estimate refuses unaffordable HTTP fallback and JSON repair without another request',async()=>{
 const expensive={models:[...catalog.models,{id:'vendor/expensive',promptPerMillionUsd:100,completionPerMillionUsd:100}]};
 for(const kind of ['fallback','repair']){
  let calls=0;
  const m=manifest([step('first',{fallback:['vendor/expensive']})],{max_cost_per_run_usd:.0002});
  const result=await skills.runFlow(m,{},()=>{},{catalog:expensive,chat:async()=>{
   calls++;
   if(kind==='fallback')throw Object.assign(new Error('unavailable'),{status:503});
   return reply('invalid',.00018);
  }});
  assert.equal(result.status,'failed');assert.match(result.error,/budget estimate exceeded/);assert.equal(calls,1);
  assert.equal(result.steps.first.attempts.length,1);assert.ok(result.estCost>0);
 }
});

test('ordered flow renders system and user with prior raw outputs without prototype traversal',async()=>{
  assert.equal(typeof skills.runFlow,'function');
  const seen=[],events=[];
  const result=await skills.runFlow(manifest(),{name:'Ada'},e=>events.push(e),{catalog,chat:async(messages,opts)=>{seen.push({messages,opts});return reply();}});
  assert.equal(result.status,'done');
  assert.equal(seen[0].messages[0].content,'system Ada');
  assert.equal(seen[1].messages[1].content,'Ada {"ok":true}');
  assert.equal(result.steps.first.json.ok,true);
  assert.equal(result.steps.first.output,'{"ok":true}');
  assert.deepEqual(events.map(e=>e.status),['waiting','waiting','running','done','running','done']);
  assert.equal(skills.renderTemplate('{{ x }}:{{steps.first.output}}:{{missing}}:{{constructor.name}}',{x:3,steps:result.steps}),'3:{"ok":true}::');
});

test('loader falls back only on 404 and retains legacy prompts for runner', async () => {
  assert.equal(typeof skills.loadSkill, 'function');
  const calls=[];
  const fetcher=async url=>{calls.push(url);return url.endsWith('flow.json')?{status:404,ok:false}:url.endsWith('skill.json')?{ok:true,json:async()=>({entry:{system:'inline:system',user_template:'prompts/user.md'}})}:{ok:true,text:async()=>'legacy {{topic}}'};};
  const loaded=await skills.loadSkill('legacy',fetcher);
  assert.equal(loaded.manifest.prompts['prompts/user.md'],'legacy {{topic}}');
  assert.equal(calls.length,3);
  await assert.rejects(skills.loadSkill('bad',async()=>({ok:false,status:500})),/500/);
});

 test('JSON fence parsing and same-model repair account for both attempts; second invalid JSON fails without fallback',async()=>{
  let calls=0;const seen=[];
  const repaired=await skills.runFlow(manifest([step('first',{fallback:['vendor/two']})]),{},()=>{},{catalog,chat:async(m,o)=>{seen.push({m:structuredClone(m),o});return reply(++calls===1?'not json':'```json\n{"ok":true}\n```',.01);}});
  assert.equal(repaired.status,'done');assert.equal(calls,2);assert.equal(repaired.estCost,.02);
  assert.equal(repaired.steps.first.attempts.length,2);assert.equal(seen[1].o.model,'vendor/one');
  assert.match(seen[1].m.at(-1).content,/Return valid JSON only\./);
  calls=0;const events=[];
  const failed=await skills.runFlow(manifest(),{},e=>events.push(e),{catalog,chat:async()=>{calls++;return reply('invalid',.01);}});
  assert.equal(failed.status,'failed');assert.equal(calls,2);assert.equal(failed.estCost,.02);
  assert.equal(events.at(-1).status,'skipped');
 });
 test('HTTP fallback uses actual model; auth aborts without fallback',async()=>{
  const models=[];const m=manifest([step('first',{fallback:['vendor/two']})]);
  const result=await skills.runFlow(m,{},()=>{},{catalog,chat:async(_,o)=>{models.push(o.model);if(models.length===1)throw Object.assign(new Error('unavailable'),{status:503});return reply('{"ok":true}',.001,'vendor/two');}});
  assert.equal(result.status,'done');assert.deepEqual(models,['vendor/one','vendor/two']);assert.equal(result.steps.first.receipt.requested,'vendor/two');
  let calls=0;const failed=await skills.runFlow(m,{},()=>{},{catalog,chat:async()=>{calls++;throw Object.assign(new Error('auth'),{status:401});}});
  assert.equal(failed.status,'failed');assert.equal(calls,1);
 });
test('budget preflight blocks low caps, unknown pricing, auto, missing prompts before any call',async()=>{
 let calls=0; const chat=async()=>{calls++;return reply();};
 for(const m of [manifest(undefined,{max_cost_per_run_usd:.001}),manifest([step('first',{model:'auto'})]),manifest([step('first',{fallback:['missing/model']})]),manifest([step('first',{system:'missing.md'})])]){
  const result=await skills.runFlow(m,{name:'x'.repeat(5000)},()=>{},{catalog,chat});
  assert.equal(result.status,'failed');
 }
 assert.equal(calls,0);
 const broken={models:[{id:'vendor/one',promptPerMillionUsd:1}]};
 const result=await skills.runFlow(manifest(),{},()=>{},{catalog:broken,chat});
 assert.equal(result.status,'failed');assert.equal(calls,0);
});
test('actual estimates stop next call after cap exceeded or usage cost becomes unknown, including repair',async()=>{
 let calls=0; const result=await skills.runFlow(manifest(),{},()=>{},{catalog,chat:async()=>{calls++;return reply('invalid',2);}});
 assert.equal(calls,1);assert.equal(result.estCost,2);assert.equal(result.status,'failed');
 calls=0;const unknown=await skills.runFlow(manifest(),{},()=>{},{catalog,chat:async()=>{calls++;return reply('{"ok":true}',null);}});
 assert.equal(calls,1);assert.equal(unknown.estCost,null);assert.equal(unknown.status,'failed');
});
test('stop_if ends cleanly and skips downstream; timeout prevents hanging',async()=>{
 let calls=0;const statuses=[];
 const result=await skills.runFlow(manifest([step('first',{stop_if:{field:'fit_score',lt:3,message:'Weak fit'}}),step('second')]),{},e=>statuses.push(e.status),{catalog,chat:async()=>{calls++;return reply('{"fit_score":2}');}});
 assert.equal(result.status,'stopped');assert.equal(result.message,'Weak fit');assert.equal(calls,1);assert.equal(statuses.at(-1),'skipped');
});
test('stop_if accepts finite numeric strings without coercing blank or nonnumeric JSON values',async()=>{
 const cases=[
  ['2','stopped',1],[' 2 ','stopped',1],['2.5','stopped',1],
  ['3','done',2],['4','done',2],[2,'stopped',1],[4,'done',2],
  ['', 'done',2],['   ','done',2],['not a score','done',2],
  ['NaN','done',2],['Infinity','done',2],[null,'done',2],
  [false,'done',2],[[], 'done',2],[{},'done',2],[undefined,'done',2]
 ];
 for(const [score,status,expectedCalls] of cases){
  let calls=0;
  const m=manifest([step('first',{stop_if:{field:'fit_score',lt:3,message:'Weak fit'}}),step('second')]);
  const result=await skills.runFlow(m,{},()=>{},{catalog,chat:async()=>{
   calls++;return reply(calls===1?JSON.stringify({fit_score:score}):'{"ok":true}');
  }});
  assert.equal(result.status,status,`score ${JSON.stringify(score)}`);
  assert.equal(calls,expectedCalls,`score ${JSON.stringify(score)}`);
  if(status==='stopped'){
   assert.equal(result.message,'Weak fit');assert.equal(result.steps.second.status,'skipped');
   assert.equal(result.steps.first.json.fit_score,score,'Keep original parsed JSON unchanged');
  }
 }
});
test('flow timeout prevents hanging',async()=>{
 const timed=await Promise.race([skills.runFlow(manifest([step('first')],{timeout_s:.02}),{},()=>{},{catalog,chat:async()=>new Promise(()=>{})}),new Promise(resolve=>setTimeout(()=>resolve({status:'hung'}),100))]);
 assert.equal(timed.status,'failed');assert.match(timed.error,/timeout/i);assert.equal(timed.estCost,null);
});
test('chatOnce sends response_format and abort signal; legacy request remains plain; incomplete pricing is unknown',async()=>{
 const {chatOnce,estCost}=await import('../js/api.js');const {get}=await import('../js/store.js');
 const previous=globalThis.fetch;const requests=[];get().catalog=catalog;
 globalThis.fetch=async(url,opts)=>{requests.push(opts);return {ok:true,json:async()=>({model:'vendor/one',choices:[{message:{content:'{}'}}],usage:{prompt_tokens:10,completion_tokens:2}})};};
 try{
  const signal=new AbortController().signal;
  await chatOnce([{role:'user',content:'dummy'}],{model:'vendor/one',responseFormat:'json',signal});
  assert.deepEqual(JSON.parse(requests[0].body).response_format,{type:'json_object'});assert.equal(requests[0].signal,signal);
  await chatOnce([{role:'user',content:'legacy'}],{model:'vendor/one'});
  assert.equal(JSON.parse(requests[1].body).response_format,undefined);
  assert.equal(estCost({prompt_tokens:3,completion_tokens:1},{models:[{id:'vendor/one',promptPerMillionUsd:1}]},'vendor/one'),null);
 }finally{globalThis.fetch=previous;}
});
test('gallery ships four-step manifest and loads all eight prompt files without fetching inline values',async()=>{
 const {readFile}=await import('node:fs/promises');
 const m=JSON.parse(await readFile(new URL('../skills/impossibuild__prospect-to-cold-email/singular.flow.json',import.meta.url),'utf8'));
 assert.deepEqual(m.runtime.steps.map(s=>s.id),['extract','angle','write','check']);
 assert.equal(m.runtime.max_cost_per_run_usd,.1);assert.equal(m.runtime.timeout_s,180);
 const calls=[];const loaded=await skills.loadSkill('impossibuild__prospect-to-cold-email',async url=>{
  calls.push(url);const content=await readFile(new URL('..'+url,import.meta.url),'utf8');return {ok:true,json:async()=>JSON.parse(content),text:async()=>content};
 });
 assert.equal(Object.keys(loaded.prompts).length,8);assert.equal(calls.length,9);
 assert.match(loaded.prompts['prompts/3-write.user.md'],/steps.angle.output/);
});
test('each fallback gets its own same-model JSON repair allowance after HTTP failure',async()=>{
 let n=0;const models=[];
 const result=await skills.runFlow(manifest([step('first',{fallback:['vendor/two']})]),{},()=>{},{catalog,chat:async(_,o)=>{
  models.push(o.model);n++;
  if(n===1)return reply('invalid');
  if(n===2)throw Object.assign(new Error('HTTP unavailable'),{status:503});
  return reply(n===3?'invalid':'{"ok":true}',.00001,'vendor/two');
 }});
 assert.equal(result.status,'done');assert.deepEqual(models,['vendor/one','vendor/one','vendor/two','vendor/two']);
 assert.equal(result.steps.first.attempts.length,4);
});
test('manifest form attributes escape HTML, including field identifiers and numeric bounds',async()=>{
 assert.equal(typeof skills.renderField,'function');
 const html=skills.renderField({key:'x" autofocus onfocus="alert(1)',type:'number',label:'<script>',min:'" onmouseover="bad',default:'" onfocus="bad'});
 assert.ok(!html.includes('id="fld-x" autofocus'));assert.ok(!html.includes('min="" onmouseover'));
 assert.ok(!html.includes('value="" onfocus'));assert.ok(html.includes('&lt;script&gt;'));
});
test('preflight estimates normal route and validates fallback prices and repeated downstream context/output limits',async()=>{
 const {flowPreflight}=await import('../js/flow.js');
 const a=manifest([step('first')]);const base=flowPreflight(a,{},catalog);
 assert.equal(flowPreflight(manifest([step('first',{fallback:['vendor/two']})]),{},catalog),base);
 assert.throws(()=>flowPreflight(manifest([step('first',{fallback:['missing/model']})]),{},catalog),/Unknown pricing/);
 const short=flowPreflight(manifest([step('first'),step('second',{user_template:'inline:{{steps.first.output}}'})]),{},catalog);
 const repeat=flowPreflight(manifest([step('first'),step('second',{user_template:'inline:{{steps.first.output}} {{steps.first.output}}'})]),{},catalog);
 assert.ok(repeat>short);assert.ok(flowPreflight(manifest([step('first',{max_output_tokens:200}),step('second')]),{},catalog)>short);
});
test('JSON failure does not invoke fallback; missing prompt HTTP errors do not silently become prompt text',async()=>{
 let n=0;
 const result=await skills.runFlow(manifest([step('first',{fallback:['vendor/two']})]),{},()=>{},{catalog,chat:async()=>{n++;return reply('bad');}});
 assert.equal(result.status,'failed');assert.equal(n,2);assert.equal(result.steps.first.attempts.length,2);
 await assert.rejects(skills.loadSkill('x',async url=>url.endsWith('flow.json')?{ok:true,json:async()=>({runtime:{steps:[step('first',{system:'missing.md'})]}})}:{ok:false,status:404}),/prompt missing.md HTTP 404/);
});
test('flow result includes nested runtime output, repairs and unknown estimates as escaped plain text',async()=>{
 const {renderFlowResult}=await import('../js/flow-ui.js');
 const m=manifest([step('first')]);m.runtime.output={show:['first.nested.email']};
 const ctx={status:'done',estCost:null,steps:{first:{output:'<script>bad</script>',json:{nested:{email:{subject:'hello',body:'<b>plain</b>'}}},attempts:[reply().receipt,reply('bad',null).receipt]}}};
 const html=renderFlowResult(m,ctx);
 assert.match(html,/Total estimated cost: unknown/);assert.match(html,/2 attempt\(s\)/);assert.match(html,/&lt;b&gt;plain/);assert.ok(!html.includes('<script>'));assert.match(html,/data-copy=/);
});
test('HTTP error usage receipts are retained for billed attempts before fallback',async()=>{
 const {chatOnce}=await import('../js/api.js');const {get}=await import('../js/store.js');get().catalog=catalog;
 const original=globalThis.fetch;
 globalThis.fetch=async()=>({ok:false,status:503,json:async()=>({model:'vendor/one',error:{message:'unavailable'},usage:{prompt_tokens:500,completion_tokens:50,total_tokens:550}})});
 try{await assert.rejects(chatOnce([],{model:'vendor/one'}),error=>{
  assert.equal(error.receipt?.prompt_tokens,500);assert.equal(error.receipt?.estCost,.0006);return true;
 });}finally{globalThis.fetch=original;}
});