// Boot: hydrate store, load catalog, hash router, chrome.
import { hydrate, get, subscribe, touch } from "./store.js";
import { loadCatalog } from "./api.js";
import { syncBanner, renderTopbar, renderNav } from "./chrome.js";

import {startVideoRuntime} from './video-runtime.js';
import { bindMode } from './presentation.js';
import * as videoFlow from './views/video-flow.js';
import * as create from './views/create.js';
import * as chat from "./views/chat.js";
import * as skills from "./views/skills.js";
import * as models from "./views/models.js";
import * as settings from "./views/settings.js";
import * as workDetail from './views/work-detail.js';
import * as work from "./views/work.js";

export const VIEWS = [
  { id: "video-flow", ...videoFlow },
  { id: "create", ...create },
  { id: "chat", ...chat },
  { id: "skills", ...skills },
  { id: "models", ...models },
  { id: "settings", ...settings },
  { id: "work-detail", ...workDetail },
  { id: "work", ...work },
];

let currentView = "create";
const viewRoot = document.getElementById("view");
let mountedView;

export function renderView(){
  mountedView?.destroy?.();
  const def = VIEWS.find(v => v.id === currentView);
  mountedView = def;
  viewRoot.innerHTML = def.view();
  if(def.bind) def.bind(viewRoot);
  renderNav(currentView==='work-detail'?'work':['video-flow','skills'].includes(currentView)?'create':currentView);
}

function route(){
  const hash = location.hash.replace(/^#\//, "").split('?')[0] || "create";
  currentView = hash.startsWith('work/')?'work-detail':hash==='flow/claw__motion-trimmer-video'?'video-flow':VIEWS.some(v => v.id === hash) ? hash : "create";
  if(document.documentElement.dataset.mode==='lite' && ['chat','models'].includes(currentView)) currentView='create';
  if(!location.hash)history.replaceState(null,'','#/create');
  renderView();
}
window.addEventListener("hashchange", route);

async function boot(){
  await hydrate();
  startVideoRuntime();
  bindMode();
  window.addEventListener('singular:mode',()=>{
    if(document.documentElement.dataset.mode==='lite' && ['chat','models'].includes(currentView)) route();
  });
  subscribe(() => { renderTopbar(); syncBanner(); });
  try{
    const cat = await loadCatalog();
    get().catalog = { as_of: cat.as_of, models: cat.models };
    touch();
  }catch(e){
    console.warn("catalog fetch failed:", e);
    window.__catalogError = String(e.message || e);
  }
  route();
  renderTopbar();
  syncBanner();
}
boot();
