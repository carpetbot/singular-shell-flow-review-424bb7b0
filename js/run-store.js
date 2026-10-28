// Durable, account-scoped foundation. No network, media cache, or UI policy here.
export const RUN_DB = 'singular-runs.v1';
export const LEGACY_VIDEO_KEY = 'motion-video.v1';
const hash = async value => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))].map(b=>b.toString(16).padStart(2,'0')).join('');
const terminal = status => ['done','failed'].includes(status);
const failure = () => new Error('Durable run storage unavailable; generation blocked.');
const request = req => new Promise((resolve,reject)=>{req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(failure());});

export async function openRunStore({key, indexedDB=globalThis.indexedDB}={}){
  if(typeof key!=='string' || !key.trim()) throw new Error('Connect a key before accessing saved runs.');
  key=key.trim();
  const account_id=await hash(key);
  if(!indexedDB?.open) throw failure();
  const db=await new Promise((resolve,reject)=>{
    let req;
    try{req=indexedDB.open(RUN_DB,1);}catch{reject(failure());return;}
    const timer=setTimeout(()=>reject(failure()),3000);
    req.onupgradeneeded=()=>{
      const runs=req.result.createObjectStore('runs',{keyPath:'id'});
      runs.createIndex('account_id','account_id');
      req.result.createObjectStore('meta');
    };
    req.onblocked=req.onerror=()=>{clearTimeout(timer);reject(failure());};
    req.onsuccess=()=>{clearTimeout(timer);resolve(req.result);};
  });
  db.onversionchange=()=>db.close();
  async function transaction(stores,mode,fn){
    let tx;
    try{tx=db.transaction(stores,mode,mode==='readwrite'?{durability:'strict'}:undefined);}catch{throw failure();}
    const done=new Promise((resolve,reject)=>{tx.oncomplete=resolve;tx.onabort=tx.onerror=()=>reject(failure());});
    try{const result=await fn(tx);await done;return result;}
    catch(error){try{tx.abort();}catch{}await done.catch(()=>{});throw error;}
  }
  function clean(value){
    const seen=new WeakSet();
    const walk=v=>{
      if(typeof v==='string'){
        if(v.includes(key)||/\b(?:s[k]-|m[r]_)[A-Za-z0-9_-]+/.test(v)||/^Bearer\s/i.test(v)) throw new Error('Credentials cannot be saved in runs.');
      }else if(v && typeof v==='object'){
        if(seen.has(v)||(!Array.isArray(v)&&Object.getPrototypeOf(v)!==Object.prototype)) throw new Error('Run data must be acyclic JSON.');
        seen.add(v);
        for(const [name,item] of Object.entries(v)){
          if(/^(api[_-]?key|authorization|password|secret|access[_-]?token|key)$/i.test(name)) throw new Error('Credentials cannot be saved in runs.');
          walk(name);walk(item);
        }
        seen.delete(v);
      }else if(v!==null && typeof v!=='boolean' && !(typeof v==='number'&&Number.isFinite(v))) throw new Error('Run data must be JSON.');
    };
    // Reject rather than silently dropping unsafe or unsupported recovery data.
    walk(value);return structuredClone(value);
  }
  const list=()=>transaction(['runs'],'readonly',tx=>request(tx.objectStore('runs').index('account_id').getAll(account_id)));
  const get=id=>transaction(['runs'],'readonly',async tx=>{const row=await request(tx.objectStore('runs').get(id));return row?.account_id===account_id?row:null;});
  await transaction(['meta'],'readwrite',tx=>request(tx.objectStore('meta').put({version:1},'ready'))).catch(error=>{db.close();throw error;});
  const allowed=new Set(['flow_id','title','status','created_at','inputs','outputs','prompt','model_ids','receipts','cost','video_job_id','idempotency_key','plan_id','body_hash','quote','settled','video_status','error','legacy']);
  function validate(data){
    if(!data || Array.isArray(data)||typeof data!=='object') throw new Error('Run fields required.');
    if(Object.keys(data).some(k=>!allowed.has(k))) throw new Error('Unknown run field.');
    if(data.status!==undefined&&!['running','rendering','done','failed'].includes(data.status)) throw new Error('Invalid run status.');
    for(const field of ['receipts','model_ids']) if(field in data&&!Array.isArray(data[field])) throw new Error('Run lists required.');
    for(const field of ['cost','settled']) if(field in data&&data[field]!==null&&!(typeof data[field]==='number'&&Number.isFinite(data[field])&&data[field]>=0)) throw new Error('Invalid run cost.');
    for(const field of ['flow_id','title','prompt']) if(field in data&&typeof data[field]!=='string') throw new Error('Run text required.');
    for(const field of ['idempotency_key','plan_id','body_hash']) if(field in data&&data[field]!==null&&(typeof data[field]!=='string'||!data[field])) throw new Error('Invalid run identity.');
    if(data.video_job_id!=null&&(typeof data.video_job_id!=='string'||!/^[A-Za-z0-9_-]{1,160}$/.test(data.video_job_id))) throw new Error('Invalid video job identity.');
    return clean(data);
  }
  function reconcile(row,patch){
    for(const field of ['flow_id','created_at','video_job_id','idempotency_key','plan_id','body_hash','quote']){
      if(row[field]!=null && field in patch && JSON.stringify(row[field])!==JSON.stringify(patch[field])) throw new Error('Run recovery identity mismatch.');
    }
    if(row.idempotency_key){
      for(const field of ['inputs','prompt','model_ids']) if(field in patch && JSON.stringify(row[field])!==JSON.stringify(patch[field])) throw new Error('Logical request identity mismatch.');
    }
    if(terminal(row.status) && patch.status!==undefined && patch.status!==row.status) return row;
    const next={...row,...patch};
    // Receipts are append-only evidence, never replaced by a stale observer's list.
    next.receipts=[...new Map([...(row.receipts||[]),...(patch.receipts||[])].map(r=>[JSON.stringify(r),r])).values()];
    if(typeof row.settled==='number' && Number.isFinite(row.settled)) next.settled=row.settled;
    if(terminal(row.status) && typeof row.cost==='number') next.cost=row.cost;
    if(['completed','failed','rejected'].includes(row.video_status)) next.video_status=row.video_status;
    return next;
  }
  return {
    account_id, list, get,
    // Origin/account-wide delivery claim; committed terminal truth is required.
    async claimVideoReady(jobId){
      if(typeof jobId!=='string'||!/^[A-Za-z0-9_-]{1,160}$/.test(jobId))return false;
      return transaction(['runs','meta'],'readwrite',async tx=>{
        const rows=await request(tx.objectStore('runs').index('account_id').getAll(account_id));
        if(!rows.some(r=>r.video_job_id===jobId&&r.status==='done'))return false;
        const meta=tx.objectStore('meta'),id='video-ready:'+account_id+':'+jobId;
        if(await request(meta.get(id)))return false;
        await request(meta.put(true,id));return true;
      });
    },
    pending:async()=> (await list()).filter(row=>!terminal(row.status)),
    async migrateLegacy({storage=localStorage,locks=navigator.locks}={}){
      if(!locks?.request) throw new Error('Safe legacy recovery lock unavailable; migration blocked.');
      return locks.request(LEGACY_VIDEO_KEY,{mode:'exclusive'},async()=>{
        let records;
        try{records=JSON.parse(storage.getItem(LEGACY_VIDEO_KEY)||'[]');}catch{throw new Error('Legacy recovery unreadable; original retained.');}
        if(!Array.isArray(records)) throw new Error('Legacy recovery unreadable; original retained.');
        const rows=[];let unscoped=0;
        for(const source of records){
          if(!source||typeof source.token!=='string'||!source.token||(source.id!=null&&!/^[A-Za-z0-9_-]{1,160}$/.test(source.id))) throw new Error('Invalid legacy recovery; original retained.');
          if(!source.keyHash){unscoped++;continue;}
          if(source.keyHash!==account_id) continue;
          const legacy=clean(source),status=source.status==='completed'?'done':['failed','rejected'].includes(source.status)?'failed':'rendering';
          rows.push({id:'legacy-'+await hash(JSON.stringify([account_id,source.token])),account_id,recovery_metadata_missing:true,...validate({flow_id:'claw__motion-trimmer-video',title:'Recovered video',status,
            created_at:source.created_at??null,inputs:{},outputs:{},prompt:'',model_ids:source.quote?.model?[source.quote.model]:[],receipts:[],
            cost:source.settled??null,video_job_id:source.id??null,idempotency_key:source.token,
            plan_id:source.planId??null,body_hash:source.bodyHash??null,quote:source.quote??null,settled:source.settled??null,video_status:source.status??'uncertain',error:source.error??null,legacy})});
        }
        const imported=await transaction(['runs'],'readwrite',async tx=>{
          const store=tx.objectStore('runs');let count=0;
          const current=await request(store.index('account_id').getAll(account_id));
          for(const row of rows){
            const latest=current.find(r=>r.idempotency_key===row.idempotency_key)||await request(store.get(row.id));
            if(!latest){await request(store.add(row));current.push(row);count++;}
            else{
              const patch={status:row.status,video_status:row.video_status,settled:row.settled,cost:row.cost,error:row.error,legacy:row.legacy};
              for(const field of ['video_job_id','idempotency_key','plan_id','body_hash','quote']) if(row[field]!=null) patch[field]=row[field];
              // Upgrade only deterministic, untouched pre-marker import placeholders;
              // never infer a metadata hole on a normal durable request row.
              if(latest.recovery_metadata_missing===undefined&&latest.id===row.id&&latest.prompt===''&&JSON.stringify(latest.inputs)==='{}'&&JSON.stringify(latest.outputs)==='{}'&&!latest.receipts?.length)latest.recovery_metadata_missing=true;
              const next=reconcile(latest,patch);
              await request(store.put(next));
              current[current.findIndex(r=>r.id===latest.id)]=next;
            }
          }
          return count;
        });
        // Never delete: old VideoSession tabs still write this list. Repeated imports
        // use deterministic identities and the IDB transaction is the commit point.
        return {imported,unscoped};
      });
    },
    close:()=>db.close(),
    async create(data){
      data=validate(data);
      if(typeof data.flow_id!=='string'||!data.flow_id) throw new Error('Run flow required.');
      const row={id:crypto.randomUUID(),account_id,flow_id:data.flow_id,title:'Untitled run',status:'running',created_at:new Date().toISOString(),inputs:{},outputs:{},prompt:'',model_ids:[],receipts:[],cost:null,video_job_id:null,idempotency_key:null,...data};
      return transaction(['runs'],'readwrite',async tx=>{
        const store=tx.objectStore('runs');
        const existing=await request(store.index('account_id').getAll(account_id));
        if(row.idempotency_key){
          const same=existing.find(r=>r.idempotency_key===row.idempotency_key);
          if(same){
            for(const field of ['flow_id','inputs','prompt','model_ids','plan_id','body_hash','quote']){
              if(field in data && JSON.stringify(same[field])!==JSON.stringify(row[field])) throw new Error('Logical request identity mismatch.');
            }
            return same;
          }
          if(existing.some(r=>r.flow_id===row.flow_id&&!terminal(r.status))) throw new Error('Resolve the existing pending or unconfirmed run first.');
        }
        await request(store.add(row));return row;
      });
    },
    // One-time enrichment applies only to migration-created metadata holes. Ordinary
    // update/create identity rules remain unchanged, including after enrichment.
    async enrichLegacy(id,data){
      data=validate(data);
      const fields=['inputs','outputs','prompt','model_ids','receipts','idempotency_key','plan_id','body_hash','quote'];
      if(Object.keys(data).some(k=>!fields.includes(k))||fields.some(k=>!(k in data))) throw new Error('Complete recovery metadata required.');
      const body=data.outputs?.request;
      if(!body||body.prompt!==data.prompt||JSON.stringify(data.model_ids)!==JSON.stringify([body.model])||await hash(JSON.stringify(body))!==data.body_hash) throw new Error('Logical request identity mismatch.');
      return transaction(['runs'],'readwrite',async tx=>{
        const store=tx.objectStore('runs'),row=await request(store.get(id));
        if(row?.account_id!==account_id) throw new Error('Run not found for this account.');
        for(const field of ['idempotency_key','plan_id','body_hash','quote']) if(row[field]==null||JSON.stringify(row[field])!==JSON.stringify(data[field])) throw new Error('Run recovery identity mismatch.');
        const base=row.recovery_metadata_missing===true?{...row,inputs:data.inputs,prompt:data.prompt,model_ids:data.model_ids,recovery_metadata_missing:false}:row;
        const next=reconcile(base,data);
        await request(store.put(next));return next;
      });
    },
    async update(id,patch){
      patch=validate(patch);
      return transaction(['runs'],'readwrite',async tx=>{
        const store=tx.objectStore('runs'),row=await request(store.get(id));
        if(row?.account_id!==account_id) throw new Error('Run not found for this account.');
        const next=reconcile(row,patch);
        if(next.idempotency_key){
          const existing=await request(store.index('account_id').getAll(account_id));
          if(existing.some(r=>r.id!==id&&r.idempotency_key===next.idempotency_key)) throw new Error('Run idempotency key already assigned.');
        }
        await request(store.put(next));return next;
      });
    },
  };
}
