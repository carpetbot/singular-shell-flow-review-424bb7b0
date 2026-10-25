import { get } from './store.js';
import { esc as escapeHtml, fmtUsd, openModal, toast } from './ui.js';
// Credentials never belong in prompt/output inspection, even if pasted into notes.
function esc(value){
  const key=get().settings.apiKey;
  const text=String(value??'');
  return escapeHtml(key?text.split(key).join('[key redacted]'):text);
}
import { runFlow, renderTemplate, promptText, readPath } from './flow.js';

const costLabel = value => value == null ? 'unknown' : fmtUsd(value);
function attemptSummary(attempts=[]){
  if(!attempts.length)return '— → — tok · estimated — · 0 attempt(s)';
  const unknown=attempts.some(a=>a.estCost==null);
  const cost=unknown?null:attempts.reduce((n,a)=>n+a.estCost,0);
  const tokens=key=>attempts.some(a=>a[key]==null)?'?':attempts.reduce((n,a)=>n+a[key],0);
  return `${tokens('prompt_tokens')} → ${tokens('completion_tokens')} tok · estimated ${costLabel(cost)} · ${attempts.length} attempt(s)`;
}
function plain(value){return typeof value==='string'?value:JSON.stringify(value,null,2);}
function copyBlock(label,value){
  const text=plain(value) ?? '';
  return `<div class="card output-card"><div class="output-header"><strong>${esc(label)}</strong><button class="btn ghost sm" data-copy="${esc(text)}" aria-label="Copy ${esc(label)}">Copy</button></div><pre>${esc(text)}</pre></div>`;
}
function outputBlock(path,value){
  if(value==null)return `<div class="note">${esc(path)} · unavailable (step skipped or failed)</div>`;
  if(path.endsWith('.email') && typeof value==='object')return copyBlock('Subject',value.subject)+copyBlock('Email body',value.body);
  if(path.endsWith('.follow_ups') && Array.isArray(value))return value.map((v,i)=>copyBlock(`Follow-up ${i+1} · after ${v.send_after_days} days`,v.body)).join('');
  return copyBlock(path,value);
}
export function renderBreakdown(manifest,ctx=null){
  const cards=manifest.runtime.steps.map((step,index)=>{
    const state=readPath(ctx,`steps.${step.id}`);
    const attempts=state?.attempts || [];
    const status=state?.status || 'waiting';
    let system,user;
    try{system=promptText(manifest,step.system);user=promptText(manifest,step.user_template);}
    catch(error){system='Template unavailable: '+error.message;user='';}
    const references=[...new Set([...`${system}\n${user}`.matchAll(/\{\{\s*([\w.]+)\s*\}\}/g)].map(m=>m[1]))];
    const actual=state?.receipt?.requested;
    const fallback=actual && actual!==step.model ? ((step.fallback || []).includes(actual)?'Fallback used':'Different receipt model') : attempts.length?'Primary route':'Not run';
    const cost=status==='skipped' || !attempts.length ? '—' : attempts.some(a=>a.estCost==null)?'unknown':costLabel(attempts.reduce((sum,a)=>sum+a.estCost,0));
    const rendered=ctx && !['waiting','skipped'].includes(status)?`<details><summary>Run-context prompts</summary><p class="note">Base prompts rendered with this run’s inputs and prior outputs. Conditional repair messages are not stored here.</p><pre>${esc(renderTemplate(system,ctx))}\n\n${esc(renderTemplate(user,ctx))}</pre></details>`:'';
    return `<article class="step-card" data-breakdown="${esc(step.id)}"><h4>${index+1}. ${esc(step.plain_label || step.label || step.id)} <span class="tag">${esc(status)}</span></h4><div class="model-id">Requested: ${esc(step.model)}</div>${step.why?`<p class="step-why">${esc(step.why)}</p>`:''}<p class="step-meta">Reads: ${esc(references.join(' · ') || 'No input references')}</p><p class="step-meta">Receipt model: ${esc(actual || 'Not available')} · ${esc(fallback)}</p><p class="step-meta">${esc(attemptSummary(attempts))} · Step cost: <span data-step-cost="${esc(step.id)}">${esc(cost)}</span></p><p class="step-summary">${esc(state?.output?'Output excerpt: '+state.output.slice(0,240)+(state.output.length>240?'…':''):'No output yet.')}</p>${state?.error?`<p class="next-action">${esc(state.error)}</p>`:''}<details><summary>Raw JSON / output and receipts</summary><pre>${esc(state?.output || 'No output recorded.')}</pre>${attempts.map((receipt,i)=>`<div class="receipt">Attempt ${i+1} · ${esc(receipt.requested)} · ${esc(receipt.prompt_tokens??'?')} → ${esc(receipt.completion_tokens??'?')} tok · estimated ${esc(costLabel(receipt.estCost))}${receipt.caveat?' · '+esc(receipt.caveat):''}</div>`).join('')}</details><details><summary>Original prompt templates</summary><pre>${esc(system)}\n\n${esc(user)}</pre></details>${rendered}</article>`;
  }).join('');
  return `<section class="breakdown pro-only"><h4>Flow breakdown</h4><p class="note">Selection rationale, not measured performance rankings. Receipt models are echoed by the gateway when available, otherwise the requested model. Costs are estimates across all attempts.</p>${cards}</section>`;
}
export function renderFlowResult(manifest,ctx){
  const check=readPath(ctx,'steps.check');
  const verdict=check?.status==='done'?readPath(check,'json.verdict'):null;
  const audit=verdict==='pass'?'AI check passed — review before sending':verdict==='fix'?'Check found issues':'Not checked';
  const issues=verdict==='fix'?readPath(check,'json.issues'):null;
  const issueHtml=Array.isArray(issues)?`<ul class="audit-issues">${issues.map(issue=>`<li>${esc(plain(issue))}</li>`).join('')}</ul>`:'';
  const outputs=(manifest.runtime.output?.show || []).filter(path=>!path.startsWith('check.')).map(path=>{
    const [id,...keys]=path.split('.');
    const value=readPath(readPath(ctx,`steps.${id}.json`),keys.join('.'));
    if(value==null)return '';
    if(path==='angle.reason')return `<p class="note">Why this angle: ${esc(plain(value))}</p>`;
    return outputBlock(path,value);
  }).join('');
  const raw=Object.entries(ctx.steps).map(([id,s])=>`<h4>${esc(id)}</h4><pre>${esc(s.output)}</pre><div>${esc(attemptSummary(s.attempts))}</div>${s.attempts.map((r,i)=>`<div class="receipt">attempt ${i+1}: ${esc(r.requested)} · ${esc(r.prompt_tokens??'?')} → ${esc(r.completion_tokens??'?')} tok · estimated ${esc(costLabel(r.estCost))} ${esc(r.caveat || '')}</div>`).join('')}`).join('');
  const next=ctx.status==='stopped'?'Add a stronger signal in your notes, then run again.':ctx.status==='failed'?'Review the error, check your key and pricing, then retry when ready. A retry starts a new run.':'';
  return `<div class="result-heading"><h3>${ctx.status==='done'?'Your draft':'Run '+esc(ctx.status)}</h3><span class="audit-badge ${verdict==='pass'?'pass':verdict==='fix'?'fix':''}">${esc(audit)}</span></div><div class="result-status"><p>${esc(ctx.error || ctx.message || 'Draft ready. Review every claim before sending.')}</p>${next?`<p class="next-action">${esc(next)}</p>`:''}<p>Total estimated cost: ${esc(costLabel(ctx.estCost))}. Usage receipts are not billed charges.</p><p class="note">This is a model audit of your notes, not independent factual verification.</p></div>${issueHtml}${outputs}${renderBreakdown(manifest,ctx)}<details class="pro-only"><summary>Raw all-step outputs and attempts</summary>${raw}</details>`;
}
export function openFlowRunner({id,manifest},fields,fieldsHtml,collect){
  const steps=manifest.runtime.steps;
  openModal(`<div class="runner-heading"><div><div class="eyebrow">COMMUNITY FLOW · ${steps.length} AI STEPS</div><h3>${esc(manifest.name || id)}</h3></div><button class="btn ghost close-modal" aria-label="Close flow">✕</button></div><p class="runner-intro">Your notes in. A considered first draft out.</p><p class="note">No web research or email sending. Costs are estimates, not a guaranteed billing cap.</p>${!get().settings.apiKey?'<div class="key-note"><strong>Add your Singular key to run</strong><p>Open <a href="https://singular.impossibuild.ai/" target="_blank" rel="noopener noreferrer">Singular → Settings ↗</a> to get your key, then add it in <a href="#/settings" id="shell-settings">shell Settings</a>. You can explore the form without a key.</p></div>':''}<div class="runner-workspace"><div class="configure-pane"><div class="form-heading"><h4>Your context</h4><button class="btn ghost sm" id="sample" type="button">Try with sample</button></div><p id="sample-note" class="note" hidden>Fictional example · review or replace before running.</p><div class="panel-ui">${fieldsHtml}</div><ol id="flow-steps">${steps.map(s=>`<li data-step="${esc(s.id)}" data-status="waiting"><strong>${esc(s.plain_label || s.label || s.id)}</strong><span class="step-state">waiting</span><span class="pro-only">${esc(s.model)}</span></li>`).join('')}</ol><div class="run-actions"><button class="btn" id="run" ${get().settings.apiKey?'':'disabled'}>Run flow →</button><button class="btn ghost pro-only" id="preview">Preview first step</button><span class="note">Only runs when you choose.</span></div><div id="skout" style="margin-top:14px"></div></div><div id="flow-inspect">${renderBreakdown(manifest)}</div></div>`,(modal,close)=>{
    modal.querySelector('.close-modal').onclick=close;
    modal.querySelector('#shell-settings')?.addEventListener('click',close);
    modal.querySelector('#sample').onclick=()=>{
      const example={prospect_name:'Mara Example',company:'Paper Moon Kites (fictional)',research_notes:'Fictional example: Paper Moon Kites is an imaginary paper kite studio. Its fictional founder Mara is opening a second studio and is looking for a simple opening checklist. No real company or person is described.',your_offer:'A simple launch checklist for small creative studios.',sender_name:'Alex Example',prospect_role:'Fictional founder',your_proof:'',ask:'reply'};
      for(const [key,value] of Object.entries(example)){
        const el=modal.querySelector('#fld-'+key);if(el)el.value=value;
      }
      modal.querySelector('#sample-note').hidden=false;
    };
    const out=modal.querySelector('#skout'),btn=modal.querySelector('#run');
    modal.querySelector('#preview').onclick=()=>{
      try{
        const ctx={...collect(manifest),steps:Object.create(null)};const s=steps[0];
        out.innerHTML=`<h4>First step preview only · ${esc(s.label)}</h4><pre style="white-space:pre-wrap">${esc(renderTemplate(promptText(manifest,s.system),ctx))}\n\n${esc(renderTemplate(promptText(manifest,s.user_template),ctx))}</pre>`;
      }catch(error){out.textContent=error.message;}
    };
    btn.onclick=async()=>{
      const vals=collect(manifest);
      const missing=fields.filter(f=>f.required && !String(vals[f.key]??'').trim());
      if(missing.length){toast('missing: '+missing.map(f=>f.label).join(', '),'err');return;}
      if(!get().settings.apiKey){toast('Set API key in Settings first','err');return;}
      btn.disabled=true;btn.textContent='Running…';
      modal.querySelector('#preview').disabled=true;
      modal.querySelector('#sample').disabled=true;
      const snapshot={...vals,steps:Object.create(null)};
      const inspect=modal.querySelector('#flow-inspect');
      out.innerHTML='<p class="note" role="status">Running your flow. You can switch Lite / Pro without interrupting it.</p>';
      try{
        const ctx=await runFlow(manifest,vals,event=>{
          const el=[...modal.querySelectorAll('#flow-steps li')].find(el=>el.dataset.step===event.id);
          const s=steps.find(s=>s.id===event.id);
          el.dataset.status=event.status;
          snapshot.steps[event.id]=event;
          const stepCost=event.status==='skipped' || !event.attempts?.length?'—':event.attempts.some(a=>a.estCost==null)?'unknown':costLabel(event.attempts.reduce((sum,a)=>sum+a.estCost,0));
          el.innerHTML=`<strong>${esc(s.plain_label || s.label || s.id)}</strong><span class="step-state">${esc(event.status)}</span><span class="step-cost">${esc(stepCost)}</span><span class="pro-only">${esc(event.receipt?.requested || s.model)}</span>${event.error?`<span>${esc(event.error)}</span>`:''}`;
          inspect.innerHTML=renderBreakdown(manifest,snapshot);
        });
        out.innerHTML=renderFlowResult(manifest,ctx);
        inspect.replaceChildren(out.querySelector('.breakdown'));
        out.querySelectorAll('[data-copy]').forEach(button=>button.onclick=async()=>{
          try{await navigator.clipboard.writeText(button.dataset.copy);toast('Copied');}catch{toast('Clipboard unavailable; select and copy the text','err');}
        });
      }catch(error){out.textContent=error.message;}
      finally{btn.disabled=false;btn.textContent='Run flow →';modal.querySelector('#preview').disabled=false;modal.querySelector('#sample').disabled=false;}
    };
  });
}
