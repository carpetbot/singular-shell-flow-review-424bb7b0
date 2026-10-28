// Durable boundary around the frozen paid engine. No request/body/quote algorithms here.
import {VideoSession} from './video.js';
import {openRunStore,LEGACY_VIDEO_KEY} from './run-store.js';
import {get,subscribe,hydrate} from './store.js';
export const VIDEO_FLOW='claw__motion-trimmer-video';
let context=null,epoch=0;
const listeners=new Set();
function emit(){window.dispatchEvent(new Event('singular:runs'));}
function invalidate(){
 epoch++;
 if(context){context.abort.abort();for(const s of context.sessions)s.dispose();context.store?.close();}
 context=null;
 document.querySelectorAll('[data-video-notice]').forEach(el=>el.remove());
 for(const fn of listeners)fn();
 emit();
}
export function onVideoAccountChange(fn){listeners.add(fn);return()=>listeners.delete(fn);}
export async function videoContext(key=get().settings.apiKey){
 key=(key||'').trim();
 if(context?.key!==key)invalidate();
 if(!key)throw new Error('Connect your Singular key in Settings.');
 if(!context){
  const c={key,epoch,abort:new AbortController(),sessions:new Set(),store:null};context=c;
  c.valid=()=>context===c&&!c.abort.signal.aborted&&get().settings.apiKey.trim()===key;
  c.assert=()=>{if(!c.valid())throw new Error('Connected key changed; reopen this video.');};
  c.ready=(async()=>{
   const store=await openRunStore({key});
   if(!c.valid()){store.close();c.assert();}
   c.store=store;const migration=await store.migrateLegacy();c.assert();
   if(migration.unscoped)notice('Older video references have no account scope; originals retained. Recover videos using My work.');
   return c;
  })();
  // Initialization errors must remain visible, and must block all paid requests.
  c.ready.catch(()=>{if(c.valid())notice('Durable video recovery unavailable; generation blocked. Original references retained.');});
 }
 return context.ready;
}
function notice(message){
 const el=document.createElement('div');el.className='toast';el.dataset.videoNotice='';el.textContent=message;
 document.getElementById('toasts')?.append(el);return el;
}
function scopedStorage(storage,account){
 return {
  getItem(name){if(name!==LEGACY_VIDEO_KEY)return storage.getItem(name);const rows=JSON.parse(storage.getItem(name)||'[]');if(!Array.isArray(rows))throw new Error('Recovery unreadable');return JSON.stringify(rows.filter(r=>r.keyHash===account));},
  setItem(name,value){if(name!==LEGACY_VIDEO_KEY)return storage.setItem(name,value);const all=JSON.parse(storage.getItem(name)||'[]');storage.setItem(name,JSON.stringify([...all.filter(r=>r.keyHash!==account),...JSON.parse(value)]));}
 };
}
export async function durableVideoSession(options={}){
 const c=await videoContext(options.key);c.assert();
 const baseFetch=options.fetcher||fetch;
 const fetcher=(path,opts={})=>{c.assert();return baseFetch(path,{...opts,signal:AbortSignal.any([c.abort.signal,opts.signal||AbortSignal.timeout(120000)])});};
 class DurableSession extends VideoSession{
  async create(spec,price){
   c.assert();await c.store.migrateLegacy();c.assert();
   this.draft={...this.draft,prompt:spec.prompt,model_ids:[spec.model]};
   return super.create(spec,price);
  }
  async save(underLock=false,insert=false){
   c.assert();
   // The engine owns its origin lock and monotone local reconciliation. Await IDB
   // before it can proceed from save() to POST, even if a legacy write succeeded.
   await super.save(underLock,insert);c.assert();
   const r=this.record;if(!r)return;
   const patch={video_job_id:r.id??null,video_status:r.status,status:r.status==='completed'?'done':['failed','rejected'].includes(r.status)?'failed':'rendering',settled:r.settled??null,cost:r.settled??null,error:r.error??null,legacy:structuredClone(r)};
   const existing=(await c.store.list()).find(row=>row.idempotency_key===r.token);
   if(existing)await c.store.update(existing.id,patch);
   else await c.store.create({flow_id:VIDEO_FLOW,title:this.draft?.inputs?.topic?.slice(0,100)||'Video draft',inputs:this.draft?.inputs||{},prompt:this.draft?.prompt||'',model_ids:this.draft?.model_ids||[],receipts:(this.draft?.receipts||[]).map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,v===undefined?null:v]))),idempotency_key:r.token,plan_id:r.planId,body_hash:r.bodyHash,quote:r.quote,...patch});
   c.assert();emit();
  }
 }
 const s=new DurableSession({...options,key:c.key,fetcher,storage:scopedStorage(options.storage||localStorage,c.store.account_id)});
 c.sessions.add(s);return s;
}
export async function saveVideoPlan(brief,run){
 const c=await videoContext();c.assert();
 if(!run)return c.store.create({flow_id:VIDEO_FLOW,title:brief.topic.slice(0,100)||'Video plan',inputs:brief,status:'running',model_ids:['anthropic/claude-sonnet-5.5','deepseek/deepseek-v4.1-flash-1017']});
 const patch={...run.patch};if(patch.receipts)patch.receipts=patch.receipts.map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,v===undefined?null:v])));
 await c.store.update(run.id,patch);c.assert();emit();
}
export function startVideoRuntime(){
 let key=get().settings.apiKey.trim();
 const changed=()=>{const next=get().settings.apiKey.trim();if(next!==key){key=next;invalidate();if(key)videoContext().catch(()=>{});}};
 subscribe(changed);
 window.addEventListener('storage',async event=>{
  if(event.key===LEGACY_VIDEO_KEY)return;
  if(event.key!==null){try{const v=JSON.parse(event.newValue||event.oldValue||'null');if(v?.v!==1||!v.settings||!Object.hasOwn(v.settings,'apiKey'))return;}catch{return;}}
  invalidate();await hydrate({clearMissingKey:true});key=get().settings.apiKey.trim();if(key)videoContext().catch(()=>{});
 });
 if(key)videoContext().catch(()=>{});
}
