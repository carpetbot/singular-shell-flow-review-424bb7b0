import { chatOnce } from './api.js';
import { get } from './store.js';

export function readPath(ctx, path){
  let value=ctx;
  for(const key of path.split('.')){
    if(['__proto__','prototype','constructor'].includes(key) || value == null || !Object.hasOwn(Object(value),key)) return undefined;
    value=value[key];
  }
  return value;
}
export function renderTemplate(tpl, ctx){
  return String(tpl).replace(/\{\{\s*([\w.]+)\s*\}\}/g,(_,key)=>String(readPath(ctx,key) ?? ''));
}
export function promptText(manifest,path){
  if(typeof path!=='string') throw new Error('Missing prompt template');
  if(path.startsWith('inline:')) return path.slice(7);
  if(!Object.hasOwn(manifest.prompts || {},path)) throw new Error(`Missing prompt template: ${path}`);
  return manifest.prompts[path];
}
// Estimate input tokens as UTF-8 bytes / 4 plus framing tokens. Downstream
// output placeholders use 4 bytes/token. Neither is a billing guarantee.
const bytes = text => new TextEncoder().encode(text).length;
function modelPrice(catalog,id){
  if(typeof id!=='string' || !/^[\w.-]+\/[\w.-]+$/.test(id)) throw new Error('Exact non-auto model ID required');
  const p=catalog?.models?.find(m=>m.id===id);
  if(!p || ![p.promptPerMillionUsd,p.completionPerMillionUsd].every(v=>typeof v==='number' && Number.isFinite(v) && v>=0)) throw new Error(`Unknown pricing: ${id}`);
  return p;
}
function callEstimate(catalog,id,inputBytes,maxOutput){
  const p=modelPrice(catalog,id);
  return ((Math.ceil(inputBytes/4)+128)*p.promptPerMillionUsd+maxOutput*p.completionPerMillionUsd)/1e6;
}
export function flowPreflight(manifest,vals,catalog){
  const runtime=manifest.runtime;
  if(!Number.isFinite(runtime?.max_cost_per_run_usd) || runtime.max_cost_per_run_usd<0) throw new Error('Run estimate ceiling required');
  const bounds={...vals,steps:Object.create(null)};let estimate=0;
  const ids=new Set();
  for(const s of runtime.steps){
    if(!/^[\w-]+$/.test(s.id) || ['constructor','prototype','__proto__'].includes(s.id) || ids.has(s.id)) throw new Error('Invalid or duplicate step ID');
    ids.add(s.id);
    const maxOutput=s.max_output_tokens || 2048;
    if(!Number.isInteger(maxOutput) || maxOutput<1 || maxOutput>100000) throw new Error('Finite max_output_tokens required');
    const size=[s.system,s.user_template].map(p=>bytes(renderTemplate(promptText(manifest,p),bounds))).reduce((a,b)=>a+b,0);
    // Validate every candidate up front; mutually exclusive fallbacks and
    // conditional repairs are guarded when needed, not reserved in preflight.
    for(const id of [s.model,...(s.fallback || [])]) modelPrice(catalog,id);
    estimate+=callEstimate(catalog,s.model,size,maxOutput);
    // Include each reference separately when later templates are rendered.
    bounds.steps[s.id]={output:'x'.repeat(maxOutput*4)};
  }
  if(estimate>runtime.max_cost_per_run_usd) throw new Error(`Budget preflight: estimated ${estimate} exceeds ${runtime.max_cost_per_run_usd}`);
  return estimate;
}
export async function runFlow(manifest, vals, onStep=()=>{}, deps={}){
  const chat=deps.chat || chatOnce;
  const ctx={...vals,steps:Object.create(null),status:'running',estCost:0};
  const steps=manifest.runtime.steps;
  const deadline=Date.now()+Math.min(manifest.runtime.timeout_s || 180,180)*1000;
  const timedChat=async(messages,opts)=>{
    const controller=new AbortController();let timer;
    try{
      return await Promise.race([chat(messages,{...opts,signal:controller.signal}),new Promise((_,reject)=>{
        timer=setTimeout(()=>{controller.abort();reject(new Error('Flow timeout; upstream charge may be unknown'));},Math.max(0,deadline-Date.now()));
      })]);
    }finally{clearTimeout(timer);}
  };
  const catalog=deps.catalog || get().catalog;
  const cap=manifest.runtime.max_cost_per_run_usd;
  const emit=(s,status)=>{ctx.steps[s.id].status=status;onStep({id:s.id,...ctx.steps[s.id],status});};
  for(const s of steps){ctx.steps[s.id]={output:'',json:null,receipt:null,attempts:[]};emit(s,'waiting');}
  try{ctx.preflightEstimate=flowPreflight(manifest,vals,catalog);}
  catch(error){ctx.status='failed';ctx.error=error.message;for(const s of steps)emit(s,'skipped');return ctx;}
  const account=(state,receipt)=>{
    state.attempts.push(receipt);state.receipt=receipt;
    const cost=receipt?.estCost;
    ctx.estCost=ctx.estCost!==null && typeof cost==='number' && Number.isFinite(cost) && cost>=0 ? ctx.estCost+cost : null;
  };
  for(const s of steps){
    if(ctx.status!=='running'){emit(s,'skipped');continue;}
    emit(s,'running');
    try{
      const messages=[{role:'system',content:renderTemplate(promptText(manifest,s.system),ctx)},{role:'user',content:renderTemplate(promptText(manifest,s.user_template),ctx)}];
      const maxOutput=s.max_output_tokens || 2048;
      const models=[s.model,...(s.fallback || [])];let modelIndex=0;
      for(let repair=0;repair<2;repair++){
        let result;
        while(!result){
          const estimate=callEstimate(catalog,models[modelIndex],messages.reduce((n,m)=>n+bytes(m.content),0),maxOutput);
          if(ctx.estCost===null || ctx.estCost+estimate>cap) throw new Error('Run budget estimate exceeded or cost unknown; no further calls');
          try{ result=await timedChat(messages,{model:models[modelIndex],maxTokens:maxOutput,responseFormat:s.response_format}); }
          catch(error){
            account(ctx.steps[s.id],error.receipt || {requested:models[modelIndex],estCost:error.status?estimate:null,caveat:'Failed attempt: conservative estimate, no usage receipt',httpStatus:error.status});
            if(!error.status || [401,402,403].includes(error.status) || error.kind==='balance' || modelIndex===models.length-1) throw error;
            modelIndex++;repair=0;
          }
        }
        const state=ctx.steps[s.id];
        state.output=result.content;account(state,result.receipt);
        if(ctx.estCost===null || ctx.estCost>cap) throw new Error('Run budget estimate exceeded or cost unknown; no further calls');
        try{
          state.json=s.response_format==='json' ? JSON.parse(result.content.trim().replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'')) : null;
          break;
        }catch(error){
          if(repair===1) throw new Error('Invalid JSON after repair');
          if(messages.at(-1).content!=='Return valid JSON only.') messages.push({role:'user',content:'Return valid JSON only.'});
        }
      }
      emit(s,'done');
      const stop=s.stop_if;const value=stop && readPath(ctx.steps[s.id].json,stop.field);
      if(stop && typeof value==='number' && value<stop.lt){ctx.status='stopped';ctx.message=stop.message;}
    }catch(error){ctx.status='failed';ctx.error=error.message;ctx.steps[s.id].error=error.message;emit(s,'failed');}
  }
  if(ctx.status==='running') ctx.status='done';
  return ctx;
}
