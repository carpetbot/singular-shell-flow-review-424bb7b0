import {get,subscribe,hydrate} from '../store.js';
import {videoContext} from '../video-runtime.js';
import {fetchVideoJob,fetchVideo} from '../work-api.js';
import {readMedia,saveMedia} from '../media-cache.js';
import {capturePoster,savePoster} from '../poster-cache.js';
import {renderTopbar,syncBanner} from '../chrome.js';
export const RUN_AGAIN_KEY='singular:run-again.v1';
export function view(){return `<section id="work-detail" class="work-page"><a href="#/work">← My work</a><p id="detail-status" role="status" aria-live="polite"></p><div id="detail-body"></div></section>`;}
const text=(tag,value)=>{const e=document.createElement(tag);e.textContent=value;return e;};
const cost=n=>typeof n==='number'&&Number.isFinite(n)?n===0?'$0':n<0.01?'under 1¢':'$'+n.toFixed(2):'Not recorded';
const date=value=>{if(value==null)return 'Not recorded';const d=new Date(typeof value==='number'?value*1000:value);return isNaN(d)?'Not recorded':d.toLocaleString();};
const hasPrompt=p=>typeof p==='string'&&p.trim()&&p!=='Prompt saved on another device';
let cleanup=()=>{};
export function destroy(){cleanup();cleanup=()=>{};}
export function bind(root){
  destroy();let active=true,key=get().settings.apiKey.trim(),epoch=0,read=0,account=null,row=null,controller=null,metadataAbort=null,url=null,frame=null,playingJob=null;
  const status=root.querySelector('#detail-status'),body=root.querySelector('#detail-body');
  let route='';try{route=decodeURIComponent(location.hash.split('?')[0].replace(/^#\/work\//,''));}catch{}
  const valid=e=>active&&epoch===e&&get().settings.apiKey.trim()===key;
  function clearPlayer(){
    controller?.abort();controller=null;const player=body.querySelector('video');
    if(player){if(frame!==null)player.cancelVideoFrameCallback?.(frame);player.pause();player.removeAttribute('src');player.load();}
    frame=null;if(url)URL.revokeObjectURL(url);url=null;playingJob=null;
  }
  function reset(){epoch++;read++;metadataAbort?.abort();metadataAbort=null;clearPlayer();row=null;account=null;body.replaceChildren();status.textContent='Checking connected key…';}
  async function copy(value,e){try{await navigator.clipboard.writeText(value);if(valid(e))status.textContent='Copied.';}catch{if(valid(e))status.textContent='Copy unavailable. Select and copy the text below.';}}
  function button(label,fn){const b=text('button',label);b.type='button';b.className='btn ghost';b.addEventListener('click',fn);return b;}
  async function media(job,e){
    clearPlayer();const abort=new AbortController();controller=abort;playingJob=job;
    const output=body.querySelector('#detail-output');output.replaceChildren(text('p','Loading video…'));
    try{
      let blob=await readMedia(account,job).catch(()=>null);if(!valid(e)||controller!==abort)return;
      if(!blob){blob=await fetchVideo(job,abort.signal);if(!valid(e)||controller!==abort)return;void saveMedia(account,job,blob).catch(()=>{});}
      if(!valid(e)||controller!==abort)return;
      url=URL.createObjectURL(blob);const player=document.createElement('video');player.id='work-player';player.controls=true;player.playsInline=true;
      const download=text('a','Download MP4');download.href=url;download.className='btn';download.download=job+'.mp4';
      let presented=false,captured=false;
      const poster=async()=>{
        if(!presented||captured||player.readyState<2)return;captured=true;player.removeEventListener('loadeddata',poster);
        if(!valid(e)||controller!==abort)return;const image=capturePoster(player);if(image)await savePoster(account,job,image).catch(()=>{});
      };
      player.addEventListener('loadeddata',poster);
      if(player.requestVideoFrameCallback)frame=player.requestVideoFrameCallback(()=>{frame=null;presented=true;poster();});
      player.src=url;output.replaceChildren(player,download);
    }catch(error){if(valid(e)&&controller===abort&&error.name!=='AbortError')output.replaceChildren(text('p','Video unavailable or incomplete.'),button('Retry download',()=>media(job,e)));}
  }
  function draw(next,e){
    if(row?.id===next.id&&next.id.startsWith('gateway:')){
      if(['done','failed'].includes(row.status))next={...next,status:row.status};
      if(!hasPrompt(next.prompt)&&hasPrompt(row.prompt))next={...next,prompt:row.prompt};
      if(next.cost==null&&typeof row.cost==='number')next={...next,cost:row.cost};
    }
    const samePlayer=row?.id===next.id&&playingJob===next.video_job_id&&next.status==='done'&&body.querySelector('#detail-output');
    const output=samePlayer?body.querySelector('#detail-output'):document.createElement('section');output.id='detail-output';
    if(!samePlayer)clearPlayer();row=next;
    body.replaceChildren(output);
    if(!next.video_job_id){output.replaceChildren(text('pre',typeof next.outputs==='string'?next.outputs:JSON.stringify(next.outputs??{},null,2)));output.append(button('Copy output',()=>copy(typeof next.outputs==='string'?next.outputs:JSON.stringify(next.outputs??{},null,2),e)));}
    else if(next.status!=='done')output.replaceChildren(text('p',next.status==='failed'?'This video failed.': 'Your video is still rendering. You can leave this page.'));
    body.append(text('h1',next.title||'Saved run'));
    const actions=document.createElement('div');actions.className='detail-actions';
    if(next.id.startsWith('gateway:'))actions.append(button('Refresh status',()=>{if(valid(e))load();}));
    if(hasPrompt(next.prompt))actions.append(button('Copy prompt',()=>copy(next.prompt,e)));
    const again=button('Run again with changes',()=>{
      if(!valid(e))return;
      // A one-shot, account-scoped draft only. Never submits or reuses paid identity.
      const flow_id=next.flow_id==='claw__motion-trimmer-video-plan'?'claw__motion-trimmer-video':next.flow_id;
      const inputs={};for(const field of ['topic','context','platform'])if(typeof next.inputs?.[field]==='string')inputs[field]=next.inputs[field].slice(0,4000);
      const payload={v:1,account_id:account,source_run_id:next.id,flow_id,inputs,created_at:Date.now()};
      try{sessionStorage.setItem(RUN_AGAIN_KEY,JSON.stringify(payload));window.dispatchEvent(new CustomEvent('singular:run-again',{detail:payload}));location.hash='#/flow/'+encodeURIComponent(flow_id);}
      catch{status.textContent='Could not prepare changes. Browser session storage is unavailable.';}
    });
    again.disabled=!['claw__motion-trimmer-video','claw__motion-trimmer-video-plan'].includes(next.flow_id)||typeof next.inputs?.topic!=='string'||!next.inputs.topic.trim();actions.append(again);body.append(actions);
    if(again.disabled)body.append(text('p','Original inputs not recorded on this browser. Open Create to start a new run.'));
    const meta=document.createElement('aside');meta.className='detail-meta';
    for(const [label,value] of [['Status',next.status==='done'?'Saved':next.status==='failed'?'Failed':'Rendering'],['Cost',cost(next.cost)],['Model',next.model_ids?.join(', ')||'Not recorded'],['Created',date(next.created_at)],['Prompt',hasPrompt(next.prompt)?next.prompt:'Prompt saved on another device']]){
      meta.append(text('h2',label),text('p',value));
    }
    const receipts=document.createElement('section');receipts.id='detail-receipts';receipts.className='pro-only';receipts.append(text('h2','Per-step receipts'));
    if(next.receipts?.length)for(const receipt of next.receipts)receipts.append(text('pre',JSON.stringify(receipt,null,2)));
    else receipts.append(text('p','Per-step model, tokens, cost and fallback were not recorded.'));
    meta.append(receipts);body.append(meta);status.textContent='';
    if(next.video_job_id&&next.status==='done'&&!samePlayer)media(next.video_job_id,e);
  }
  async function load(){
    const e=epoch,n=++read;
    if(!key){status.textContent='Connect your Singular key in Settings to view this run.';return;}
    try{
      const c=await videoContext(key);if(!valid(e)||n!==read)return;account=c.store.account_id;
      let next=await c.store.get(route);if(!valid(e)||n!==read)return;
      if(!next&&route.startsWith('gateway:')){
        const id=route.slice(8);if(!/^[A-Za-z0-9_-]{1,160}$/.test(id))throw new Error('Invalid video reference.');
        // One validated authenticated status lookup. Never enumerate the account
        // to find an already known gateway identity.
        metadataAbort?.abort();const abort=new AbortController();metadataAbort=abort;
        const found=await fetchVideoJob(id,abort.signal);
        if(!valid(e)||n!==read)return;
        next={id:'gateway:'+id,title:'Video',flow_id:'claw__motion-trimmer-video',inputs:{},video_job_id:id,status:found.status==='completed'?'done':['failed','rejected'].includes(found.status)?'failed':'rendering',prompt:hasPrompt(found.params?.prompt)?found.params.prompt:'',model_ids:[found.model],created_at:found.created_at,cost:found.cost_usd,receipts:[]};
      }
      if(!valid(e)||n!==read)return;
      if(!next){clearPlayer();row=null;body.replaceChildren();status.textContent='Run not found for this key. It may belong to another key or have been removed.';return;}
      draw(next,e);
    }catch(error){if(valid(e)&&n===read&&error.name!=='AbortError')status.textContent='Could not load this run. Return to My work and retry.';}
  }
  const changed=()=>{const next=get().settings.apiKey.trim();if(next!==key){reset();key=next;load();}};
  const unsub=subscribe(changed);
  const runs=event=>{if(active&&account&&event.detail?.account_id===account&&!route.startsWith('gateway:'))load();};window.addEventListener('singular:runs',runs);
  const storage=async event=>{
    if(event.key!==null){try{const v=JSON.parse(event.newValue||event.oldValue||'null');if(v?.v!==1||!v.settings||!Object.hasOwn(v.settings,'apiKey'))return;}catch{return;}}
    reset();const e=epoch;await hydrate({clearMissingKey:true});if(valid(e)){key=get().settings.apiKey.trim();renderTopbar();syncBanner();load();}
    else if(active&&epoch===e){key=get().settings.apiKey.trim();load();}
  };window.addEventListener('storage',storage);
  cleanup=()=>{active=false;reset();unsub();window.removeEventListener('singular:runs',runs);window.removeEventListener('storage',storage);};
  const e=epoch;hydrate({clearMissingKey:true}).then(()=>{if(active&&epoch===e){key=get().settings.apiKey.trim();renderTopbar();syncBanner();load();}});
}
