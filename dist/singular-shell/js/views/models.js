// Model catalog: live pricing.json, searchable, feed honesty surfaced.
import { get } from "../store.js";
import { esc, fmtUsd } from "../ui.js";

const FREE_IDS = new Set(["nano-gpt-help", "qwen/qwen3.5-omni-flash", "qwen/qwen3.5-omni-plus"]);

export function view(){
  const s = get();
  const cat = s.catalog;
  if(!cat) return `<h2>Model catalog</h2><div class="skel" style="height:300px"></div>`;
  return `
    <h2>Model catalog <span class="chip">${cat.models.length} models</span> <span class="chip" title="pricing.json as_of">as of ${esc(cat.as_of?.slice(0,16).replace("T"," "))}</span></h2>
    <div class="searchbar">
      <input type="text" id="q" placeholder="search qwen, claude, gpt…">
      <div class="filterchips">
        ${["all","chat","image","audio_speech","audio_transcription","video"].map(k=>`<span class="tag kfilter" data-k="${k}" style="cursor:pointer">${k}</span>`).join("")}
      </div>
    </div>
    <div class="tablewrap"><table id="tbl"></table></div>
    <div class="note" style="margin-top:10px">⚠ Feed honesty: <code>0/0</code> pricing can mean genuinely-free <i>or unknown</i> — only 3 models are known free-designated. <code>:free</code> tier IDs don't exist in this feed. Zero-price rows are marked <b>?</b> unless confirmed.</div>`;
}

let kindFilter = "all";

export function bind(root){
  const s = get();
  const q = root.querySelector("#q");
  const tbl = root.querySelector("#tbl");
  function draw(){
    const term = (q.value || "").toLowerCase();
    const rows = s.catalog.models.filter(m => {
      if(kindFilter !== "all" && m.kind !== kindFilter) return false;
      if(term && !(m.id.toLowerCase().includes(term) || (m.name||"").toLowerCase().includes(term))) return false;
      return true;
    }).slice(0, 300);
    tbl.innerHTML = `<thead><tr><th>id</th><th>kind</th><th>$/M in</th><th>$/M out</th><th>$/img</th><th>ctx</th><th>route</th></tr></thead>
      <tbody>${rows.map(m => {
        const free = m.promptPerMillionUsd === 0 && m.completionPerMillionUsd === 0;
        const knownFree = FREE_IDS.has(m.id);
        return `<tr class="${m.routable ? "" : "off"}"><td>${esc(m.id)}${free && !knownFree ? ' <span title="0-price: may be unknown, not free">?</span>' : ""}</td>
        <td>${esc(m.kind)}</td><td>${fmtUsd(m.promptPerMillionUsd)}</td><td>${fmtUsd(m.completionPerMillionUsd)}</td>
        <td>${m.pricePerImageUsd != null ? fmtUsd(m.pricePerImageUsd) : "—"}</td><td>${m.maxContextTokens ?? "—"}</td>
        <td>${m.routable ? "✓" : "✗"}</td></tr>`;
      }).join("")}</tbody>`;
  }
  q.oninput = draw;
  root.querySelectorAll(".kfilter").forEach(t => t.onclick = () => {
    kindFilter = t.dataset.k;
    root.querySelectorAll(".kfilter").forEach(x => x.style.borderColor = "var(--line)");
    t.style.borderColor = "var(--blue)";
    draw();
  });
  draw();
}
