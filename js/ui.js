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
  const root = document.getElementById("modal-root");
  root.innerHTML = `<div class="modal">${html}</div>`;
  root.classList.add("open");
  const close = () => { root.classList.remove("open"); root.innerHTML = ""; document.removeEventListener("keydown", onEsc); };
  const onEsc = e => { if(e.key === "Escape") close(); };
  document.addEventListener("keydown", onEsc);
  root.onclick = e => { if(e.target === root) close(); };
  if(onBind) onBind(root.querySelector(".modal"), close);
  return close;
}

export function skeleton(n = 3){
  return Array.from({length: n}, () => '<div class="skel"></div>').join("");
}

export function fmtUsd(x){
  if(x == null) return "—";
  if(x === 0) return "$0";
  return x >= 0.01 ? "$" + x.toFixed(4) : "$" + x.toExponential(2);
}
