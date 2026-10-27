// Skill gallery + declarative ui: panel renderer.
// v1 gallery = static JSONs under ./skills/ (the manifest + prompts are data,
// exactly per SKILL-MANIFEST-SPEC.md). When a real gallery endpoint exists,
// only SKILL_INDEX changes.
import { get } from "../store.js";
import { chatOnce } from "../api.js";
import { esc, toast, fmtUsd, openModal } from "../ui.js";

import { openFlowRunner } from '../flow-ui.js';
import {routableModels} from '../graph.js';
import {openGraphRunner} from '../graph-ui.js';
import {openVideoRunner} from '../video-ui.js';
const SKILL_INDEX = ["claw__motion-trimmer", "impossibuild__prospect-to-cold-email", "impossibuild__model-jury", "claw__motion-trimmer-video"];

export async function loadSkill(id, fetcher = fetch){
  let r = await fetcher(`/skills/${id}/singular.flow.json`);
  if(r.status === 404) r = await fetcher(`/skills/${id}/singular.skill.json`);
  if(!r.ok) throw new Error(`manifest HTTP ${r.status}`);
  const m = await r.json();
  const prompts = {};
  for(const entry of [m.entry, ...(m.runtime?.steps || m.runtime?.graph || [])].filter(Boolean)){
    for(const path of [entry.system, entry.user_template].filter(Boolean)){
      if(path.startsWith('inline:') || Object.hasOwn(prompts, path)) continue;
      const p = await fetcher(`/skills/${id}/${path}`);
      if(!p.ok) throw new Error(`prompt ${path} HTTP ${p.status}`);
      prompts[path] = await p.text();
    }
  }
  m.prompts = prompts;
  return { manifest: m, prompts };
}

const WIDGET2TYPE = { text: "text", textarea: "textarea", slider: "slider", select: "select", number: "number", file: "file" };
function normField(f){
  return { key: f.name || f.key, type: WIDGET2TYPE[f.widget] || f.widget || f.type,
           label: humanize(f.name || f.key || ""), required: f.required,
           min: f.min, max: f.max, step: f.step, default: f.default, options: f.options, suffix: f.suffix,
           placeholder: f.placeholder, hint: f.hint || f.description };
}
function humanize(k){
  const t = String(k).replace(/_/g, " ");
  return t.replace(/\bs\b$/, "(s)").replace(/^length$/, "Length (s)");
}

export function renderField(f, value){
  const id = esc("fld-" + f.key);
  const lab = `<label for="${id}">${esc(f.label)}${f.hint ? ` <span class="note">· ${esc(f.hint)}</span>` : ""}</label>`;
  switch(f.type){
    case "textarea":
      return `<div>${lab}<textarea id="${id}" rows="4" placeholder="${esc(f.placeholder||"")}">${esc(value??"")}</textarea></div>`;
    case "text":
      return `<div>${lab}<input type="text" id="${id}" placeholder="${esc(f.placeholder||"")}"></div>`;
    case "number":
      return `<div>${lab}<input type="number" id="${id}" min="${esc(f.min??0)}" max="${esc(f.max??1000)}" step="${esc(f.step||1)}" value="${esc(value??f.default??"")}"></div>`;
    case "slider": {
      const v = value ?? f.default ?? f.min ?? 0;
      return `<div>${lab}<input type="range" id="${id}" min="${esc(f.min)}" max="${esc(f.max)}" step="${esc(f.step||1)}" value="${esc(v)}" data-suffix="${esc(f.suffix||"")}"><span class="range-out" id="${id}-out">${esc(v)}${esc(f.suffix||"")}</span></div>`;
    }
    case "model":
      return `<div>${lab}<input type="search" data-model-filter="${id}" aria-controls="${id}" aria-label="Filter ${esc(f.label)} models" placeholder="Type to filter models…"><select id="${id}" required><option value="">Choose exact model…</option>${routableModels(get().catalog).map(m=>`<option value="${esc(m.id)}"${m.id===value?' selected':''}>${esc(m.id)} · $${esc(typeof m.promptPerMillionUsd==='number'?Number(m.promptPerMillionUsd.toPrecision(3)):'unknown')} input / $${esc(typeof m.completionPerMillionUsd==='number'?Number(m.completionPerMillionUsd.toPrecision(3)):'unknown')} output per 1M tokens</option>`).join('')}</select></div>`;
    case "select":
      return `<div>${lab}<select id="${id}">${(f.options||[]).map(o=>`<option value="${esc(o.value??o)}">${esc(o.label??o)}</option>`).join("")}</select></div>`;
    default:
      return "";
  }
}

function collectValues(manifest){
  const vals = {};
  for(const f0 of manifest.ui?.fields || []){
    const f = normField(f0);
    const el = document.getElementById("fld-" + f.key);
    if(!el) continue;
    vals[f.key] = el.type === "number" || el.type === "range" ? Number(el.value) : el.value;
  }
  return vals;
}

export { runFlow, renderTemplate } from '../flow.js';
import { runFlow, renderTemplate } from '../flow.js';

function budgetPreflight(manifest, catalog, modelId, renderedChars){
  const estTokens = Math.ceil(renderedChars / 4);
  if(modelId === "auto") return { ok: true, est: null };
  const m = catalog?.models?.find(x => x.id === modelId.split(":")[0]);
  if(!m) return { ok: true, est: null };
  const est = (estTokens * 2 / 1e6) * ((m.promptPerMillionUsd||0) + (m.completionPerMillionUsd||0));
  const ceiling = manifest.runtime?.max_cost_per_call_usd;
  if(ceiling != null && est > ceiling) return { ok: false, est, ceiling };
  return { ok: true, est };
}

export function view(){
  return `<div class="page-heading"><div class="eyebrow">WORKSPACE</div><h2>Flows</h2><p>Start with an outcome. Let the steps take care of the rest.</p></div>
    <section class="gallery-section" aria-labelledby="gallery-title"><div class="section-heading"><h3 id="gallery-title">Community templates</h3><span class="note">Use with your own Singular key</span></div>
    <div class="skill-grid" id="grid" role="region" aria-label="Flow templates" tabindex="0"><p class="note">Loading templates…</p></div></section>
    <div class="gallery-foot"><span>01 / Choose a flow</span><span>02 / Add your context</span><span>03 / Review the result</span></div>
    <p class="privacy-note">A draft, not an autopilot. Nothing is researched on the web or sent on your behalf.</p>`;
}

export async function bind(root){
  const grid = root.querySelector("#grid");
  const cards = [];
  for(const id of SKILL_INDEX){
    try{
      const { manifest } = await loadSkill(id);
      cards.push({ id, manifest });
    }catch(e){ console.warn("skill load failed", id, e); }
  }
  grid.innerHTML = cards.length ? cards.map((c, i) => `
    <button type="button" class="skill-card" data-i="${i}">
      <span class="template-top"><span class="tag">${c.manifest.runtime?.video ? 'Plan + explicit video' : c.manifest.runtime?.graph ? '5–6 AI calls' : c.manifest.runtime?.steps ? `${c.manifest.runtime.steps.length} AI steps` : '1 AI step'} · your key</span><span class="template-arrow" aria-hidden="true">↗</span></span>
      <span class="template-title">${esc(c.manifest.name || c.id)}</span>
      <span class="skill-desc">${c.manifest.runtime?.video ? 'Review a draft plan, then generate and download here. Release-gated.' : c.manifest.runtime?.graph ? 'Compare three answers blind. Find the winner and best value.' : c.manifest.runtime?.steps ? 'Turn your prospect notes into an email and two follow-ups.' : 'Turn a video idea into a timed, shoot-ready shot list.'}</span>
      <span class="template-bottom">${esc(c.manifest.author?.name || 'Community')}<span>Open flow →</span></span>
      <span class="skill-id pro-only">${esc(c.manifest.id)}@${esc(c.manifest.version)}</span>
    </button>`).join('') : '<p role="alert">Templates could not be loaded. Reload to try again.</p>';
  grid.querySelectorAll(".skill-card").forEach(el =>
    el.onclick = () => openRunner(cards[Number(el.dataset.i)]));
}

function openRunner({ id, manifest }){
  if(manifest.runtime?.video)return openVideoRunner();
  if(manifest.runtime?.graph)return openGraphRunner({id,manifest},renderField);
  const fields = (manifest.ui?.fields || []).map(normField);
  const req = Object.fromEntries(Object.entries(manifest.inputs || {}).map(([k, v]) => [k, v.required]));
  fields.forEach(f => {
    if(req[f.key] != null) f.required = req[f.key];
    f.hint ||= manifest.inputs?.[f.key]?.description;
    f.default ??= manifest.inputs?.[f.key]?.default;
  });
  if(manifest.runtime?.steps){
    const fieldHtml=f=>renderField(f,f.default);
    return openFlowRunner({id,manifest},fields,fields.filter(f=>f.required).map(fieldHtml).join('')+`<details class="more-details"><summary>More details <span class="note">· optional</span></summary><div class="optional-fields">${fields.filter(f=>!f.required).map(fieldHtml).join('')}</div></details>`,collectValues);
  }
  openModal(`
    <h3 style="font-family:var(--disp);margin-bottom:4px">${esc(manifest.name || id)}</h3>
    <div class="kv pro-only" style="margin-bottom:14px">${esc(manifest.id)}@${esc(manifest.version)} · model: ${esc(manifest.runtime?.model_policy?.prefer || "auto")} · ceiling ≤${fmtUsd(manifest.runtime?.max_cost_per_call_usd)}</div>
    ${!get().settings.apiKey?'<div class="key-note"><strong>Add your Singular key to run</strong><p>Get your key at <a href="https://singular.impossibuild.ai/" target="_blank" rel="noopener noreferrer">Singular → Settings ↗</a>, then add it in <a href="#/settings" id="shell-settings">shell Settings</a>.</p></div>':''}
    <div class="panel-ui" id="panel" style="margin-top:20px">
      ${fields.map(f => renderField(f)).join("")}
    </div>
    <div style="display:flex;gap:10px;margin-top:16px">
      <button class="btn" id="run" style="flex:1" ${get().settings.apiKey?'':'disabled'}>Run flow →</button>
      <button class="btn ghost pro-only" id="preview">Preview prompt</button>
    </div>
    <div id="skout" style="margin-top:14px"></div>`, (modal, close) => {
    modal.querySelectorAll('input[type=range]').forEach(r => {
      r.addEventListener("input", () => {
        const out = modal.querySelector("#fld-" + r.id.slice(4) + "-out");
        if(out) out.textContent = r.value + (r.dataset.suffix || "");
      });
    });
    const out = modal.querySelector("#skout");
    modal.querySelector("#preview").onclick = () => {
      const vals = collectValues(manifest);
      const rendered = renderTemplate(manifest.prompts[manifest.entry?.user_template] || "", vals);
      out.innerHTML = `<div class="card"><h3>Rendered user prompt</h3><div class="mono" style="font-size:12px;white-space:pre-wrap;color:var(--dim)">${esc(rendered)}</div></div>`;
    };
    modal.querySelector("#run").onclick = async () => {
      const s = get();
      if(!s.settings.apiKey){ toast("set mr_ key in Settings first", "err"); return; }
      const vals = collectValues(manifest);
      const missing = fields.filter(f => f.required && !String(vals[f.key] ?? "").trim());
      if(missing.length){ toast("missing: " + missing.map(f => f.label).join(", "), "err"); return; }
      const userTpl = manifest.entry?.user_template;
      const userMsg = renderTemplate(manifest.prompts[userTpl] || "", vals);
      const sysMsg = (manifest.entry?.system || "").startsWith("inline:")
        ? manifest.entry.system.slice("inline:".length)
        : (manifest.prompts[manifest.entry?.system] || "");
      const model = manifest.runtime?.model_policy?.prefer || "auto";
      const check = budgetPreflight(manifest, s.catalog, model, sysMsg.length + userMsg.length);
      if(!check.ok){
        out.innerHTML = `<div class="card" style="border-color:var(--red)">🛑 budget pre-flight: est ${fmtUsd(check.est)} > skill ceiling ${fmtUsd(check.ceiling)} — call refused before sending.</div>`;
        return;
      }
      const btn = modal.querySelector("#run");
      btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> running…';
      try{
        const { content, receipt } = await chatOnce(
          [{ role: "system", content: sysMsg }, { role: "user", content: userMsg }],
          { model, maxTokens: manifest.runtime?.max_output_tokens || 2048 });
        out.innerHTML = `<div class="card"><h3>Output</h3><div style="white-space:pre-wrap;font-size:14px">${esc(content)}</div>
          <div class="receipt" style="margin-top:10px">${esc(receipt.requested)} · ${receipt.prompt_tokens ?? "?"}→${receipt.completion_tokens ?? "?"} tok · ${receipt.estCost != null ? fmtUsd(receipt.estCost) : "cost —"}${receipt.caveat ? " · ⚠ " + esc(receipt.caveat) : ""}</div></div>`;
      }catch(e){
        out.innerHTML = `<div class="card" style="border-color:var(--red)">✗ [${esc(e.kind||"error")}] ${esc(e.message)}</div>`;
      }finally{
        btn.disabled = false; btn.textContent = "Run skill ▸";
      }
    };
  });
}
