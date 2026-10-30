import {get} from './store.js';
import {durableVideoSession,saveVideoPlan,videoContext,onVideoAccountChange,followVideo} from './video-runtime.js';
import {chatOnce,loadCatalog} from './api.js';
import {openModal,esc} from './ui.js';
import {MODELS,FIELDS,releaseReady,quoteVideo,quoteDefaultVideo,planVideo,validatePlan} from './video.js';
export const videoMoney=n=>typeof n==='number'&&Number.isFinite(n)?'$'+n.toFixed(2):'unknown / unsettled';
const usd=videoMoney;
export function videoRunnerMarkup(){
 return `<h3>Motion Trimmer → Video</h3>
 <p>A generated draft, not an exact editing timeline. Overlays are editor instructions, not composited video.</p>
 <p class="note">5-second draft · model defaults. Framing: Model default / ratio not guaranteed. Platform is creative context only. No image uploads, stitching or added music.</p>
 <p class="note" id="video-defaults">Audio: Wan default on; MiniMax unspecified. No aspect ratio or audio controls.</p>
 ${!get().settings.apiKey?'<p class="key-note">Add your Singular key in Settings to plan or resume. No key is included in media URLs.</p>':''}
 <div class="panel-ui" style="display:flex;flex-direction:column;gap:12px">
 <label for="video-topic">Topic / brief</label><textarea id="video-topic" rows="3" maxlength="4000"></textarea>
 <details><summary>Audience, style and key message · optional</summary><label for="video-context">Creative context / CTA</label><textarea id="video-context" rows="2" maxlength="4000"></textarea></details>
 <label for="video-platform">Platform · creative context</label><select id="video-platform"><option value="x">X</option><option value="instagram-reels">Instagram Reels</option><option value="youtube-shorts">YouTube Shorts</option></select>

 <label for="video-model">Video model</label><select id="video-model">${MODELS.map(m=>`<option value="${esc(m.id)}">${esc(m.name)} · ${m.resolution}</option>`).join('')}</select>
 <button class="btn" id="video-plan">Plan draft · paid text call</button>
 <section id="video-shot-list" aria-label="Shot list"></section>
 <div class="pro-only"><label for="video-plan-json">Editable shot beats, overlays and dropped details · JSON</label><textarea id="video-plan-json" rows="7" spellcheck="false"></textarea></div>
 <label for="video-prompt">Editable video prompt · no rendered words/logos</label><textarea id="video-prompt" rows="4" maxlength="12000"></textarea>
 <button class="btn ghost" id="video-quote">Refresh exact price</button><p id="video-price" class="note">No quote yet. Planner usage is separate; estimate is not a hard account cap.</p>
 <button class="btn" id="video-generate" disabled>Generate video · quote required</button>
 <p id="video-message" role="status" aria-live="polite"></p>
 <div id="video-receipts" class="receipt"></div>
 <label for="video-history">Saved video job references · current account</label><select id="video-history"></select>
 <button class="btn ghost" id="video-clear">Clear finished jobs</button>
 <button class="btn ghost" id="video-resume">Resume existing job</button>
 <button class="btn ghost" id="video-download-retry" hidden>Retry download only</button>
 <button class="btn ghost" id="video-new">Make another version</button>
 <video id="video-player" controls playsinline preload="metadata" style="width:100%;max-height:360px" hidden></video>
 <a id="video-download" class="btn" style="align-self:flex-start" download="motion-trimmer.mp4" hidden>Download MP4</a>
 </div><p class="note">Rendering continues when you leave and resumes after reload. Closing this view does not cancel a submission. Planning stays locked until the existing submission finishes or is rejected, then choose Make another version. No cancellation or refund is implied. If the video start is not confirmed, use the identical prompt/configuration; never submit a fresh version to recover it.</p>`;
}
export function openVideoRunner(options={}){
 openModal(videoRunnerMarkup(),(root,close)=>bindVideoRunner(root,{...options,onAccountChange:close}));
}
// The page and compatibility modal share the exact durable engine binding.
export async function bindVideoRunner(root,{fields=FIELDS,fetcher=fetch,storage=localStorage,chat=chatOnce,inputs=null,signal,autoQuote=false,onAccountChange=()=>{}}={}){
 let disposed=false,session;
 const cleanups=[];
 const dispose=()=>{if(disposed)return;disposed=true;session?.dispose();for(const fn of cleanups)fn();root.querySelectorAll('video').forEach(v=>{v.pause();v.removeAttribute('src');v.load();});root.querySelectorAll('button,select,textarea').forEach(e=>{e.onclick=null;e.onchange=null;e.oninput=null;});};
 if(signal){signal.addEventListener('abort',dispose,{once:true});cleanups.push(()=>signal.removeEventListener('abort',dispose));if(signal.aborted){dispose();return dispose;}}
  const el=id=>root.querySelector('#video-'+id);let quote=null,planning=false,running=false,downloadIncomplete=false,receipts=[],quoteSequence=0,quotePending=false,quoteTimer;
  cleanups.push(()=>{quoteSequence++;clearTimeout(quoteTimer);});
  el('plan').disabled=true;el('quote').disabled=true;
  const sample=el('sample');if(sample)sample.onclick=()=>{if(session?.record||planning||running)return;el('topic').value='A fictional paper boat explores a quiet moonlit pond';el('context').value='For curious makers. End with an invitation to imagine.';el('platform').value='instagram-reels';};
  let account,savedDraft;
  try{
   session=await durableVideoSession({key:get().settings.apiKey||'',fetcher,storage,fields,onChange:()=>{if(session)render();}});
   account=await videoContext();const rows=await account.store.list();account.assert();
   // Run again is an explicit new-draft action, but never bypass unresolved work.
   if(inputs&&session.record&&['completed','failed','rejected'].includes(session.record.status)&&!session.records.some(r=>!['completed','failed','rejected'].includes(r.status)))await session.newVersion();
   savedDraft=session.record?rows.find(r=>r.idempotency_key===session.record.token):rows.filter(r=>r.outputs?.plan).sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)))[0];
   if(session.record&&savedDraft?.recovery_metadata_missing){
    for(const row of rows.filter(r=>!r.idempotency_key&&r.outputs?.request&&r.outputs?.plan&&r.outputs?.render_identity?.token===session.record.token&&r.outputs.render_identity.plan_id===session.record.planId&&r.outputs.render_identity.body_hash===session.record.bodyHash)){
     const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(row.outputs.request))))].map(b=>b.toString(16).padStart(2,'0')).join('');
     if(hash===session.record.bodyHash){savedDraft=row;break;}
    }
   }
  }catch(e){if(root.isConnected&&!disposed){el('message').textContent=e.message;root.querySelectorAll('button:not(.close-modal):not(#video-sample)').forEach(b=>b.disabled=true);}return dispose;}
  if(!root.isConnected||disposed){session.dispose();return dispose;}
  if(inputs&&!session.record)savedDraft=null;
  if(savedDraft){
   for(const field of ['topic','context','platform'])if(typeof savedDraft.inputs?.[field]==='string')el(field).value=savedDraft.inputs[field];
   const plan=savedDraft.outputs?.plan;if(plan){plan.prompt=savedDraft.prompt||plan.prompt;el('plan-json').value=JSON.stringify(plan,null,2);}
   el('prompt').value=savedDraft.prompt||'';receipts=savedDraft.receipts||[];
   session.draftId=savedDraft.id;
   session.draft={inputs:savedDraft.inputs,receipts,outputs:savedDraft.outputs};
  }
  const offAccount=onVideoAccountChange(()=>{dispose();onAccountChange();});cleanups.push(offAccount);
  if(inputs&&!session.record)for(const field of ['topic','context','platform'])if(typeof inputs[field]==='string')el(field).value=inputs[field].slice(0,4000);
  const spec=()=>({model:el('model').value,duration:5,prompt:el('prompt').value});
  const say=s=>{if(root.isConnected&&!disposed&&account.valid())el('message').textContent=s;};
  function renderPlan(){
   try{const p=validatePlan(JSON.parse(el('plan-json').value),5);let at=0;
    el('shot-list').innerHTML='<h4>Shot list</h4><ol>'+p.shotbeats.map(b=>{const start=at;at+=b.duration_s;return `<li><strong>${esc(start)}–${esc(at)} s</strong> · ${esc(b.description)}</li>`;}).join('')+'</ol><h4>Overlay text · add in your editor</h4><ul>'+p.overlays.map(o=>`<li>${esc(o.at_s)} s · ${esc(o.text)}</li>`).join('')+'</ul><h4>Dropped items</h4><ul>'+p.dropped.map(d=>`<li>${esc(d)}</li>`).join('')+'</ul>';
   }catch{el('shot-list').textContent=el('plan-json').value?'Plan needs valid shot times, overlays and dropped items. Edit JSON in Pro or plan again.':'Plan a draft to see its shots, overlay text and dropped items.';}
  }
  function render(){
   if(!root.isConnected||disposed)return;
   renderPlan();
   const progress=el('progress');if(progress){const step=session.record?.status==='completed'?'Saved':session.record?'Render':el('plan-json').value?'Approve':'Plan';for(const item of progress.querySelectorAll('[data-step]')){if(item.dataset.step===step)item.setAttribute('aria-current','step');else item.removeAttribute('aria-current');}}
   if(el('sample'))el('sample').disabled=planning||running||!!session.record;
   if(el('nodes'))el('nodes').textContent='Plan · anthropic/claude-sonnet-5.5 → deepseek/deepseek-v4.1-flash-1017 · '+(receipts.length?receipts.map(r=>usd(r.estCost)).join(' + '):'usage priced separately')+' | Render · '+el('model').value+' · '+(quote?usd(quote.price):'quote required');
   el('plan').disabled=planning||running||!session.key||!!session.record||session.records.some(r=>!['completed','failed','rejected'].includes(r.status));el('quote').disabled=running;
   const retry=session.record&&!session.record.id;
   const pending=session.records.filter(r=>!['completed','failed','rejected'].includes(r.status));
   const otherPending=pending.some(r=>r.token!==session.record?.token);
   el('generate').disabled=otherPending||planning||quotePending||running||!session.key||!quote||(!retry&&!el('plan-json').value)||(session.record?.id!=null);
   el('defaults').textContent=el('model').value===MODELS[0].id?'Audio: Wan default on. Framing: Model default / ratio not guaranteed.':'Audio: MiniMax unspecified. Framing: Model default / ratio not guaranteed.';
   el('generate').textContent=(autoQuote?'Generate':retry?'Retry identical submission':'Generate video')+' · '+(quote?usd(quote.price):quotePending?'checking price…':'quote required');
   el('receipts').textContent='Planner attempts: '+(receipts.length?receipts.map(r=>(r.model||r.requested)+' · estimated '+usd(r.estCost)).join('; '):'none saved for this request')+'\nVideo receipts: '+(session.records.length?session.records.map(r=>(r.id||(r.status==='rejected'?'submission rejected':'video start not confirmed'))+' · '+r.status+' · quoted '+usd(r.quote?.price)+' · '+(['completed','failed','rejected'].includes(r.status)?'settled ':'pending; unsettled ')+usd(r.settled)+(r.error?' · '+r.error:'')).join('\n'):'none');
   el('receipts').style.whiteSpace='pre-wrap';
   el('history').innerHTML=session.records.map((r,i)=>`<option value="${i}"${session.record===r?' selected':''}>${esc(r.id||(r.status==='rejected'?'rejected submission':'video start not confirmed'))} · ${esc(r.status)}</option>`).join('');
   el('resume').disabled=running||!session.record?.id;el('new').disabled=running||pending.length>0||downloadIncomplete;
   el('clear').disabled=running||!session.records.some(r=>['completed','failed','rejected'].includes(r.status));
   el('download-retry').hidden=session.record?.status!=='completed';
  }
  const show=async()=>{let url;try{url=await session.download();downloadIncomplete=false;}catch(e){if(e.message==='Download incomplete, retry download')downloadIncomplete=true;throw e;}if(!root.isConnected||disposed)return;el('player').src=url;el('player').hidden=false;el('download').href=url;el('download').hidden=false;say('Ready · generated draft. Download does not create another job.');};
  async function follow(){if(!root.isConnected||disposed||session.stopped)return;await followVideo(session);if(session.stopped)return;if(session.record.status==='completed')await show();else if(session.record.status==='failed')say('Generation failed: '+session.record.error+' · gateway reports failed jobs uncharged. Edit and choose Make another version.');}
  const perform=fn=>async()=>{if(running)return;running=true;render();try{await fn();}catch(e){say(e.message);}finally{running=false;render();}};
  el('plan').onclick=async()=>{
   if(planning||running)return;
   if(session.record||session.records.some(r=>!['completed','failed','rejected'].includes(r.status))){say('Resolve the existing submission with an identical retry or Resume. After it finishes or is rejected, choose Make another version before planning. Closing this view does not cancel it.');return;}
   planning=true;render();say('Planning draft…');
   let saved;const brief={topic:el('topic').value,context:el('context').value,platform:el('platform').value,duration:5};
   try{saved=await saveVideoPlan(brief);const catalog=await loadCatalog();account.assert();const result=await planVideo(brief,{chat,catalog,signal:AbortSignal.any([account.abort.signal,AbortSignal.timeout(60000)])});account.assert();await saveVideoPlan(brief,{id:saved.id,patch:{status:'done',outputs:{plan:result.plan},prompt:result.plan.prompt,receipts:result.receipts}});session.draftId=saved.id;session.draft={inputs:brief,receipts:result.receipts,outputs:{plan:result.plan}};receipts.push(...result.receipts);el('plan-json').value=JSON.stringify(result.plan,null,2);el('prompt').value=result.plan.prompt;say('Review and edit the plan and prompt. Video has not been submitted.');if(autoQuote&&!disposed)await refreshQuote();}
   catch(e){if(saved&&account.valid())await saveVideoPlan(brief,{id:saved.id,patch:{status:'failed',receipts:e.receipts||[]}}).catch(()=>{});receipts.push(...e.receipts||[]);say(e.status===401?'Planner authentication failed':e.status===402?'Planner insufficient credits':e.message);}
   finally{planning=false;render();}
  };
  async function refreshQuote(){
   const seq=++quoteSequence,snapshot=JSON.stringify(spec());quote=null;quotePending=true;clearTimeout(quoteTimer);render();
   try{
    if(autoQuote){const p=JSON.parse(el('plan-json').value);p.prompt=el('prompt').value;validatePlan(p,5);}
    const catalog=await session.request('/pricing.json',{},false);account.assert();
    if(disposed||seq!==quoteSequence||snapshot!==JSON.stringify(spec()))return;
    const next=(releaseReady(fields)?quoteVideo:quoteDefaultVideo)(catalog,spec().model,5);
    if(autoQuote){const age=Date.now()-Date.parse(next.as_of);if(!Number.isFinite(age)||age < -300000||age>86400000)throw new Error('Fresh video price unavailable. Retry price in Pro.');}
    quote=next;el('price').textContent=autoQuote?'Video price '+usd(quote.price)+'. Planning is billed separately.':usd(quote.price)+' · '+quote.duration+' s / '+quote.resolution+' · catalog '+quote.as_of+' · checked again before submit. Planner excluded.';
    if(autoQuote)quoteTimer=setTimeout(()=>{if(!disposed&&seq===quoteSequence){quote=null;el('price').textContent='Price expired. Refresh price in Pro or edit your draft to recheck.';render();}},Math.max(1,Date.parse(next.as_of)+86400000-Date.now()));
   }catch(error){if(!disposed&&seq===quoteSequence&&account.valid()){quote=null;el('price').textContent='Price unavailable. '+error.message;say(error.message);}}
   finally{if(!disposed&&seq===quoteSequence){quotePending=false;render();}}
  }
  el('quote').onclick=refreshQuote;
  el('generate').onclick=perform(async()=>{if(!quote)throw new Error('Review fresh price first');if(!session.record){const p=JSON.parse(el('plan-json').value);p.prompt=el('prompt').value;validatePlan(p,spec().duration);session.draft={...session.draft,outputs:{plan:p}};}say('Creating job · quote pending, charge not settled');await session.create(spec(),quote.price);await follow();});
  el('clear').onclick=perform(async()=>{const selected=session.record?.token;await session.clearFinished();if(selected!==session.record?.token){downloadIncomplete=false;el('player').removeAttribute('src');el('player').hidden=true;el('download').removeAttribute('href');el('download').hidden=true;}say('Finished jobs cleared. Unfinished jobs are kept.');});
  el('resume').onclick=perform(async()=>{say('Resuming existing job, no new generation');await follow();});
  el('download-retry').onclick=perform(show);
  el('new').onclick=perform(async()=>{await session.newVersion();quote=null;el('player').removeAttribute('src');el('player').hidden=true;el('download').removeAttribute('href');el('download').hidden=true;say('Review edits and price. Make another version starts a separate video.');if(autoQuote)await refreshQuote();});
  el('history').onchange=()=>{if(running)return;session.dispose();session.record=session.records[Number(el('history').value)];session.stopped=false;el('player').removeAttribute('src');el('player').hidden=true;el('download').removeAttribute('href');el('download').hidden=true;render();};
  el('model').onchange=()=>{quote=null;el('price').textContent='Model changed; refresh price. The draft stays five seconds.';render();if(autoQuote)refreshQuote();};
  el('plan-json').oninput=()=>{try{const p=JSON.parse(el('plan-json').value);if(typeof p.prompt==='string')el('prompt').value=p.prompt;}catch{}render();if(autoQuote)refreshQuote();};
  el('prompt').oninput=()=>{try{const p=JSON.parse(el('plan-json').value);p.prompt=el('prompt').value;el('plan-json').value=JSON.stringify(p,null,2);}catch{}render();if(autoQuote)refreshQuote();};
  if(session.record){el('model').value=session.record.quote?.model||MODELS[0].id;say(session.record.status==='rejected'?'Submission rejected before job creation. Fix authentication/credits, then choose Make another version (close/reopen after changing Settings).':session.record.id?'Saved job found. Resume with the key you used to start this video.':'We couldn’t confirm whether the video started: re-enter identical prompt and configuration, refresh price, retry same saved submission. Any available local prompt is restored above.');}
  const syncStorage=event=>{if(event.key==='motion-video.v1'||event.key===null)session.exclusive(()=>{session.refresh();render();}).catch(e=>{say(e.message);el('generate').disabled=true;el('new').disabled=true;});};
  window.addEventListener('storage',syncStorage);
  const observer=new MutationObserver(()=>{if(!root.isConnected)dispose();});observer.observe(document.body,{childList:true,subtree:true});
  const pagehide=()=>dispose();window.addEventListener('pagehide',pagehide,{once:true});
  cleanups.push(()=>observer.disconnect(),()=>window.removeEventListener('pagehide',pagehide),()=>window.removeEventListener('storage',syncStorage));
  render();
  if(autoQuote&&el('plan-json').value)refreshQuote();
  return dispose;
}
