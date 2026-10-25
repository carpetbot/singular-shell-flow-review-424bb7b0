// Chrome: topbar chips + nav active + error banner.
import { get, set } from "./store.js";
import { loadCatalog } from "./api.js";
import { toast } from "./ui.js";

export function renderTopbar(){
  const s = get();
  const chip = document.getElementById("keychip");
  chip.textContent = s.settings.apiKey ? "mr_ key ✓" : "no key";
  chip.className = "chip " + (s.settings.apiKey ? "ok" : "warn");
  const rc = document.getElementById("routechip");
  const prof = s.settings.routingProfile || "auto";
  rc.textContent = prof === "auto" ? (s.settings.model || "auto") : `${s.settings.model || "auto"} · ${prof}`;
}

export function renderNav(active){
  document.querySelectorAll("[data-nav]").forEach(a =>
    a.classList.toggle("active", a.dataset.nav === active));
}

export function syncBanner(){
  const b = document.getElementById("syncbanner");
  const err = window.__catalogError;
  if(err){
    b.hidden = false;
    b.innerHTML = `⚠ Couldn't load live pricing catalog (${err}). Cost estimates fall back to last cache until retry succeeds. <button class="btn sm ghost" id="banner-retry">Retry</button>`;
    b.querySelector("#banner-retry").addEventListener("click", retryCatalog);
  }else{
    b.hidden = true;
  }
}

export async function retryCatalog(){
  try{
    const cat = await loadCatalog();
    window.__catalogError = null;
    set({ catalog: { as_of: cat.as_of, models: cat.models } });
    toast("pricing catalog loaded (" + (cat.models?.length || 0) + " models)", "ok");
  }catch(e){
    window.__catalogError = String(e.message || e);
  }
  syncBanner();
}
