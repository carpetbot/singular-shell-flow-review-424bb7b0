// Boot: hydrate store, load catalog, hash router, chrome.
import { hydrate, get, subscribe, touch } from "./store.js";
import { loadCatalog } from "./api.js";
import { syncBanner, renderTopbar, renderNav } from "./chrome.js";

import { bindMode } from './presentation.js';
import * as chat from "./views/chat.js";
import * as skills from "./views/skills.js";
import * as models from "./views/models.js";
import * as settings from "./views/settings.js";

export const VIEWS = [
  { id: "chat", ...chat },
  { id: "skills", ...skills },
  { id: "models", ...models },
  { id: "settings", ...settings },
];

let currentView = "skills";
const viewRoot = document.getElementById("view");

export function renderView(){
  const def = VIEWS.find(v => v.id === currentView);
  viewRoot.innerHTML = def.view();
  if(def.bind) def.bind(viewRoot);
  renderNav(currentView);
}

function route(){
  const hash = location.hash.replace(/^#\//, "") || "skills";
  currentView = VIEWS.some(v => v.id === hash) ? hash : "skills";
  if(document.documentElement.dataset.mode==='lite' && ['chat','models'].includes(currentView)) currentView='skills';
  renderView();
}
window.addEventListener("hashchange", route);

async function boot(){
  await hydrate();
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
