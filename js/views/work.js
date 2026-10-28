import {readPosters,savePoster,capturePoster} from '../poster-cache.js';
import {videoContext} from '../video-runtime.js';
import { get, subscribe, hydrate } from '../store.js';
import { listVideos, fetchVideo } from '../work-api.js';
import { renderTopbar, syncBanner } from '../chrome.js';
export function view(){return `<div class="work-page"><h1>My work</h1><p>Recover videos for your connected key, including jobs from other devices.</p><p><a href="#/settings">Manage key in Settings</a></p><button id="work-refresh" type="button">Refresh videos</button><p id="work-status" role="status" aria-live="polite"></p><div id="work-list" class="work-list"></div><button id="work-more" type="button" hidden>Load more</button><section id="work-media" aria-label="Selected video" hidden></section></div>`;}
function titleFor(job){
  const line=typeof job.params?.prompt==='string' ? job.params.prompt.split(/\r?\n/).map(s=>s.trim()).find(s=>s && s!=='Prompt saved on another device') : '';
  if(line)return line.length>120?line.slice(0,119)+'…':line;
  const date=job.created_at==null?null:new Date(typeof job.created_at==='number'?job.created_at*1000:job.created_at);
  return date&&!isNaN(date)?'Video from '+date.toLocaleDateString():'Video';
}
const labelFor=status=>status==='completed'?'Ready':['failed','rejected'].includes(status)?'Failed':'Rendering';
const terminal=status=>['completed','failed','rejected'].includes(status);
function mergeJob(gateway,local){
  if(!local)return gateway;
  return {...gateway,...local,status:terminal(local.status)||!terminal(gateway.status)?local.status:gateway.status,
    model:local.model||gateway.model,created_at:local.created_at||gateway.created_at,
    params:{...gateway.params,...local.params,prompt:local.params?.prompt||gateway.params?.prompt}};
}
let cleanup=()=>{};
export function destroy(){cleanup();cleanup=()=>{};}
export function bind(root){
  let active=true,key=get().settings.apiKey.trim(),epoch=0,items=[],cursor=null,busy=false,objectURL=null;
  let listAbort=null,mediaAbort=null,opened=null,frameCallback=null,posters=new Map(),posterAccount=null;
  const status=root.querySelector('#work-status'),list=root.querySelector('#work-list'),more=root.querySelector('#work-more'),media=root.querySelector('#work-media'),refresh=root.querySelector('#work-refresh');
  const valid=(e)=>active && epoch===e && get().settings.apiKey.trim()===key;
  function clearMedia(){
    mediaAbort?.abort();mediaAbort=null;
    const video=media.querySelector('video');if(video){if(frameCallback!==null)video.cancelVideoFrameCallback?.(frameCallback);frameCallback=null;video.pause();video.removeAttribute('src');video.load();}
    media.replaceChildren();media.hidden=true;
    if(objectURL) URL.revokeObjectURL(objectURL);objectURL=null;
  }
  function reset(){opened=null;posters=new Map();posterAccount=null;epoch++;listAbort?.abort();listAbort=null;clearMedia();items=[];cursor=null;busy=false;list.replaceChildren();more.hidden=true;refresh.disabled=false;}
  function text(tag,value){const e=document.createElement(tag);e.textContent=value;return e;}
  function draw(){
    const cards=document.createDocumentFragment();
    for(const job of items){
      const card=document.createElement('article');card.className='work-card';
      const label=text('p',labelFor(job.status));label.className='work-status';
      if(job.status==='completed'&&posters.has(job.id)){const image=document.createElement('img');image.className='work-poster';image.alt='Video preview';image.src=posters.get(job.id);card.append(image);}
      card.append(text('h2',titleFor(job)),label);
      const prompt=typeof job.params?.prompt==='string' ? job.params.prompt : 'Prompt saved on another device';
      card.append(text('p',prompt),text('p',String(job.model || job.params?.model || 'Model not provided')));
      if(job.created_at!=null){const date=new Date(typeof job.created_at==='number' ? job.created_at*1000 : job.created_at);if(!isNaN(date)) card.append(text('p',date.toLocaleString()));}
      if(job.status==='completed'){
        const open=text('button','Open video');open.type='button';open.setAttribute('aria-label','Open video '+job.id);open.addEventListener('click',()=>openMedia(job.id));card.append(open);
      }
      cards.append(card);
    }
    list.replaceChildren(cards);
  }
  async function localRows(e){
    try{
      const c=await videoContext(key),rows=await c.store.list();if(!valid(e))return;
      if(posterAccount!==c.store.account_id){const saved=await readPosters(c.store.account_id).catch(()=>new Map());if(!valid(e))return;posters=saved;posterAccount=c.store.account_id;}
      const local=rows.filter(r=>r.idempotency_key).map(r=>({id:r.video_job_id||r.id,local_id:r.id,status:r.video_status,params:{prompt:r.prompt||undefined},model:r.model_ids[0],created_at:r.created_at,cost_usd:r.cost}));
      const merged=new Map(items.map(x=>[x.id,x]));for(const job of local)merged.set(job.id,mergeJob(merged.get(job.id)||{},job));items=[...merged.values()];draw();
      const selected=new URLSearchParams(location.hash.split('?')[1]||'').get('video');
      if(selected&&opened!==selected&&items.some(j=>j.id===selected&&j.status==='completed')){opened=selected;openMedia(selected);}
    }catch{if(valid(e))status.textContent='Local video recovery unavailable; originals retained.';}
  }
  async function load(append=false){
    if(busy || !active) return;
    if(!key){status.textContent='Connect your Singular key in Settings to recover videos.';refresh.disabled=true;return;}
    const e=epoch;busy=true;more.disabled=true;refresh.disabled=true;status.textContent='Loading videos…';
    const controller=new AbortController();listAbort=controller;
    try{
      await localRows(e);if(!valid(e))return;
      const page=await listVideos(append?cursor:null,controller.signal);if(!valid(e)) return;
      const merged=new Map(items.map(x=>[x.id,x]));for(const job of page.items){const local=merged.get(job.id);merged.set(job.id,mergeJob(job,local?.local_id?local:null));}
      items=[...merged.values()];cursor=page.next_cursor;draw();status.textContent=items.length ? `${items.length} video jobs loaded.` : 'No video jobs found for this key.';
    }catch(err){if(valid(e) && err.name!=='AbortError') status.textContent=err.message?.startsWith('Key not accepted') ? err.message : 'Could not load videos. Retry.';}
    finally{if(valid(e)){busy=false;more.hidden=!cursor;more.disabled=false;refresh.disabled=false;}}
  }
  async function openMedia(id){
    clearMedia();const e=epoch,controller=new AbortController();mediaAbort=controller;
    media.hidden=false;media.append(text('h2',id),text('p','Loading video…'));
    try{
      const blob=await fetchVideo(id,controller.signal);if(!valid(e) || mediaAbort!==controller) return;
      objectURL=URL.createObjectURL(blob);media.replaceChildren(text('h2',id));
      const player=document.createElement('video');player.id='work-player';player.controls=true;player.playsInline=true;
      const download=text('a','Download MP4');download.href=objectURL;download.download=id+'.mp4';
      // Require both a presented frame and loaded data; Chromium can report either first.
      let presented=false,captured=false;
      const cacheFrame=async()=>{
        if(!presented||captured||player.readyState<2)return;
        captured=true;player.removeEventListener('loadeddata',cacheFrame);
        if(!valid(e)||mediaAbort!==controller||!items.some(j=>j.id===id&&j.status==='completed'))return;
        const image=capturePoster(player);if(!image)return;
        try{const c=await videoContext(key);if(!valid(e)||mediaAbort!==controller)return;await savePoster(c.store.account_id,id,image);
          if(valid(e)&&mediaAbort===controller){posters.set(id,image);draw();}
        }catch{/* Optional cache failure must not interrupt playback/download. */}
      };
      player.addEventListener('loadeddata',cacheFrame);
      // Register before setting src so even a fast paused first frame is observed.
      if(player.requestVideoFrameCallback)frameCallback=player.requestVideoFrameCallback(()=>{frameCallback=null;presented=true;cacheFrame();});
      player.src=objectURL;media.append(player,download);
    }catch(err){if(valid(e) && mediaAbort===controller && err.name!=='AbortError'){media.replaceChildren(text('p','Video unavailable or incomplete. Retry opening it.'));}}
  }
  function changed(){const next=get().settings.apiKey.trim();if(next!==key){reset();key=next;load();}}
  const unsubscribe=subscribe(changed);
  const runsChanged=()=>{if(active&&key)localRows(epoch);};window.addEventListener('singular:runs',runsChanged);
  // Follow existing settings storage on cross-tab account changes too.
  const storageChanged=async(event)=>{
    // Ignore unrelated stores; clearing settings must hide prior media immediately.
    if(event.key!==null){
      try{const value=JSON.parse(event.newValue || event.oldValue || 'null');if(value?.v!==1 || !value.settings || !Object.hasOwn(value.settings,'apiKey')) return;}catch{return;}
    }
    reset();refresh.disabled=true;status.textContent='Checking connected key…';
    await hydrate({clearMissingKey:true});
    if(active){key=get().settings.apiKey.trim();renderTopbar();syncBanner();load();}
  };
  window.addEventListener('storage',storageChanged);
  more.addEventListener('click',()=>load(true));
  refresh.addEventListener('click',()=>{reset();load();});
  cleanup=()=>{active=false;reset();unsubscribe();window.removeEventListener('singular:runs',runsChanged);window.removeEventListener('storage',storageChanged);};
  // A different tab may have changed settings while this route was unmounted.
  const startingEpoch=epoch;refresh.disabled=true;status.textContent='Checking connected key…';
  hydrate({clearMissingKey:true}).then(()=>{
    if(active && epoch===startingEpoch){key=get().settings.apiKey.trim();renderTopbar();syncBanner();load();}
  });
}
