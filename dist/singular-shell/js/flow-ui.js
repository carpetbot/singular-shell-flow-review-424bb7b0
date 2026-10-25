import { get } from './store.js';
import { esc, fmtUsd, openModal, toast } from './ui.js';
import { runFlow, renderTemplate, promptText, readPath } from './flow.js';

const costLabel = value => value == null ? 'unknown' : fmtUsd(value);
function attemptSummary(attempts=[]){
  const unknown=attempts.some(a=>a.estCost==null);
  const cost=unknown?null:attempts.reduce((n,a)=>n+a.estCost,0);
  const tokens=key=>attempts.some(a=>a[key]==null)?'?':attempts.reduce((n,a)=>n+a[key],0);
  return `${tokens('prompt_tokens')} → ${tokens('completion_tokens')} tok · estimated ${costLabel(cost)} · ${attempts.length} attempt(s)`;
}
function plain(value){return typeof value==='string'?value:JSON.stringify(value,null,2);}
function copyBlock(label,value){
  const text=plain(value) ?? '';
  return `<div class="card"><strong>${esc(label)}</strong> <button class="btn ghost" data-copy="${esc(text)}">Copy</button><pre style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(text)}</pre></div>`;
}
function outputBlock(path,value){
  if(value==null)return `<div class="note">${esc(path)} · unavailable (step skipped or failed)</div>`;
  if(path.endsWith('.email') && typeof value==='object')return copyBlock('Subject',value.subject)+copyBlock('Email body',value.body);
  if(path.endsWith('.follow_ups') && Array.isArray(value))return value.map((v,i)=>copyBlock(`Follow-up ${i+1} · after ${v.send_after_days} days`,v.body)).join('');
  return copyBlock(path,value);
}
export function renderFlowResult(manifest,ctx){
  const outputs=(manifest.runtime.output?.show || []).map(path=>{
    const [id,...keys]=path.split('.');
    return outputBlock(path,readPath(ctx.steps[id]?.json,keys.join('.')));
  }).join('');
  const raw=Object.entries(ctx.steps).map(([id,s])=>`<h4>${esc(id)}</h4><pre style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(s.output)}</pre><div>${esc(attemptSummary(s.attempts))}</div>${s.attempts.map((r,i)=>`<div class="receipt">attempt ${i+1}: ${esc(r.requested)} · ${esc(r.prompt_tokens??'?')} → ${esc(r.completion_tokens??'?')} tok · estimated ${esc(costLabel(r.estCost))} ${esc(r.caveat || '')}</div>`).join('')}`).join('');
  return `<div class="card"><h3>Flow ${esc(ctx.status)}</h3><p>${esc(ctx.message || ctx.error || '')}</p><p>Total estimated cost: ${esc(costLabel(ctx.estCost))}. Usage receipts are not billed charges.</p></div>${outputs}<details><summary>Raw all-step outputs and attempts</summary>${raw}</details>`;
}
export function openFlowRunner({id,manifest},fields,fieldsHtml,collect){
  const steps=manifest.runtime.steps;
  openModal(`<h3>${esc(manifest.name || id)}</h3><p class="note">Notes to draft only. No web research or email sending. Costs are estimates, not a guaranteed billing cap.</p><div class="panel-ui">${fieldsHtml}</div><ol id="flow-steps">${steps.map(s=>`<li data-step="${esc(s.id)}" data-status="waiting"><strong>${esc(s.label || s.id)}</strong> · waiting · ${esc(s.model)}</li>`).join('')}</ol><button class="btn" id="run">Run flow ▸</button> <button class="btn ghost" id="preview">Preview first step</button><div id="skout" style="margin-top:14px"></div>`,modal=>{
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
      try{
        const ctx=await runFlow(manifest,vals,event=>{
          const el=[...modal.querySelectorAll('#flow-steps li')].find(el=>el.dataset.step===event.id);
          const s=steps.find(s=>s.id===event.id);
          el.dataset.status=event.status;
          el.innerHTML=`<strong>${esc(s.label || s.id)}</strong> · ${esc(event.status)} · ${esc(event.receipt?.requested || s.model)}<div class="receipt">${esc(attemptSummary(event.attempts))}${event.error?' · '+esc(event.error):''}</div>`;
        });
        out.innerHTML=renderFlowResult(manifest,ctx);
        out.querySelectorAll('[data-copy]').forEach(button=>button.onclick=async()=>{
          try{await navigator.clipboard.writeText(button.dataset.copy);toast('Copied');}catch{toast('Clipboard unavailable; select and copy the text','err');}
        });
      }catch(error){out.textContent=error.message;}
      finally{btn.disabled=false;btn.textContent='Run flow ▸';}
    };
  });
}
