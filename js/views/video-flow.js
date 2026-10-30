import {get,subscribe,hydrate} from '../store.js';
import {keyConnectMarkup,bindKeyConnect} from '../key-connect.js';
import {videoRunnerMarkup,bindVideoRunner} from '../video-ui.js';

export const FLOW_ID='claw__motion-trimmer-video';
let cleanup=()=>{};
let pendingInputs=null;
// Run again: input fields only, never a paid request, plan, token or credential.
export function prefillVideoInputs(inputs){
 pendingInputs={};
 for(const field of ['topic','context','platform'])if(typeof inputs?.[field]==='string')pendingInputs[field]=inputs[field].slice(0,4000);
}
export function view(){
 const template=document.createElement('template');template.innerHTML=videoRunnerMarkup();
 const panel=template.content.querySelector('.panel-ui');
 const inputs=document.createElement('section');inputs.id='video-inputs';inputs.className='panel-ui';inputs.setAttribute('aria-label','Video inputs');
 const result=document.createElement('section');result.id='video-result';result.className='panel-ui';result.setAttribute('aria-label','Video result');
 let output=false;
 for(const node of [...panel.childNodes]){if(node.id==='video-shot-list')output=true;(output?result:inputs).append(node);}
 inputs.insertAdjacentHTML('afterbegin',`<div id="video-key" class="key-note">${keyConnectMarkup()}</div><h2>Your idea</h2><p class="note" id="video-lite-summary">5-second clip · landscape for now · you approve the price first</p><button type="button" class="btn ghost" id="video-sample">Try a sample</button><div class="pro-only"><p class="note">A generated draft, not an exact editing timeline. Overlays are editor instructions, not composited video. Platform is creative context only. No image uploads, stitching or added music.</p><p class="note" id="video-defaults"></p></div>`);
 inputs.querySelector('#video-plan').textContent='Plan my video';
 inputs.querySelector('#video-plan').insertAdjacentHTML('afterend','<p class="note" id="video-plan-charge">Planning uses a separately billed text call. You approve video generation next.</p>');
 result.querySelector('#video-quote').classList.add('pro-only');
 result.querySelector('#video-receipts').classList.add('pro-only');
 // The legacy notice/defaults are outside the extracted form. Only page notices above remain.
 result.insertAdjacentHTML('afterbegin','<h2>Review your draft</h2>');
 result.querySelector('#video-generate').insertAdjacentHTML('afterend','<p class="note" id="video-charge-note">charged only if it renders</p>');
 result.insertAdjacentHTML('beforeend','<p class="note pro-only">Rendering continues when you leave and resumes after reload. Closing this page does not cancel a submission. Use an identical retry for an unconfirmed start. After a terminal result, choose Make another version to create a separate video.</p><a href="#/work">Find saved videos in My work</a>');
 return `<article data-video-page>
 <style>
 [data-video-page]{min-width:0;max-width:1180px;margin:auto}
 [data-video-page] .video-columns{display:grid;grid-template-columns:minmax(0,0.85fr) minmax(0,1.15fr);gap:24px;align-items:start;margin-top:22px}
 [data-video-page] .panel-ui{min-width:0;padding:20px;border:1px solid var(--line);border-radius:var(--r);background:var(--panel);display:flex;flex-direction:column;gap:12px}
 [data-video-page] textarea,[data-video-page] select{width:100%;min-width:0;max-width:100%;box-sizing:border-box}
 [data-video-page] :is(p,li,button,select,#video-nodes){overflow-wrap:anywhere;word-break:break-word}
 [data-video-page] #video-progress{display:flex;list-style:none;gap:12px;padding:12px 0;flex-wrap:wrap;color:var(--dim)}
 [data-video-page] #video-progress li{padding:6px 12px;border-bottom:2px solid var(--line)}
 [data-video-page] #video-progress [aria-current]{color:var(--ink);border-color:var(--green)}
 [data-video-page] #video-nodes{font-family:var(--mono);font-size:12px;color:var(--dim);padding:12px;border:1px solid var(--line);border-radius:var(--r)}
 [data-video-page] #video-receipts{font-size:12px}
 @media(max-width:700px){[data-video-page] .video-columns{grid-template-columns:minmax(0,1fr);gap:16px}[data-video-page] .panel-ui{padding:16px}}
 </style>
 <p><a href="#/create">← Create</a></p><h1>Idea to video</h1><p>Plan a clip, review the prompt, then render a five-second video.</p>
 <div id="video-nodes" class="pro-only" aria-label="Models and costs"></div>
 <ol id="video-progress" aria-label="Video progress">${['Plan','Approve','Render','Saved'].map(step=>`<li data-step="${step}"${step==='Plan'?' aria-current="step"':''}>${step}</li>`).join('')}</ol>
 <div class="video-columns">${inputs.outerHTML}${result.outerHTML}</div></article>`;
}
export function destroy(){cleanup();cleanup=()=>{};}
export async function bind(root,{inputs=pendingInputs}={}){
 destroy();pendingInputs=null;
 let active=true,release=()=>{},disconnect=()=>{},key=get().settings.apiKey.trim(),epoch=0,controller;
 function clear(){epoch++;controller?.abort();release();release=()=>{};disconnect();disconnect=()=>{};}
 async function mount(){
  if(!active)return;clear();const e=epoch;
  const page=root.querySelector('[data-video-page]');if(!page)return;
  disconnect=bindKeyConnect(page);
  if(!key){page.querySelectorAll('button:not(#inline-connect),select,textarea').forEach(el=>el.disabled=true);return;}
  controller=new AbortController();
  const dispose=await bindVideoRunner(page,{inputs,signal:controller.signal,autoQuote:true,onAccountChange:()=>{
   // Runtime invalidation must remove old account data before any asynchronous hydration.
   if(active){clear();root.replaceChildren();queueMicrotask(()=>{if(active){key=get().settings.apiKey.trim();root.innerHTML=view();mount();}});}
  }});
  if(!active||epoch!==e){dispose?.();return;}release=dispose||(()=>{});inputs=null;
 }
 function changed(){const next=get().settings.apiKey.trim();if(next!==key){clear();key=next;root.innerHTML=view();mount();}}
 const unsub=subscribe(changed);
 const storage=async event=>{
  if(event.key!==null){try{const v=JSON.parse(event.newValue||event.oldValue||'null');if(v?.v!==1||!v.settings||!Object.hasOwn(v.settings,'apiKey'))return;}catch{return;}}
  clear();root.replaceChildren();const e=epoch;await hydrate({clearMissingKey:true});if(active&&epoch===e){key=get().settings.apiKey.trim();root.innerHTML=view();mount();}
 };
 window.addEventListener('storage',storage);
 cleanup=()=>{active=false;clear();unsub();window.removeEventListener('storage',storage);};
 await mount();
}
