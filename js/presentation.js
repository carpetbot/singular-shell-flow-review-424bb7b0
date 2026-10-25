// View level only: never changes models, credentials, forms, or execution.
export const MODE_KEY = 'singular.ui.mode';
export function mode(){
  try { return localStorage.getItem(MODE_KEY)==='pro'?'pro':'lite'; }
  catch { return 'lite'; }
}
export function setMode(value){
  const next=value==='pro'?'pro':'lite';
  try { localStorage.setItem(MODE_KEY,next); } catch { /* Session-only if storage denied. */ }
  applyMode(next);
  window.dispatchEvent(new CustomEvent('singular:mode',{detail:next}));
}
function applyMode(value){
  document.documentElement.dataset.mode=value;
  document.querySelectorAll('[data-mode-choice]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.modeChoice===value)));
}
export function bindMode(){
  applyMode(mode());
  document.querySelectorAll('[data-mode-choice]').forEach(button=>button.addEventListener('click',()=>setMode(button.dataset.modeChoice)));
}
