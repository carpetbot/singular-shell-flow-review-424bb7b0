// Shared UI primitives: esc, toasts, modal, skeleton.
export function esc(s){ return String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c])); }

export function toast(msg, kind = ""){
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.textContent = msg;
  document.getElementById("toasts").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .3s"; setTimeout(() => el.remove(), 320); }, 4200);
}

export function openModal(html, onBind){
  const root = document.getElementById('modal-root');
  const returnFocus=document.activeElement;
  const previousOverflow=document.body.style.overflow;
  root.innerHTML=`<div class="modal" role="dialog" aria-labelledby="dialog-title" tabindex="-1">${html}</div>`;
  const modal=root.querySelector('.modal');
  const title=modal.querySelector('h3,h2');if(title)title.id='dialog-title';
  if(!modal.querySelector('.close-modal'))modal.insertAdjacentHTML('afterbegin','<button class="btn ghost close-modal" style="float:right" aria-label="Close flow">✕</button>');
  root.classList.add('open');
  document.body.style.overflow='hidden';
  const backgrounds=[document.getElementById('layout'),document.getElementById('tabbar')];
  backgrounds.forEach(el=>el.inert=true);
  const close=()=>{
    root.classList.remove('open');root.innerHTML='';document.removeEventListener('keydown',onKey);
    document.body.style.overflow=previousOverflow;backgrounds.forEach(el=>el.inert=false);
    if(returnFocus?.isConnected)returnFocus.focus({preventScroll:true});
  };
  const onKey=e=>{
    if(e.key==='Escape'){close();return;}
    if(e.key!=='Tab')return;
    // Keep the view-level switch reachable while the dialog is open.
    const targets=[...document.querySelectorAll('#topbar [data-mode-choice],.modal button,.modal input,.modal textarea,.modal select,.modal summary,.modal a')].filter(el=>!el.disabled && el.getClientRects().length);
    const current=targets.indexOf(document.activeElement);
    if(current===-1 || (!e.shiftKey && current===targets.length-1) || (e.shiftKey && current===0)){
      e.preventDefault();targets[e.shiftKey?targets.length-1:0]?.focus();
    }
  };
  document.addEventListener('keydown',onKey);
  root.onclick=e=>{if(e.target===root)close();};
  modal.querySelector('.close-modal').onclick=close;
  modal.querySelector('#shell-settings')?.addEventListener('click',close);
  if(onBind)onBind(modal,close);
  modal.focus({preventScroll:true});
  return close;
}

export function skeleton(n = 3){
  return Array.from({length: n}, () => '<div class="skel"></div>').join("");
}

export function fmtUsd(x){
  if(typeof x!=='number' || !Number.isFinite(x) || x<0) return '—';
  if(x === 0) return '$0';
  if(x<1){
    const cents=x*100;
    if(cents<0.01)return '<0.01¢';
    return cents.toLocaleString('en-US',{useGrouping:false,maximumFractionDigits:cents<1?3:2})+'¢';
  }
  return '$'+x.toLocaleString('en-US',{useGrouping:false,maximumFractionDigits:2});
}
