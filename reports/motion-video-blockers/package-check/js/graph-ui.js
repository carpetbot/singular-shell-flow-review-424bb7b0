import {get} from './store.js';
import {esc as escapeHtml,fmtUsd,openModal} from './ui.js';
function esc(value){const key=get().settings.apiKey;return escapeHtml(key?String(value??'').split(key).join('[key redacted]'):String(value??''));}
const cost=value=>value==null?'unknown':fmtUsd(value);
const json=value=>esc(JSON.stringify(value,null,2));
export function renderGraphResult(manifest,ctx){
 const tally=ctx.steps.tally?.status==='done'?ctx.steps.tally.json:null;
 const finished=ctx.status==='done' && tally;
 const card=(title,slot)=>{if(!slot)return `<article class="card"><h4>${title}</h4><p>Unavailable: no qualifying answer with known cost.</p></article>`;const row=tally.ranking.find(r=>r.slot===slot),node=manifest.runtime.graph.find(n=>n.id===slot);return `<article class="card jury-answer"><h4>${title}</h4><p>${esc(ctx[node.model_from_input])} · Score ${esc(row.avg)} / 5 · ${esc(cost(row.cost_usd))}</p><pre>${esc(ctx.steps[slot].output)}</pre><button class="btn ghost sm" data-copy="${esc(ctx.steps[slot].output)}">Copy answer</button></article>`;};
 let result=`<h3>${finished?'Comparison complete':'Run '+esc(ctx.status)}</h3><p role="status">${esc(ctx.error||ctx.message||'One judge’s opinion, not independent factual verification. Review the evidence.')}</p><p>Total estimated cost: ${esc(cost(ctx.estCost))}. Estimates are not billed charges or a guaranteed cap.</p>`;
 if(finished){
  result+=card('Winner',tally.best_overall)+`<p><strong>Judge’s stated reason:</strong> ${esc(ctx.steps.judge.json.reason||'Not supplied.')}</p><p class="note">This reason may differ from the code-verified ranking after quote checks, must-have failures or careful-pass averaging.</p>`+card('Best value',tally.best_value);
  const winner=tally.ranking.find(r=>r.slot===tally.best_overall),value=tally.ranking.find(r=>r.slot===tally.best_value);
  if(winner && winner.slot===value?.slot)result+='<p>The winner is also the best value.</p>';
  else if(winner?.cost_usd>0 && value?.cost_usd!=null)result+=`<p>${esc(Math.max(0,(1-value.cost_usd/winner.cost_usd)*100).toFixed(1))}% cheaper than the winner; within 0.5 points.</p>`;
  result+=`<details><summary>Other answers</summary>${tally.ranking.filter(r=>r.slot!==tally.best_overall && r.slot!==tally.best_value).map(r=>card('Answer '+r.rank,r.slot)).join('')||'<p>No additional ranked answer.</p>'}</details>`;
  result+=`<section class="pro-only"><h4>Rubric</h4><pre>${json(ctx.steps.rubric.json)}</pre><h4>Score table · verified quotes and weighted scores</h4><table><thead><tr><th>Rank / slot</th><th>Score</th><th>Cost</th><th>Evidence</th></tr></thead><tbody>${tally.ranking.map(r=>`<tr><td>${esc(r.rank)} · ${esc(r.slot)}</td><td>${esc(r.avg)}</td><td>${esc(cost(r.cost_usd))}</td><td><pre>${json({criteria:r.criteria,quote_failures:r.quote_failures,must_haves_failed:r.must_haves_failed,judges:[ctx.steps.judge.json,ctx.steps.judge_reversed?.json].filter(Boolean).map(j=>j.scores.find(s=>ctx.steps.blind.private_map[String(s.answer)]===r.slot))})}</pre></td></tr>`).join('')}</tbody></table><h4>Slot map · revealed after judging</h4><pre>${json(Object.fromEntries(Object.entries(ctx.steps.blind.private_map).map(([label,slot])=>[label,{slot,model:ctx[manifest.runtime.graph.find(n=>n.id===slot).model_from_input]}])))}</pre><h4>Disagreement flags</h4><pre>${json(tally.disagreements)}</pre></section>`;
 }
 const failures=Object.entries(ctx.steps).filter(([,s])=>s.error).map(([id,s])=>{const node=manifest.runtime.graph.find(n=>n.id===id);return node?.on_fail==='continue_as_no_answer'?`<p class="next-action">${esc(ctx[node.model_from_input])}: no answer (${s.receipt?.httpStatus?'gateway error '+esc(s.receipt.httpStatus):'gateway error'})</p><p class="pro-only">${esc(id)}: ${esc(s.error)}</p>`:`<p class="next-action">${esc(id)}: ${esc(s.error)}</p>`;}).join('');
 return result+failures+`<section class="pro-only"><h4>Per-node receipts · costs and tokens</h4>${Object.entries(ctx.steps).map(([id,s])=>`<details><summary>${esc(id)} · ${esc(s.status)} · ${s.attempts.length?esc(cost(s.receipt?.estCost)):'—'}</summary><pre>${json(s.attempts)}</pre></details>`).join('')}</section>`;
}

import {runGraph,graphPreflight} from './graph.js';
export function openGraphRunner({id,manifest},renderField){
 const fields=Object.entries(manifest.inputs).map(([key,s])=>({key,...s,label:key.replaceAll('_',' '),hint:s.description,type:s.type==='string'?'textarea':s.type}));
 const html=fields.map(f=>f.type==='boolean'?`<label><input type="checkbox" id="fld-${esc(f.key)}" ${f.default?'checked':''}> ${esc(f.label)} · ${esc(f.hint)}</label>`:renderField(f,f.default)).join('');
 openModal(`<div class="runner-heading"><h3>${esc(manifest.name||id)}</h3><button class="btn ghost close-modal" aria-label="Close flow">✕</button></div><p>Compare three anonymous answers. One judge’s opinion, not independent factual verification.</p><p class="note">5 calls, or 6 with careful mode. Estimates are not a guaranteed billing cap. No web research or sending.</p>${!get().settings.apiKey?'<div class="key-note">Add your Singular key in <a href="#/settings" id="shell-settings">Settings</a> to run.</div>':''}<div class="panel-ui">${html}<label for="jury-cap">Required numeric run estimate cap (USD)</label><input id="jury-cap" type="number" min="0" step="0.01" required value="${esc(manifest.runtime.max_cost_per_run_usd)}"></div><p id="jury-estimate" role="status">Choose every model to estimate this run.</p><ol id="jury-progress">${manifest.runtime.graph.map(n=>`<li data-node="${esc(n.id)}"><strong>${esc(n.id)}</strong> <span>waiting</span></li>`).join('')}</ol><button class="btn" id="run" ${get().settings.apiKey?'':'disabled'}>Run comparison →</button><div id="skout"></div>`,(modal,close)=>{
  modal.querySelector('.close-modal').onclick=close;modal.querySelector('#shell-settings')?.addEventListener('click',close);
  modal.querySelectorAll('[data-model-filter]').forEach(search=>search.addEventListener('input',()=>{
   const select=modal.querySelector('#'+search.dataset.modelFilter),query=search.value.toLowerCase();
   for(const option of select.options)option.hidden=!!option.value && option.value!==select.value && !option.value.toLowerCase().includes(query);
  }));
  const collect=()=>Object.fromEntries(fields.map(f=>{const el=modal.querySelector('#fld-'+f.key);return [f.key,f.type==='boolean'?el.checked:el.value];}));
  const selectedManifest=()=>{const cap=modal.querySelector('#jury-cap').value;return {...manifest,runtime:{...manifest.runtime,max_cost_per_run_usd:cap.trim()?Number(cap):NaN}};};
  const estimate=()=>{try{const amount=graphPreflight(selectedManifest(),collect(),get().catalog);modal.querySelector('#jury-estimate').textContent='Estimated maximum route: '+cost(amount)+' (heuristic, not billed cost)';}catch(error){modal.querySelector('#jury-estimate').textContent=error.message;}};
  modal.querySelectorAll('select,input,textarea').forEach(el=>el.addEventListener('change',estimate));
  modal.querySelector('#run').onclick=async()=>{
   const vals=collect(),out=modal.querySelector('#skout'),button=modal.querySelector('#run');
   const missing=fields.filter(f=>f.required&&!String(vals[f.key]??'').trim());
   if(missing.length){out.textContent='Required: '+missing.map(f=>f.label).join(', ');return;}
   if(!get().settings.apiKey){out.textContent='Add a key in Settings first.';return;}
   button.disabled=true;modal.querySelectorAll('select,input,textarea').forEach(el=>el.disabled=true);
   try{const ctx=await runGraph(selectedManifest(),vals,e=>{const row=[...modal.querySelectorAll('[data-node]')].find(el=>el.dataset.node===e.id);row.querySelector('span').textContent=e.status+(e.error?' · '+e.error:'');});out.innerHTML=renderGraphResult(manifest,ctx);out.querySelectorAll('[data-copy]').forEach(el=>el.onclick=async()=>{try{await navigator.clipboard.writeText(el.dataset.copy);el.textContent='Copied';}catch{el.textContent='Select text to copy';}});}catch(error){out.textContent=error.message;}finally{button.disabled=false;modal.querySelectorAll('select,input,textarea').forEach(el=>el.disabled=false);}
  };
 });
}
