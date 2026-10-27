import {get} from './store.js';
import {chatOnce,loadCatalog} from './api.js';
import {openModal,esc} from './ui.js';
import {MODELS,FIELDS,releaseReady,quoteVideo,quoteDefaultVideo,planVideo,validatePlan,VideoSession} from './video.js';
export const videoMoney=n=>typeof n==='number'&&Number.isFinite(n)?'$'+n.toFixed(2):'unknown / unsettled';
const usd=videoMoney;
export function openVideoRunner({fields=FIELDS,fetcher=fetch,storage=localStorage,chat=chatOnce}={}){
 openModal(`<h3>Motion Trimmer → Video</h3>
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
 <label for="video-history">Saved video job references · no prompts or API keys stored here</label><select id="video-history"></select>
 <button class="btn ghost" id="video-clear">Clear finished jobs</button>
 <button class="btn ghost" id="video-resume">Resume existing job</button>
 <button class="btn ghost" id="video-download-retry" hidden>Retry download only</button>
 <button class="btn ghost" id="video-new">Make another version</button>
 <video id="video-player" controls playsinline preload="metadata" style="width:100%;max-height:360px" hidden></video>
 <a id="video-download" class="btn" style="align-self:flex-start" download="motion-trimmer.mp4" hidden>Download MP4</a>
 </div><p class="note">Closing stops polling, not the upstream job. No cancellation or refund is implied. Reload requires explicit Resume with the key you used to start this video. If the video start is not confirmed, use the identical prompt/configuration; never submit a fresh version to recover it.</p>`,modal=>{
  const el=id=>modal.querySelector('#video-'+id);let quote=null,planning=false,running=false,downloadIncomplete=false,receipts=[];
  const session=new VideoSession({key:get().settings.apiKey||'',fetcher,storage,fields,onChange:()=>render()});
  const spec=()=>({model:el('model').value,duration:5,prompt:el('prompt').value});
  const say=s=>{if(modal.isConnected)el('message').textContent=s;};
  function renderPlan(){
   try{const p=validatePlan(JSON.parse(el('plan-json').value),5);let at=0;
    el('shot-list').innerHTML='<h4>Shot list</h4><ol>'+p.shotbeats.map(b=>{const start=at;at+=b.duration_s;return `<li><strong>${esc(start)}–${esc(at)} s</strong> · ${esc(b.description)}</li>`;}).join('')+'</ol><h4>Overlay text · add in your editor</h4><ul>'+p.overlays.map(o=>`<li>${esc(o.at_s)} s · ${esc(o.text)}</li>`).join('')+'</ul><h4>Dropped items</h4><ul>'+p.dropped.map(d=>`<li>${esc(d)}</li>`).join('')+'</ul>';
   }catch{el('shot-list').textContent=el('plan-json').value?'Plan needs valid shot times, overlays and dropped items. Edit JSON in Pro or plan again.':'Plan a draft to see its shots, overlay text and dropped items.';}
  }
  function render(){
   if(!modal.isConnected)return;
   renderPlan();
   el('plan').disabled=planning||running||!session.key;
   const retry=session.record&&!session.record.id;
   const pending=session.records.filter(r=>!['completed','failed','rejected'].includes(r.status));
   const otherPending=pending.some(r=>r.token!==session.record?.token);
   el('generate').disabled=otherPending||running||!session.key||!quote||(!retry&&!el('plan-json').value)||(session.record?.id!=null);
   el('defaults').textContent=el('model').value===MODELS[0].id?'Audio: Wan default on. Framing: Model default / ratio not guaranteed.':'Audio: MiniMax unspecified. Framing: Model default / ratio not guaranteed.';
   el('generate').textContent=(retry?'Retry identical submission':'Generate video')+' · '+(quote?usd(quote.price):'quote required');
   el('receipts').textContent='Planner attempts: '+(receipts.length?receipts.map(r=>(r.model||r.requested)+' · estimated '+usd(r.estCost)).join('; '):'none in this view (not retained after reload)')+'\nVideo receipts: '+(session.records.length?session.records.map(r=>(r.id||(r.status==='rejected'?'submission rejected':'video start not confirmed'))+' · '+r.status+' · quoted '+usd(r.quote?.price)+' · '+(['completed','failed','rejected'].includes(r.status)?'settled ':'pending; unsettled ')+usd(r.settled)+(r.error?' · '+r.error:'')).join('\n'):'none');
   el('receipts').style.whiteSpace='pre-wrap';
   el('history').innerHTML=session.records.map((r,i)=>`<option value="${i}"${session.record===r?' selected':''}>${esc(r.id||(r.status==='rejected'?'rejected submission':'video start not confirmed'))} · ${esc(r.status)}</option>`).join('');
   el('resume').disabled=running||!session.record?.id;el('new').disabled=running||pending.length>0||downloadIncomplete;
   el('clear').disabled=running||!session.records.some(r=>['completed','failed','rejected'].includes(r.status));
   el('download-retry').hidden=session.record?.status!=='completed';
  }
  const show=async()=>{let url;try{url=await session.download();downloadIncomplete=false;}catch(e){if(e.message==='Download incomplete, retry download')downloadIncomplete=true;throw e;}if(!modal.isConnected)return;el('player').src=url;el('player').hidden=false;el('download').href=url;el('download').hidden=false;say('Ready · generated draft. Download does not create another job.');};
  async function follow(){if(!modal.isConnected||session.stopped)return;await session.resume();if(session.stopped)return;if(session.record.status==='completed')await show();else if(session.record.status==='failed')say('Generation failed: '+session.record.error+' · gateway reports failed jobs uncharged. Edit and choose Make another version.');}
  const perform=fn=>async()=>{if(running)return;running=true;render();try{await fn();}catch(e){say(e.message);}finally{running=false;render();}};
  el('plan').onclick=async()=>{
   if(planning||running)return;planning=true;render();say('Planning draft…');
   try{const catalog=await loadCatalog();const result=await planVideo({topic:el('topic').value,context:el('context').value,platform:el('platform').value,duration:5},{chat,catalog,signal:AbortSignal.timeout(60000)});receipts.push(...result.receipts);el('plan-json').value=JSON.stringify(result.plan,null,2);el('prompt').value=result.plan.prompt;say('Review and edit the plan and prompt. Video has not been submitted.');}
   catch(e){receipts.push(...e.receipts||[]);say(e.status===401?'Planner authentication failed':e.status===402?'Planner insufficient credits':e.message);}
   finally{planning=false;render();}
  };
  el('quote').onclick=perform(async()=>{quote=null;const r=await session.request('/pricing.json',{},false);quote=(releaseReady(fields)?quoteVideo:quoteDefaultVideo)(r,spec().model,5);el('price').textContent=usd(quote.price)+' · '+quote.duration+' s / '+quote.resolution+' · catalog '+quote.as_of+' · checked again before submit. Planner excluded.';});
  el('generate').onclick=perform(async()=>{if(!quote)throw new Error('Review fresh price first');if(!session.record){const p=JSON.parse(el('plan-json').value);p.prompt=el('prompt').value;validatePlan(p,spec().duration);}say('Creating job · quote pending, charge not settled');await session.create(spec(),quote.price);await follow();});
  el('clear').onclick=perform(async()=>{const selected=session.record?.token;await session.clearFinished();if(selected!==session.record?.token){downloadIncomplete=false;el('player').removeAttribute('src');el('player').hidden=true;el('download').removeAttribute('href');el('download').hidden=true;}say('Finished jobs cleared. Unfinished jobs are kept.');});
  el('resume').onclick=perform(async()=>{say('Resuming existing job, no new generation');await follow();});
  el('download-retry').onclick=perform(show);
  el('new').onclick=perform(async()=>{await session.newVersion();quote=null;el('player').removeAttribute('src');el('player').hidden=true;el('download').removeAttribute('href');el('download').hidden=true;say('Review edits and refresh price. Make another version to start a separate video.');});
  el('history').onchange=()=>{if(running)return;session.dispose();session.record=session.records[Number(el('history').value)];session.stopped=false;el('player').removeAttribute('src');el('player').hidden=true;el('download').removeAttribute('href');el('download').hidden=true;render();};
  el('model').onchange=()=>{quote=null;el('price').textContent='Model changed; refresh price. The draft stays five seconds.';render();};
  el('plan-json').oninput=()=>{try{const p=JSON.parse(el('plan-json').value);if(typeof p.prompt==='string')el('prompt').value=p.prompt;}catch{}render();};
  el('prompt').oninput=()=>{try{const p=JSON.parse(el('plan-json').value);p.prompt=el('prompt').value;el('plan-json').value=JSON.stringify(p,null,2);}catch{}render();};
  if(session.record){el('model').value=session.record.quote.model;say(session.record.status==='rejected'?'Submission rejected before job creation. Fix authentication/credits, then choose Make another version (close/reopen after changing Settings).':session.record.id?'Saved job found. Resume with the key you used to start this video.':'We couldn’t confirm whether the video started: re-enter identical prompt and configuration, refresh price, retry same submission. Prompt is not stored.');}
  const syncStorage=event=>{if(event.key==='motion-video.v1'||event.key===null)session.exclusive(()=>{session.refresh();render();}).catch(e=>{say(e.message);el('generate').disabled=true;el('new').disabled=true;});};
  window.addEventListener('storage',syncStorage);
  const observer=new MutationObserver(()=>{if(!modal.isConnected){session.dispose();observer.disconnect();window.removeEventListener('pagehide',dispose);window.removeEventListener('storage',syncStorage);}});observer.observe(modal.parentNode,{childList:true});const dispose=()=>session.dispose();window.addEventListener('pagehide',dispose,{once:true});
  render();
 });
}
