// Model Jury named code nodes. Manifests contain data, never executable code.
export function judge_family_differs_from_all_contestants(judge,contestants){
  const maker=id=>{if(typeof id!=='string' || !id.includes('/'))throw new Error('exact provider/model id required');return id.split('/')[0].toLowerCase();};
  return contestants.map(maker).includes(maker(judge)) ? [false,'Pick a judge from a different model maker than all three contestants.'] : [true,null];
}

export function at_least_2_answers(answers,need=2){return Object.values(answers).filter(a=>a && a.trim()).length>=need;}

export function shuffle_and_relabel(answers,rng=Math.random){const slots=Object.keys(answers);for(let i=slots.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[slots[i],slots[j]]=[slots[j],slots[i]];}const blinded={},map={};slots.forEach((slot,i)=>{blinded['answer_'+(i+1)]=answers[slot]?.trim()?answers[slot]:'(no answer)';map[String(i+1)]=slot;});return [blinded,map];}

export function quoteFound(quote,answer){const norm=s=>String(s||'').replace(/[‘’“”\"'`*_]/g,'').replace(/\s+/g,' ').trim().toLowerCase();const q=norm(quote);return !!q && norm(answer).includes(q);}

export function score_cost_and_rank(judge,rubric,blinded,map,costs,reversed=null){
 const weights=Object.fromEntries(rubric.criteria.map(c=>[c.name,c.weight??1]));
 const scored=j=>Object.fromEntries(j.scores.map(s=>{const qfail=[];const criteria=Object.fromEntries(s.criteria.map(c=>{let score=Math.trunc(Number(c.score));if(!quoteFound(c.quote,blinded['answer_'+s.answer])){qfail.push(c.name);score=Math.min(score,2);}return [c.name,score];}));let num=0,den=0;for(const [name,score] of Object.entries(criteria)){const w=weights[name]??1;num+=score*w;den+=w;}return [map[String(s.answer)],{avg:den?round2(num/den):null,must_haves_failed:s.must_haves_failed||[],quote_failures:qfail,criteria}];}));
 const a=scored(judge),disagreements=[];
 if(reversed){
  const b=scored(reversed);
  for(const slot of Object.keys(a)){
   if(!b[slot])continue;
   for(const [name,sa] of Object.entries(a[slot].criteria)){const sb=b[slot].criteria[name];if(sb!==undefined && Math.abs(sa-sb)>=2)disagreements.push({slot,criterion:name,scores:[sa,sb]});}
   a[slot].avg=round2((a[slot].avg+b[slot].avg)/2);
   const failures=[...new Set(a[slot].must_haves_failed)].sort(),reverseFailures=[...new Set(b[slot].must_haves_failed)].sort();
   if(JSON.stringify(failures)!==JSON.stringify(reverseFailures))disagreements.push({slot,criterion:'must_haves',scores:[failures,reverseFailures]});
   a[slot].must_haves_failed=[...new Set([...failures,...reverseFailures])].sort();
   a[slot].quote_failures=[...new Set([...a[slot].quote_failures,...b[slot].quote_failures])].sort();
  }
 }
 const ineligible=r=>!!r.must_haves_failed.length;
 const rows=Object.entries(a).map(([slot,v])=>({slot,...v,cost_usd:costs[slot]??null}));
 rows.sort((a,b)=>Number(ineligible(a))-Number(ineligible(b))||(b.avg??0)-(a.avg??0));rows.forEach((r,i)=>r.rank=i+1);
 const passing=rows.filter(r=>!ineligible(r) && r.avg!==null),best=passing[0];
 const near=best?passing.filter(r=>r.avg>=best.avg-.5 && r.cost_usd!==null):[];near.sort((a,b)=>a.cost_usd-b.cost_usd);
 return {ranking:rows,best_overall:best?.slot??null,best_value:near[0]?.slot??null,disagreements};
}

import {chatOnce} from './api.js';
import {get} from './store.js';
import {renderTemplate,promptText} from './flow.js';
export const BUILTINS=Object.freeze({judge_family_differs_from_all_contestants,at_least_2_answers,shuffle_and_relabel,score_cost_and_rank});
export async function runGraph(manifest,vals,onNode=()=>{},deps={}){
 const ctx={...vals,steps:Object.create(null),status:'running',estCost:0};
 const nodes=manifest.runtime.graph,chat=deps.chat||chatOnce,catalog=deps.catalog||get().catalog,cap=manifest.runtime.max_cost_per_run_usd;
 const emit=(n,status)=>{ctx.steps[n.id].status=status;onNode({id:n.id,...ctx.steps[n.id]});};
 for(const n of nodes)ctx.steps[n.id]={output:'',json:null,status:'waiting',attempts:[],receipt:null};
 try{ctx.preflightEstimate=graphPreflight(manifest,vals,catalog);}catch(error){ctx.status='failed';ctx.error=error.message;for(const n of nodes)emit(n,'skipped');return ctx;}
 const answers=()=>Object.fromEntries(['slot_1','slot_2','slot_3'].map(id=>[id,ctx.steps[id]?.output||'']));
 const account=(state,receipt)=>{
  if(!deps.chat && receipt && knownCost(receipt.prompt_tokens) && knownCost(receipt.completion_tokens)){
   // The legacy client strips colon suffixes for its own pricing. Graph IDs
   // are exact catalog identifiers, so reconcile only graph usage here.
   let exact=null;try{const p=price(catalog,receipt.requested);exact=(receipt.prompt_tokens*p.promptPerMillionUsd+receipt.completion_tokens*p.completionPerMillionUsd)/1e6;}catch{}receipt={...receipt,estCost:exact};
  }
  state.receipt=receipt;state.attempts.push(receipt);ctx.estCost=knownCost(ctx.estCost)&&knownCost(receipt?.estCost)?ctx.estCost+receipt.estCost:null;};
 let reserved=0;
 const deadline=Date.now()+Math.min(manifest.runtime.timeout_s||180,180)*1000;
 const timedChat=async(messages,opts)=>{const controller=new AbortController();let timer;try{return await Promise.race([chat(messages,{...opts,signal:controller.signal}),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(new Error('Graph timeout; upstream billing may be unknown'));},Math.max(0,deadline-Date.now()));})]);}finally{clearTimeout(timer);}};
 const execute=async(n,call=null)=>{
  const state=ctx.steps[n.id];emit(n,'running');
  try{
   if(n.node==='model'){
    if(!knownCost(ctx.estCost) || ctx.estCost+reserved>cap)throw Object.assign(new Error('Run budget exceeded or cost unknown; no further calls'),{beforeCall:true});
    let result;
    try{result=await timedChat(call.messages,{model:vals[n.model_from_input],maxTokens:n.max_output_tokens,responseFormat:n.response_format});}
    catch(error){account(state,error.receipt||{requested:vals[n.model_from_input],estCost:error.status?call.estimate:null,httpStatus:error.status??null,caveat:'Failed request: conservative estimate, usage unknown'});throw error;}
    state.output=result.content;account(state,result.receipt);
    if(!knownCost(ctx.estCost) || ctx.estCost>cap)throw new Error('Run budget exceeded or cost unknown; no further calls');
    state.json=n.response_format==='json'?JSON.parse(result.content):null;
    if(n.id==='rubric'){
     const criteria=state.json?.criteria;
     if(!Array.isArray(criteria)||!criteria.length||criteria.some(c=>typeof c.name!=='string'||!c.name.trim()||![1,2,3].includes(c.weight??1))||new Set(criteria.map(c=>c.name)).size!==criteria.length||!Array.isArray(state.json.must_haves??[]))throw new Error('Invalid rubric JSON: unique criteria and weights 1–3 required');
    }
    if(n.id==='judge' || n.id==='judge_reversed'){
     const names=ctx.steps.rubric.json.criteria.map(c=>c.name),labels=new Set();
     const invalid=()=>{throw new Error('Invalid judge JSON: labels, criteria, scores or coverage');};
     if(!Array.isArray(state.json?.scores))invalid();
     for(const s of state.json.scores){const label=String(s.answer);if(!['1','2','3'].includes(label)||labels.has(label)||!Array.isArray(s.criteria)||!Array.isArray(s.must_haves_failed??[]))invalid();labels.add(label);if(!answers()[ctx.steps.blind.private_map[label]]?.trim())continue;const cn=s.criteria.map(c=>c.name);if(cn.length!==names.length || new Set(cn).size!==names.length || cn.some(name=>!names.includes(name)))invalid();for(const c of s.criteria){const num=typeof c.score==='number'||typeof c.score==='string'&&c.score.trim()?Number(c.score):NaN;if(!Number.isInteger(num)||num<1||num>5)invalid();}}
     for(const [label,slot] of Object.entries(ctx.steps.blind.private_map))if(answers()[slot]?.trim()&&!labels.has(label))invalid();
    }
   }else{
    switch(n.rule){
     case 'judge_family_differs_from_all_contestants':{const [ok,message]=BUILTINS[n.rule](vals.judge,[vals.contestant_1,vals.contestant_2,vals.contestant_3]);state.json={ok};if(!ok){ctx.status='stopped';ctx.message=message;}break;}
     case 'at_least_2_answers':state.json={ok:BUILTINS[n.rule](answers())};if(!state.json.ok){ctx.status='stopped';ctx.message=n.message;}break;
     case 'shuffle_and_relabel':{const [blinded,map]=BUILTINS[n.rule](answers(),deps.rng);Object.assign(state,blinded,{private_map:map});state.json=blinded;break;}
     case 'score_cost_and_rank':{const valid=j=>j?{...j,scores:j.scores.filter(s=>answers()[ctx.steps.blind.private_map[String(s.answer)]]?.trim())}:null;state.json=BUILTINS[n.rule](valid(ctx.steps.judge.json),ctx.steps.rubric.json,ctx.steps.blind.json,ctx.steps.blind.private_map,Object.fromEntries(Object.keys(answers()).map(id=>[id,ctx.steps[id].receipt?.estCost??null])),valid(ctx.steps.judge_reversed?.json));break;}
    }
    state.output=JSON.stringify(state.json);
   }
   emit(n,'done');
  }catch(error){state.error=error.message;
   if(error.beforeCall || !knownCost(ctx.estCost) || ctx.estCost>cap || n.on_fail!=='continue_as_no_answer'){ctx.status='failed';ctx.error=error.message;}else state.output='';emit(n,'failed');
  }finally{if(call)reserved=Math.max(0,reserved-call.estimate);}
 };
 for(let index=0;index<nodes.length;index++){
  const n=nodes[index];
  if(ctx.status!=='running' || (n.when && !vals[n.when])){emit(n,'skipped');continue;}
  let batch=[n];
  if(n.parallel_group){while(index+1<nodes.length && nodes[index+1].parallel_group===n.parallel_group)batch.push(nodes[++index]);}
  if(n.node!=='model'){await execute(n);continue;}
  const calls=batch.map(node=>{const messages=messagesFor(manifest,node,ctx);return {messages,estimate:estimate(catalog,vals[node.model_from_input],messages,node.max_output_tokens)};});
  const reservation=calls.reduce((sum,c)=>sum+c.estimate,0);
  if(!knownCost(ctx.estCost) || ctx.estCost+reserved+reservation>cap){ctx.status='failed';ctx.error='Run budget exceeded or cost unknown; group refused before calls';for(const node of batch)emit(node,'skipped');continue;}
  reserved+=reservation;
  // All estimates reserved synchronously before any gateway call begins.
  await Promise.allSettled(batch.map((node,i)=>execute(node,calls[i])));
 }
 if(ctx.status==='running')ctx.status='done';return ctx;
}
const utf8=text=>new TextEncoder().encode(text).length;
const knownCost=v=>typeof v==='number' && Number.isFinite(v) && v>=0;
export function routableModels(catalog){return (catalog?.models||[]).filter(m=>m.kind==='chat' && m.routable===true && typeof m.id==='string' && /^[^\s/]+\/\S+$/.test(m.id) && !/(^|\/)(auto|router)$/i.test(m.id) && !/-latest$/i.test(m.id));}
function price(catalog,id){
 const p=routableModels(catalog).find(m=>m.id===id);
 if(!p)throw new Error('Exact routable chat model required: '+id);
 if(![p.promptPerMillionUsd,p.completionPerMillionUsd].every(knownCost))throw new Error('Unknown pricing: '+id);
 return p;
}
function estimate(catalog,id,messages,max){const p=price(catalog,id);return ((Math.ceil(messages.reduce((n,m)=>n+utf8(m.content),0)/4)+128)*p.promptPerMillionUsd+max*p.completionPerMillionUsd)/1e6;}
function messagesFor(manifest,node,ctx){
 // Only task data, rubric text and anonymous answers enter template scope.
 // Selected identities, receipts and the private map are deliberately absent.
 const safe={task:ctx.task??'',context:ctx.context??'',criteria:ctx.criteria??'',steps:{rubric:{output:ctx.steps.rubric?.output??''},blind:Object.fromEntries([1,2,3].map(i=>['answer_'+i,ctx.steps.blind?.['answer_'+i]??'']))}};
 return [{role:'system',content:renderTemplate(promptText(manifest,node.system),safe)},{role:'user',content:renderTemplate(promptText(manifest,node.user_template),safe)}];
}
export function graphPreflight(manifest,vals,catalog){
 const runtime=manifest.runtime;
 if(!knownCost(runtime?.max_cost_per_run_usd))throw new Error('Numeric run estimate cap required');
 const bounds={...vals,steps:Object.create(null)},ids=new Set();let total=0;
 for(const n of runtime.graph){
  if(typeof n.id!=='string' || !/^[\w-]+$/.test(n.id) || ['constructor','prototype','__proto__'].includes(n.id) || ids.has(n.id))throw new Error('Invalid or duplicate graph node');ids.add(n.id);
  if(!['model','rule','merge'].includes(n.node) || (n.node!=='model' && !Object.hasOwn(BUILTINS,n.rule)))throw new Error('Unknown code builtin or node type');
  if(n.node==='model'){
   if(!Number.isInteger(n.max_output_tokens) || n.max_output_tokens<1 || n.max_output_tokens>100000)throw new Error('Finite max_output_tokens required');
   price(catalog,vals[n.model_from_input]);
   if(!n.when || vals[n.when])total+=estimate(catalog,vals[n.model_from_input],messagesFor(manifest,n,bounds),n.max_output_tokens);
   bounds.steps[n.id]={output:'x'.repeat(n.max_output_tokens*4)};
  }else if(n.rule==='shuffle_and_relabel')bounds.steps[n.id]=Object.fromEntries([1,2,3].map(i=>['answer_'+i,bounds.steps['slot_'+i]?.output||'']));
 }
 if(total>runtime.max_cost_per_run_usd)throw new Error('Budget preflight estimate exceeds cap');return total;
}

// Python round(x, 2): round the actual binary64 rational, ties to even.
function round2(value){
 const view=new DataView(new ArrayBuffer(8));view.setFloat64(0,Math.abs(value));const bits=view.getBigUint64(0),exp=Number((bits>>52n)&2047n);
 let numerator=((bits&((1n<<52n)-1n))+(exp?1n<<52n:0n))*100n;
 const shift=exp?exp-1075:-1074;
 if(shift>=0)return Math.sign(value)*Number(numerator<<BigInt(shift))/100;
 const denominator=1n<<BigInt(-shift),q=numerator/denominator,remainder=numerator%denominator;
 const up=remainder*2n>denominator || remainder*2n===denominator && q%2n===1n;
 return Math.sign(value)*Number(q+(up?1n:0n))/100;
}
