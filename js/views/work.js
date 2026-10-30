import {keyConnectMarkup,bindKeyConnect} from '../key-connect.js';
import {readPosters,savePoster,capturePoster} from '../poster-cache.js';
import {readMedia,saveMedia} from '../media-cache.js';
import {videoContext} from '../video-runtime.js';
import { get, subscribe, hydrate } from '../store.js';
import { listVideos, fetchVideo } from '../work-api.js';
import { renderTopbar, syncBanner } from '../chrome.js';
export function view(){return `<div class="work-page"><h1>Your work</h1><p>Videos you make here appear here; videos from other devices follow your key. Email and comparison capture comes next.</p><div id="work-key" class="key-note">${keyConnectMarkup()}</div><div class="work-tools"><label>Filter <select id="work-filter"><option>All</option><option>Videos</option><option>Emails</option><option>Comparisons</option><option>Rendering</option></select></label><label>Search <input id="work-search" type="search" placeholder="Search titles and prompts"></label><button id="work-refresh" type="button">Refresh videos</button></div><p id="work-status" role="status" aria-live="polite"></p><div id="work-list" class="work-list"></div><button id="work-more" type="button" hidden>Load more</button><section id="work-media" aria-label="Selected video" hidden></section></div>`;}
const kindFor=job=>job.kind||'Videos';
const flowFor=job=>kindFor(job)==='Emails'?'Prospect → Cold Email':kindFor(job)==='Comparisons'?'Model Jury':kindFor(job)==='Videos'?'Motion Trimmer → Video':'Motion Trimmer';
const dateFor=value=>{if(value==null)return null;const d=new Date(typeof value==='number'?value*1000:value);return isNaN(d)?null:d;};
const costFor=n=>typeof n==='number'&&Number.isFinite(n)?n===0?'$0':n<0.01?'under 1¢':'$'+n.toFixed(2):'Cost not recorded';
function titleFor(job){
  const line=typeof job.params?.prompt==='string' ? job.params.prompt.split(/\r?\n/).map(s=>s.trim()).find(s=>s && s!=='Prompt saved on another device') : '';
  if(line)return line.length>120?line.slice(0,119)+'…':line;
  const date=job.created_at==null?null:new Date(typeof job.created_at==='number'?job.created_at*1000:job.created_at);
  return date&&!isNaN(date)?'Video from '+date.toLocaleDateString():'Video';
}
const labelFor=status=>status==='planning'?'Planning':status==='planned'?'Planned':status==='completed'?'Ready':['failed','rejected'].includes(status)?'Failed':'Rendering';
const terminal=status=>['completed','failed','rejected'].includes(status);
function mergeJob(gateway,local){
  if(!local)return gateway;
  return {...gateway,...local,status:terminal(local.status)||!terminal(gateway.status)?local.status:gateway.status,
    cost_usd:typeof local.cost_usd==='number'&&Number.isFinite(local.cost_usd)&&local.cost_usd>=0?local.cost_usd:gateway.cost_usd??null,
    model:local.model||gateway.model,created_at:local.created_at||gateway.created_at,
    params:{...gateway.params,...local.params,prompt:local.params?.prompt||gateway.params?.prompt}};
}
let cleanup=()=>{};
export function destroy(){cleanup();cleanup=()=>{};}
export function bind(root){
  let active=true,key=get().settings.apiKey.trim(),epoch=0,checking=false,items=[],cursor=null,busy=false,objectURL=null,gatewayItems=new Map();
  let listAbort=null,mediaAbort=null,opened=null,frameCallback=null,posters=new Map(),posterAccount=null,localRead=0;
  const status=root.querySelector('#work-status'),list=root.querySelector('#work-list'),more=root.querySelector('#work-more'),media=root.querySelector('#work-media'),refresh=root.querySelector('#work-refresh');
  let disconnect=()=>{},displayedKey=null;
  function keyControls(){if(displayedKey!==key){disconnect();root.querySelector('#work-key').innerHTML=keyConnectMarkup();disconnect=bindKeyConnect(root.querySelector('#work-key'));displayedKey=key;}refresh.hidden=!key;}
  keyControls();
  const valid=(e)=>active && !checking && epoch===e && get().settings.apiKey.trim()===key;
  function clearMedia(){
    mediaAbort?.abort();mediaAbort=null;
    const video=media.querySelector('video');if(video){if(frameCallback!==null)video.cancelVideoFrameCallback?.(frameCallback);frameCallback=null;video.pause();video.removeAttribute('src');video.load();}
    media.replaceChildren();media.hidden=true;
    if(objectURL) URL.revokeObjectURL(objectURL);objectURL=null;
  }
  function reset(){opened=null;posters=new Map();posterAccount=null;epoch++;listAbort?.abort();listAbort=null;clearMedia();items=[];gatewayItems=new Map();cursor=null;busy=false;list.replaceChildren();more.hidden=true;refresh.disabled=false;}
  function text(tag,value){const e=document.createElement(tag);e.textContent=value;return e;}
  const filter=root.querySelector('#work-filter'),search=root.querySelector('#work-search');
  function draw(){
    const cards=document.createDocumentFragment(),groups=new Map(),query=search.value.trim().toLocaleLowerCase();
    const visible=items.filter(job=>(filter.value==='All'||(filter.value==='Rendering'?labelFor(job.status)==='Rendering':kindFor(job)===filter.value))&&[job.title,titleFor(job),job.params?.prompt].filter(x=>typeof x==='string').join(' ').toLocaleLowerCase().includes(query));
    visible.sort((a,b)=>(dateFor(b.created_at)?.getTime()||0)-(dateFor(a.created_at)?.getTime()||0)||a.id.localeCompare(b.id));
    for(const job of visible){
      const day=dateFor(job.created_at)?.toLocaleDateString()||'Date not recorded';
      let grid=groups.get(day);if(!grid){const section=document.createElement('section');section.className='work-day';section.append(text('h2',day));grid=document.createElement('div');grid.className='work-day-grid';section.append(grid);cards.append(section);groups.set(day,grid);}
      const card=document.createElement('article');card.className='work-card';
      const label=text('p',labelFor(job.status));label.className='work-status';
      if(job.status==='completed'&&posters.has(job.id)){const image=document.createElement('img');image.className='work-poster';image.alt='Video preview';image.src=posters.get(job.id);card.append(image);}
      const title=kindFor(job)==='Videos'?titleFor(job):job.title||'Saved run';
      card.append(text('h2',title),text('p',flowFor(job)),label,text('p',costFor(job.cost_usd)));
      const prompt=typeof job.params?.prompt==='string' ? job.params.prompt : 'Prompt saved on another device';
      card.append(text('p',prompt),text('p',String(job.model || job.params?.model || 'Model not provided')));
      if(dateFor(job.created_at))card.append(text('p',dateFor(job.created_at).toLocaleString()));
      const detail=text('a','Open run');detail.href='#/work/'+encodeURIComponent(job.local_id||'gateway:'+job.id);card.append(detail);
      // Keep A2 query-route/inline playback as a compatibility action; new history
      // links use durable run ids (gateway-only uses an explicit namespace).
      if(job.status==='completed'&&kindFor(job)==='Videos'&&(!job.local_id||job.has_media)){
        const open=text('button','Open video');open.type='button';open.setAttribute('aria-label','Open video '+job.id);open.addEventListener('click',()=>openMedia(job.id));card.append(open);
      }
      grid.append(card);
    }
    if(!visible.length)cards.append(text('p','No matching work.'));
    list.replaceChildren(cards);
  }
  function loadedStatus(){const mixed=items.some(j=>kindFor(j)!=='Videos'||(j.local_id&&!j.has_media));return items.length?`${items.length} ${mixed?'runs':'video jobs'} loaded.`:'No video jobs found for this key.';}
  async function localRows(e,account=null){
    let read;
    const current=()=>valid(e)&&read===localRead;
    try{
      const c=await videoContext(key);if(!valid(e)||(account&&account!==c.store.account_id))return;
      read=++localRead;const rows=await c.store.list();if(!current())return;
      if(posterAccount!==c.store.account_id){const saved=await readPosters(c.store.account_id).catch(()=>new Map());if(!current())return;posters=saved;posterAccount=c.store.account_id;}
      // Planner snapshots remain durable evidence, but a bound render is the
      // single user-facing run. An unsubmitted/abandoned plan stays visible.
      const visibleRows=rows.filter(r=>!(!r.idempotency_key&&r.outputs?.render_identity?.token&&rows.some(x=>x.idempotency_key===r.outputs.render_identity.token)));
      const local=visibleRows.map(r=>({id:r.video_job_id||r.id,has_media:!!r.video_job_id,local_id:r.id,title:r.title,kind:r.flow_id==='claw__motion-trimmer-video'||r.flow_id==='claw__motion-trimmer-video-plan'||r.video_job_id?'Videos':r.flow_id==='impossibuild__prospect-to-cold-email'?'Emails':r.flow_id==='impossibuild__model-jury'?'Comparisons':'Text',status:r.video_status||(!r.video_job_id&&r.flow_id==='claw__motion-trimmer-video-plan'&&r.status!=='failed'?(r.status==='done'?'planned':'planning'):r.status==='done'?'completed':r.status==='failed'?'failed':'processing'),params:{prompt:r.prompt||undefined},model:r.model_ids?.[0],created_at:r.created_at,cost_usd:r.cost}));
      const merged=new Map(gatewayItems);for(const job of local)merged.set(job.id,mergeJob(merged.get(job.id)||{},job));items=[...merged.values()];draw();if(!busy)status.textContent=loadedStatus();
      const selected=new URLSearchParams(location.hash.split('?')[1]||'').get('video');
      if(selected&&opened!==selected&&items.some(j=>j.id===selected&&j.status==='completed')){opened=selected;openMedia(selected);}
    }catch{if(valid(e))status.textContent='Local video recovery unavailable; originals retained.';}
  }
  async function load(append=false){
    if(busy || !active || checking) return;
    if(!key){keyControls();status.textContent='Connect your key to see your videos.';refresh.disabled=true;return;}keyControls();
    const e=epoch;busy=true;more.disabled=true;refresh.disabled=true;status.textContent='Loading videos…';
    const controller=new AbortController();listAbort=controller;
    try{
      await localRows(e);if(!valid(e))return;
      const page=await listVideos(append?cursor:null,controller.signal);if(!valid(e)) return;
      const merged=new Map(items.map(x=>[x.id,x]));for(const job of page.items){gatewayItems.set(job.id,mergeJob(job,gatewayItems.get(job.id)));const local=merged.get(job.id);merged.set(job.id,mergeJob(gatewayItems.get(job.id),local?.local_id?local:null));}
      items=[...merged.values()];cursor=page.next_cursor;draw();status.textContent=loadedStatus();
    }catch(err){if(valid(e) && err.name!=='AbortError') status.textContent=err.message?.startsWith('Key not accepted') ? err.message : 'Could not load videos. Retry.';}
    finally{if(valid(e)){busy=false;more.hidden=!cursor;more.disabled=false;refresh.disabled=false;}}
  }
  async function openMedia(id){
    clearMedia();const e=epoch,controller=new AbortController();mediaAbort=controller;
    media.hidden=false;media.append(text('h2',id),text('p','Loading video…'));
    try{
      const c=await videoContext(key);if(!valid(e)||mediaAbort!==controller)return;
      let blob=await readMedia(c.store.account_id,id).catch(()=>null);if(!valid(e)||mediaAbort!==controller)return;
      if(!blob){blob=await fetchVideo(id,controller.signal);if(!valid(e)||mediaAbort!==controller)return;void saveMedia(c.store.account_id,id,blob).catch(()=>{});}
      if(!valid(e) || mediaAbort!==controller) return;
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
  function changed(){const next=get().settings.apiKey.trim();if(next!==key){reset();checking=false;key=next;load();}}
  const unsubscribe=subscribe(changed);
  const runsChanged=event=>{if(active&&!checking&&key&&event.detail?.account_id)localRows(epoch,event.detail.account_id);};window.addEventListener('singular:runs',runsChanged);
  // Follow existing settings storage on cross-tab account changes too.
  const storageChanged=async(event)=>{
    // Ignore unrelated stores; clearing settings must hide prior media immediately.
    if(event.key!==null){
      try{const value=JSON.parse(event.newValue || event.oldValue || 'null');if(value?.v!==1 || !value.settings || !Object.hasOwn(value.settings,'apiKey')) return;}catch{return;}
    }
    checking=true;reset();refresh.hidden=true;displayedKey=null;disconnect();root.querySelector('#work-key').replaceChildren();refresh.disabled=true;status.textContent='';
    const e=epoch;await hydrate({clearMissingKey:true});
    if(active&&epoch===e){checking=false;key=get().settings.apiKey.trim();renderTopbar();syncBanner();load();}
  };
  window.addEventListener('storage',storageChanged);
  filter.addEventListener('change',draw);search.addEventListener('input',draw);
  more.addEventListener('click',()=>load(true));
  refresh.addEventListener('click',()=>{reset();load();});
  cleanup=()=>{active=false;disconnect();reset();unsubscribe();window.removeEventListener('singular:runs',runsChanged);window.removeEventListener('storage',storageChanged);};
  // A different tab may have changed settings while this route was unmounted.
  const startingEpoch=epoch;refresh.disabled=true;status.textContent=key?'Loading your videos…':'';
  hydrate({clearMissingKey:true}).then(()=>{
    if(active && epoch===startingEpoch){key=get().settings.apiKey.trim();renderTopbar();syncBanner();load();}
  });
}
