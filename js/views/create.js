import {get,subscribe,hydrate} from '../store.js';
import {loadSkill,openRunner} from './skills.js';
import {quoteDefaultVideo,MODELS} from '../video.js';
import {flowPreflight} from '../flow.js';
import {videoContext} from '../video-runtime.js';
import {esc} from '../ui.js';
const flows=[
 ['claw__motion-trimmer-video','Make a video','Plan, approve and render a five-second video.'],
 ['impossibuild__prospect-to-cold-email','Write a cold email','Turn prospect notes into an email and two follow-ups.'],
 ['impossibuild__model-jury','Compare answers','Compare three answers blind. Find the winner and best value.'],
 ['claw__motion-trimmer','Plan a video','Turn your idea into a timed, shoot-ready shot list.']
];
export const priceLabel=n=>typeof n!=='number'||!Number.isFinite(n)||n<0?'Price unavailable':n>0&&n<.01?'under 1¢':n===0?'$0.00':'$'+n.toFixed(2);
function price(manifest){
 try{
  if(manifest.runtime?.video)return priceLabel(quoteDefaultVideo(get().catalog,MODELS[0].id).price)+' per video · planning extra';
  if(manifest.runtime?.steps)return 'About '+priceLabel(flowPreflight(manifest,{},get().catalog))+' per email run · estimate';
  if(manifest.runtime?.graph)return 'Price depends on your model choices';
  return 'Auto routing · cost unknown until receipt';
 }catch{return 'Price unavailable · refresh pricing';}
}
export function view(){return `<div class="create-page"><div class="page-heading"><div class="eyebrow">CREATE</div><h1>What do you want to make?</h1><p>Start with an outcome. Let the steps take care of the rest.</p></div><section id="create-pickups" aria-label="Pick up where you left off"></section><div class="skill-grid" id="create-grid"><p>Loading templates…</p></div><p class="privacy-note">Your key. Nothing sent until you run. Estimates are not billing guarantees.</p></div>`;}
let cleanup=()=>{};
export function destroy(){cleanup();cleanup=()=>{};}
export function bind(root){
 let active=true,epoch=0,key=get().settings.apiKey.trim(),cards=[],sequence=0;
 const grid=root.querySelector('#create-grid'),pickup=root.querySelector('#create-pickups');
 const valid=e=>active&&e===epoch&&key===get().settings.apiKey.trim();
 function draw(){if(!active)return;grid.innerHTML=cards.map(({id,manifest,title,description})=>`<button class="skill-card" data-create-id="${id}" type="button"><span class="template-top"><span class="tag">${esc(price(manifest))}</span><span class="template-arrow" aria-hidden="true">↗</span></span><span class="template-title">${esc(title)}</span><span class="skill-desc">${esc(description)}</span><span class="template-bottom">${esc(manifest.name)}<span>Open flow →</span></span></button>`).join('');grid.querySelectorAll('[data-create-id]').forEach(el=>el.onclick=()=>openRunner(cards.find(c=>c.id===el.dataset.createId)));}
 async function recent(){
  const e=epoch,n=++sequence;pickup.replaceChildren();if(!key)return;
  try{const c=await videoContext(key);const rows=await c.store.list();if(!valid(e)||n!==sequence)return;
   const chosen=rows.sort((a,b)=>(Date.parse(b.created_at)||0)-(Date.parse(a.created_at)||0)).slice(0,2);if(!chosen.length)return;
   const h=document.createElement('h2');h.textContent='Pick up where you left off';pickup.append(h);
   for(const row of chosen){const link=document.createElement('a');link.className='pickup-card card';link.href=row.video_job_id?'#/work?video='+encodeURIComponent(row.video_job_id):'#/work';link.dataset.runId=row.id;const title=document.createElement('strong');title.textContent=(row.prompt?.split(/\r?\n/).find(s=>s.trim())||row.title||'Untitled run').slice(0,120);const status=document.createElement('span');status.textContent=row.status==='running'?'Planning':row.status==='rendering'?'Rendering':row.status==='done'?'Saved':'Failed';link.append(title,status);pickup.append(link);}
  }catch{if(valid(e)&&n===sequence)pickup.textContent='Local history unavailable; originals retained.';}
 }
 const changed=()=>{const next=get().settings.apiKey.trim();if(next!==key){epoch++;sequence++;key=next;pickup.replaceChildren();recent();}draw();};
 const unsubscribe=subscribe(changed);
 const runs=e=>{if(e.detail?.account_id)recent();};window.addEventListener('singular:runs',runs);
 const storage=async event=>{if(event.key!==null){try{const value=JSON.parse(event.newValue||event.oldValue||'null');if(value?.v!==1||!value.settings||!Object.hasOwn(value.settings,'apiKey'))return;}catch{return;}}epoch++;sequence++;pickup.replaceChildren();await hydrate({clearMissingKey:true});if(active){key=get().settings.apiKey.trim();recent();}};
 window.addEventListener('storage',storage);
 cleanup=()=>{active=false;epoch++;sequence++;unsubscribe();window.removeEventListener('singular:runs',runs);window.removeEventListener('storage',storage);pickup.replaceChildren();};
 Promise.all(flows.map(async([id,title,description])=>({id,title,description,...await loadSkill(id)}))).then(loaded=>{if(active){cards=loaded;draw();}}).catch(()=>{if(active)grid.textContent='Templates unavailable. Reload to try again.';});
 hydrate({clearMissingKey:true}).then(()=>{if(active){key=get().settings.apiKey.trim();recent();}});
}
