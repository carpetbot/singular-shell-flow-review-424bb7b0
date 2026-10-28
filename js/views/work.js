import { get, subscribe, hydrate } from '../store.js';
import { listVideos, fetchVideo } from '../work-api.js';
import { renderTopbar, syncBanner } from '../chrome.js';
export function view(){return `<div class="work-page"><h1>My work</h1><p>Recover videos for your connected key, including jobs from other devices.</p><p><a href="#/settings">Manage key in Settings</a></p><button id="work-refresh" type="button">Refresh videos</button><p id="work-status" role="status" aria-live="polite"></p><div id="work-list" class="work-list"></div><button id="work-more" type="button" hidden>Load more</button><section id="work-media" aria-label="Selected video" hidden></section></div>`;}
let cleanup=()=>{};
export function destroy(){cleanup();cleanup=()=>{};}
export function bind(root){
  let active=true,key=get().settings.apiKey.trim(),epoch=0,items=[],cursor=null,busy=false,objectURL=null;
  let listAbort=null,mediaAbort=null;
  const status=root.querySelector('#work-status'),list=root.querySelector('#work-list'),more=root.querySelector('#work-more'),media=root.querySelector('#work-media'),refresh=root.querySelector('#work-refresh');
  const valid=(e)=>active && epoch===e && get().settings.apiKey.trim()===key;
  function clearMedia(){
    mediaAbort?.abort();mediaAbort=null;
    const video=media.querySelector('video');if(video){video.pause();video.removeAttribute('src');video.load();}
    media.replaceChildren();media.hidden=true;
    if(objectURL) URL.revokeObjectURL(objectURL);objectURL=null;
  }
  function reset(){epoch++;listAbort?.abort();listAbort=null;clearMedia();items=[];cursor=null;busy=false;list.replaceChildren();more.hidden=true;refresh.disabled=false;}
  function text(tag,value){const e=document.createElement(tag);e.textContent=value;return e;}
  function draw(){
    const cards=document.createDocumentFragment();
    for(const job of items){
      const card=document.createElement('article');card.className='work-card';
      card.append(text('h2',job.id),text('p',String(job.status || 'unknown')));
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
  async function load(append=false){
    if(busy || !active) return;
    if(!key){status.textContent='Connect your Singular key in Settings to recover videos.';refresh.disabled=true;return;}
    const e=epoch;busy=true;more.disabled=true;refresh.disabled=true;status.textContent='Loading videos…';
    const controller=new AbortController();listAbort=controller;
    try{
      const page=await listVideos(append?cursor:null,controller.signal);if(!valid(e)) return;
      const merged=new Map((append?items:[]).map(x=>[x.id,x]));for(const job of page.items) merged.set(job.id,job);
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
      const player=document.createElement('video');player.id='work-player';player.controls=true;player.playsInline=true;player.src=objectURL;
      const download=text('a','Download MP4');download.href=objectURL;download.download=id+'.mp4';
      media.append(player,download);
    }catch(err){if(valid(e) && mediaAbort===controller && err.name!=='AbortError'){media.replaceChildren(text('p','Video unavailable or incomplete. Retry opening it.'));}}
  }
  function changed(){const next=get().settings.apiKey.trim();if(next!==key){reset();key=next;load();}}
  const unsubscribe=subscribe(changed);
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
  cleanup=()=>{active=false;reset();unsubscribe();window.removeEventListener('storage',storageChanged);};
  // A different tab may have changed settings while this route was unmounted.
  const startingEpoch=epoch;refresh.disabled=true;status.textContent='Checking connected key…';
  hydrate({clearMissingKey:true}).then(()=>{
    if(active && epoch===startingEpoch){key=get().settings.apiKey.trim();renderTopbar();syncBanner();load();}
  });
}
