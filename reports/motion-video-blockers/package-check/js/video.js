// Motion Trimmer → Video v1. No implicit paid generation or model fallback.
export const MODELS=Object.freeze([
 {id:'alibaba/wan-3.0/text-to-video',resolution:'720p',name:'Wan 3.0 · quality'},
 {id:'minimax/h3-max-turbo',resolution:'768p',name:'MiniMax H3 Max Turbo · budget'}
]);
// June must confirm actual gateway request names before release. Never guess.
export const FIELDS=Object.freeze({duration:null,aspectRatio:null,audio:null});
export const releaseReady=(fields=FIELDS)=>typeof fields.duration==='string' && /^[a-zA-Z_][\w]*$/.test(fields.duration) && !['model','prompt','resolution','__proto__','constructor','prototype'].includes(fields.duration);
export function quoteVideo(catalog,model,duration){
 const choice=MODELS.find(m=>m.id===model);
 if(!choice||![5,10,15].includes(duration))throw new Error('Unsupported video configuration');
 const m=catalog?.models?.find(m=>m.id===model);
 const configs=m?.videoPricing?.configs?.filter(c=>c.duration===duration && c.resolution===choice.resolution && (c.mode==null||c.mode==='text_to_video') && c.audio==null);
 if(m?.kind!=='video'||m.routable!==true||m.videoPricing?.exact!==true||configs?.length!==1||typeof configs[0].priceUsd!=='number'||!Number.isFinite(configs[0].priceUsd)||configs[0].priceUsd<0)throw new Error('Exact video price unavailable; generation blocked');
 return {model,duration,resolution:choice.resolution,price:configs[0].priceUsd,as_of:catalog.as_of};
}
export function videoBody({model,prompt,duration},fields=FIELDS){
 const choice=MODELS.find(m=>m.id===model);
 if(!choice||![5,10,15].includes(duration)||typeof prompt!=='string'||!prompt.trim()||prompt.length>12000)throw new Error('Invalid video request');
 const body={model,prompt,resolution:choice.resolution};
 if(releaseReady(fields))body[fields.duration]=duration;
 return body;
}

const finite=n=>typeof n==='number'&&Number.isFinite(n)&&n>=0;
const text=(s,max=4000)=>typeof s==='string'&&s.trim().length>0&&s.length<=max;
export function validatePlan(p,duration){
 if(![5,10,15].includes(duration)||!p||!Array.isArray(p.shotbeats)||!p.shotbeats.length||p.shotbeats.length>15||!text(p.prompt,12000)||p.prompt.trim().split(/\s+/).length>120||!Array.isArray(p.overlays)||p.overlays.length>30||!Array.isArray(p.dropped)||p.dropped.length>30)throw new Error('Invalid planner JSON');
 if(p.shotbeats.some(b=>!b||!finite(b.duration_s)||b.duration_s<=0||!text(b.description))||Math.abs(p.shotbeats.reduce((s,b)=>s+b.duration_s,0)-duration)>.001)throw new Error('Shot durations must sum to selected duration');
 if(p.overlays.some(o=>!o||!finite(o.at_s)||o.at_s>=duration||!text(o.text,500))||p.dropped.some(d=>!text(d)))throw new Error('Invalid overlays or dropped details');
 return p;
}
export async function planVideo(brief,{chat,catalog,signal}){
 const receipts=[];const models=['anthropic/claude-sonnet-5.5','deepseek/deepseek-v4.1-flash-1017'];
 const messages=[{role:'system',content:'Return JSON only: {"shotbeats":[{"duration_s":5,"description":"visual beat"}],"prompt":"one scene description, max 120 words","overlays":[{"at_s":0,"text":"editor text"}],"dropped":["unsupported asset or detail"]}. Shot durations must sum to the selected duration. Preserve beat order. Do not render words, logos, UI or on-screen text in the video prompt; return every text line only in overlays for a human editor. Mark unsupported asset/logo requirements and precise easing/cuts in dropped; no uploaded assets exist. Describe subject, setting, camera motion, lighting, colour and pacing. Platform is creative context only, not guaranteed framing. No automatic composition.'},{role:'user',content:JSON.stringify(brief)}];
 if(!text(brief.topic)||![5,10,15].includes(brief.duration))throw new Error('Topic and supported duration required');
 const tokens=Math.ceil(JSON.stringify(messages).length/4)+100;
 for(const id of models){const m=catalog?.models?.find(m=>m.id===id);if(m?.kind!=='chat'||m.routable!==true||!finite(m.promptPerMillionUsd)||!finite(m.completionPerMillionUsd)||(tokens*m.promptPerMillionUsd+1200*m.completionPerMillionUsd)/1e6>.1)throw new Error('Planner price unavailable or estimate exceeds $0.10 per attempt');}
 for(const [i,model] of models.entries()){
  try{
   const result=await chat(messages,{model,maxTokens:1200,responseFormat:'json',signal});
   receipts.push({model,...result.receipt,estCost:finite(result.receipt?.estCost)?result.receipt.estCost:null});
   return {plan:validatePlan(JSON.parse(result.content),brief.duration),receipts};
  }catch(e){
   if(receipts.length<=i)receipts.push({model,...e.receipt,estCost:finite(e.receipt?.estCost)?e.receipt.estCost:null,error:'Planner attempt failed; charge unknown without usage'});
   if(i===0&&e.status>=500&&e.status<=599)continue;
   e.receipts=receipts;throw e;
  }
 }
}

const RECOVERY='motion-video.v1';
const jobId=id=>typeof id==='string'&&/^[A-Za-z0-9_-]{1,160}$/.test(id);
async function digest(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(b=>b.toString(16).padStart(2,'0')).join('');}
export class VideoSession{
 constructor({key,fetcher=fetch,storage=localStorage,fields=FIELDS,onChange=()=>{},urlAPI=URL,locks=globalThis.navigator?.locks}){
  this.locks=locks;
  this.urlAPI=urlAPI;this.blobURL=null;this.stopped=false;this.key=key.trim();this.fetcher=(...args)=>fetcher(...args);this.storage=storage;this.fields=fields;this.onChange=onChange;this.busy=false;
  try{this.records=JSON.parse(storage.getItem(RECOVERY)||'[]');if(!Array.isArray(this.records)||this.records.some(r=>!r||typeof r.token!=='string'||(r.id&&!jobId(r.id))))throw new Error();}catch{this.records=[];this.recoveryError=true;}
  this.record=this.records.at(-1)||null;
 }
 async exclusive(fn){
  if(!this.locks?.request)throw new Error('Safe cross-tab lock unavailable; generation blocked');
  return this.locks.request(RECOVERY,{mode:'exclusive'},fn);
 }
 refresh(){
  const previous=this.records.at(-1)?.token,selected=this.record?.token;
  let records;
  try{records=JSON.parse(this.storage.getItem(RECOVERY)||'[]');if(!Array.isArray(records)||records.some(r=>!r||typeof r.token!=='string'||(r.id&&!jobId(r.id))))throw new Error();}
  catch{this.recoveryError=true;throw new Error('Recovery references unreadable; resolve before a new paid generation');}
  this.records=records;
  // A newly persisted logical run supersedes any stale selection/new-version intent.
  this.record=records.at(-1)?.token!==previous?records.at(-1)||null:selected?records.find(r=>r.token===selected)||records.at(-1)||null:null;
 }
 async save(underLock=false){
  const write=()=>{
   const updated=this.record;
   this.refresh();
   if(updated){const i=this.records.findIndex(r=>r.token===updated.token);if(i<0)this.records.push(updated);else this.records[i]=updated;this.record=updated;}
   this.storage.setItem(RECOVERY,JSON.stringify(this.records));this.onChange(this.record);
  };
  return underLock?write():this.exclusive(write);
 }
 async guardPending(exceptToken=null){
  const keyHash=await digest(this.key);
  if(this.records.some(r=>r.keyHash===keyHash&&r.token!==exceptToken&&!['completed','failed','rejected'].includes(r.status)))throw new Error('Resolve the existing pending or uncertain job first');
 }
 async sameKey(){if(!this.key||this.record&&this.record.keyHash!==await digest(this.key))throw new Error('Use the same creating key in Settings');}
 async create(spec,approvedPrice){
  if(this.busy)return;this.busy=true;
  try{return await this.exclusive(async()=>{
   this.refresh();
   if(!releaseReady(this.fields))throw new Error('Release gate: duration field unconfirmed; real generation disabled');
   if(this.recoveryError)throw new Error('Recovery references unreadable; resolve before a new paid generation');
   await this.sameKey();
   await this.guardPending(this.record?.token);
   if(this.record?.id)throw new Error('Resume existing job; new generation requires explicit new version');
   const body=JSON.stringify(videoBody(spec,this.fields)),bodyHash=await digest(body);
   if(this.record&&this.record.bodyHash!==bodyHash)throw new Error('Uncertain request: re-enter the identical prompt and configuration to retry');
   const pricing=await this.request('/pricing.json',{},false);const quote=quoteVideo(pricing,spec.model,spec.duration);
   if(quote.price!==approvedPrice)throw new Error('Price changed; review a fresh quote before approving');
   if(!this.record){
    if(this.records.length>=20)throw new Error('Recovery history full; review saved jobs before removing history');
    // One persisted plan/version identity is shared under the origin lock.
    // Intentional regeneration gets a new identity only after terminal history.
    const planId=crypto.randomUUID();
    const token=await digest(JSON.stringify({planId,model:spec.model,prompt:spec.prompt,duration:spec.duration,resolution:quote.resolution}));
    this.record={planId,token,bodyHash,keyHash:await digest(this.key),quote,settled:null,status:'creating',id:null};this.records.push(this.record);
   }
   // Persist before POST. A lost response must never create a fresh logical run.
   this.record.status='creating';await this.save(true);
   try{
    const job=await this.request('/v1/videos',{method:'POST',headers:{'Idempotency-Key':this.record.token,'Content-Type':'application/json'},body});
    if(!jobId(job.id)||!['queued','processing','completed','failed'].includes(job.status))throw new Error('Invalid create response');
    this.record.id=job.id;this.record.status=job.status;await this.save(true);return job;
   }catch(e){const rejected=[401,402].includes(e.status);this.record.status=rejected?'rejected':'uncertain';this.record.settled=rejected?0:null;this.record.error=rejected?(e.status===401?'authentication_rejected':'credit_rejected'):null;await this.save(true);throw e;}
  });}finally{this.busy=false;}
 }
 async request(path,opts={},auth=true){
  let r;try{r=await this.fetcher(path,{...opts,signal:opts.signal||AbortSignal.timeout(30000),redirect:'error',cache:'no-store',headers:{...opts.headers,...(auth?{Authorization:'Bearer '+this.key}:{})}});}catch{throw Object.assign(new Error('Network unavailable; request outcome may be unknown'),{kind:'network'});}
  if(!r.ok)throw Object.assign(new Error(r.status===401?'Authentication failed; check the creating key':r.status===402?'Insufficient credits':r.status===404?'Job not found for the creating key':r.status===502?'Content temporarily unavailable; retry download only':'Gateway HTTP '+r.status),{status:r.status,kind:r.status===401?'auth':r.status===402?'credit':'gateway'});
  return r.json();
 }
 async resume({sleep=ms=>new Promise(r=>setTimeout(r,ms)),deadlineMs=180000,now=()=>Date.now()}={}){
  await this.sameKey();if(!this.record?.id)throw new Error('Uncertain creation: re-enter identical request and retry with saved idempotency token');
  if(this.polling)return;this.polling=true;this.stopped=false;this.pollAbort=new AbortController();const until=now()+Math.min(deadlineMs,180000);let delay=1000;
  try{
   while(!this.stopped&&now()<until){
    const job=await this.request('/v1/videos/'+this.record.id,{signal:AbortSignal.any([this.pollAbort.signal,AbortSignal.timeout(Math.max(1,Math.min(20000,until-now())))])});
    if(this.stopped)return;
    if(job.id!==this.record.id||!['queued','processing','completed','failed'].includes(job.status))throw new Error('Invalid job status response');
    this.record.status=job.status;this.record.settled=job.status==='failed'?0:job.status==='completed'&&finite(job.cost_usd)?job.cost_usd:null;
    this.record.error=job.status==='failed'&&typeof job.error==='string'?job.error.slice(0,100):null;
    // Never retain or follow a result URL supplied by a model or external host.
    if(job.status==='completed')this.contentPath=safeContentPath(this.record.id,job.result_url);
    await this.save();
    if(['completed','failed'].includes(job.status))return job;
    await sleep(delay);delay=Math.min(15000,Math.round(delay*1.7));
   }
   if(!this.stopped)throw Object.assign(new Error('Polling deadline reached; explicitly Resume existing job. No cancellation or refund implied.'),{kind:'deadline'});
  }finally{this.polling=false;}
 }
 async download(){
  await this.sameKey();if(this.record?.status!=='completed')throw new Error('Complete the existing job before download');
  const path=safeContentPath(this.record.id);let r;
  try{r=await this.fetcher(path,{signal:AbortSignal.timeout(120000),headers:{Authorization:'Bearer '+this.key},redirect:'error',cache:'no-store'});}catch{throw new Error('Download network error; retry download only');}
  if(!r.ok)throw Object.assign(new Error(r.status===502?'Content temporarily unavailable; retry download only. Completed job remains charged.':'Download HTTP '+r.status+'; use the creating key'),{status:r.status});
  const type=r.headers.get('Content-Type')||'';if(!type.startsWith('video/'))throw new Error('Unexpected media type');
  const limit=100*1024*1024,declared=r.headers.get('Content-Length');
  const incomplete=()=>new Error('Download incomplete, retry download');
  if(declared!==null&&(!/^\d+$/.test(declared)||!Number.isSafeInteger(Number(declared))||Number(declared)>limit))throw incomplete();
  const reader=r.body.getReader(),parts=[];let size=0;
  try{
   while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>limit)throw incomplete();parts.push(value);}
   if(declared!==null&&size!==Number(declared))throw incomplete();
  }catch{try{await reader.cancel();}catch{}throw incomplete();}
  if(this.stopped)throw new Error('View closed; resume download explicitly');
  if(this.blobURL)this.urlAPI.revokeObjectURL(this.blobURL);
  this.blobURL=this.urlAPI.createObjectURL(new Blob(parts,{type}));return this.blobURL;
 }
 async newVersion(){return this.exclusive(async()=>{this.refresh();await this.guardPending();if(this.record&&!['completed','failed','rejected'].includes(this.record.status))throw new Error('Resolve the existing pending or uncertain job first');if(this.blobURL)this.urlAPI.revokeObjectURL(this.blobURL);this.blobURL=null;this.record=null;this.stopped=false;});}
 dispose(){this.stopped=true;this.pollAbort?.abort();if(this.blobURL)this.urlAPI.revokeObjectURL(this.blobURL);this.blobURL=null;}

}

export function safeContentPath(id,resultURL=null){
 if(!jobId(id))throw new Error('Invalid job id');
 const path='/v1/videos/'+id+'/content';
 if(resultURL!=null&&resultURL!==path&&resultURL!=='https://api.impossi.build'+path)throw new Error('Unsafe video content origin or path');
 return path;
}
