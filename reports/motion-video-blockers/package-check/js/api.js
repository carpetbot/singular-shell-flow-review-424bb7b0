// Singular gateway client (same-origin via proxy.py). Encodes the real contract
// verified 2026-10-14 against singular.impossibuild.ai docs + live probes:
//  - model:"auto" difficulty routing; models:[] ordered fallback (extension)
//  - routing_profiles eco|auto|premium|agentic ; suffixes :nitro|:floor|:exacto
//  - provider constraints (maxPrice etc.); cost receipts impossible for auto
//  - stream_options ignored => no final usage chunk on streams
import { get } from "./store.js";

const IGNORED = ["tool_choice","seed","n","stop","logprobs","user","modalities","audio","reasoning_effort"];

export function priceOf(id, cat){
  if(!cat) return null;
  const base = id.split(":")[0];
  const m = cat.models.find(x => x.id === base);
  if(!m) return null;
  return { id: m.id, name: m.name, kind: m.kind, prompt: m.promptPerMillionUsd, completion: m.completionPerMillionUsd };
}

export function estCost(u, cat, id){
  const p = priceOf(id, cat);
  if(!p || ![p.prompt,p.completion,u.prompt_tokens,u.completion_tokens].every(v=>typeof v==='number' && Number.isFinite(v) && v>=0)) return null;
  return (u.prompt_tokens*p.prompt + u.completion_tokens*p.completion)/1e6;
}

function headers(){
  const h = { "Content-Type": "application/json" };
  const k = get().settings.apiKey.trim();
  if(k) h.Authorization = "Bearer " + k;
  return h;
}

export async function loadCatalog(){
  const r = await fetch("/pricing.json", { headers: { "Accept": "application/json" } });
  if(!r.ok) throw new Error("pricing.json " + r.status);
  return await r.json();
}

function buildBody(messages, opts = {}){
  const s = get().settings;
  const model = opts.model || s.model || "auto";
  const body = { model, messages, stream: !!opts.stream };
  if(opts.stream !== undefined) body.stream = opts.stream;
  if(s.maxCostUsd && parseFloat(s.maxCostUsd) > 0 && model !== "auto"){
    // ceiling is client-side pre-flight in the SDK; on the wire it's maxPrice below
  }
  const prof = opts.routingProfile || s.routingProfile;
  if(prof && prof !== "auto") body.routing_profile = prof;
  if(Array.isArray(opts.models) && opts.models.length) body.models = opts.models;
  const mx = parseFloat(s.maxCostUsd);
  if(!isNaN(mx) && mx > 0 && body.routing){ }
  if(!isNaN(mx) && mx > 0) body.routing = { maxPrice: mx };
  if(opts.responseFormat === 'json') body.response_format = { type: 'json_object' };
  body.max_tokens = opts.maxTokens ?? 2048;
  IGNORED.forEach(() => {}); // fields we never send: gateway ignores them anyway
  return body;
}

export async function chatOnce(messages, opts = {}){
  const r = await fetch("/v1/chat/completions", {
    method: "POST", signal: opts.signal, headers: headers(), body: JSON.stringify(buildBody(messages, {...opts, stream:false})),
  });
  const data = await r.json().catch(() => ({error: {message: "non-JSON response " + r.status}}));
  if(!r.ok){
    const msg = (data.error && data.error.message) || r.status;
    const err = new Error(msg);
    err.status = r.status;
    err.kind = r.status === 401 ? "auth" : (r.status === 402 || /balance|insufficient/i.test(msg) ? "balance" : /no eligible|not routable/i.test(msg) ? "no-model" : "api");
    if(data.usage){
      const requested=data.model || opts.model || get().settings.model;
      err.receipt={requested,...data.usage,estCost:estCost(data.usage,get().catalog,requested),caveat:'HTTP error usage receipt; cost is an estimate, not a charge'};
    }
    throw err;
  }
  const choice = data.choices[0];
  const u = data.usage || {};
  const cat = get().catalog;
  const reqModel = data.model || buildBody([],opts).model;
  const receipt = {
    requested: reqModel,
    prompt_tokens: u.prompt_tokens, completion_tokens: u.completion_tokens,
    total_tokens: u.total_tokens,
    estCost: u.prompt_tokens != null ? estCost(u, cat, reqModel) : null,
    caveat: reqModel === "auto" ? "auto: gateway does not disclose the resolved upstream — cost unestimable client-side" : null,
  };
  return { content: choice.message.content, receipt };
}

export async function chatStream(messages, opts = {}, onDelta){
  const r = await fetch("/v1/chat/completions", {
    method: "POST", headers: {...headers(), "Accept": "text/event-stream"},
    body: JSON.stringify(buildBody(messages, {...opts, stream:true})),
  });
  if(!r.ok){
    const data = await r.json().catch(() => ({}));
    const msg = (data.error && data.error.message) || ("HTTP " + r.status);
    const err = new Error(msg);
    err.status = r.status;
    err.kind = r.status === 401 ? "auth" : /balance|insufficient/i.test(msg) ? "balance" : "api";
    throw err;
  }
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = "", full = "", usage = null;
  while(true){
    const {done, value} = await reader.read();
    if(done) break;
    buf += dec.decode(value, {stream:true});
    const parts = buf.split("\n\n"); buf = parts.pop();
    for(const p of parts){
      for(const line of p.split("\n")){
        if(!line.startsWith("data:")) continue;
        const d = line.slice(5).trim();
        if(d === "[DONE]") continue;
        try{
          const j = JSON.parse(d);
          const delta = j.choices && j.choices[0] && j.choices[0].delta && j.choices[0].delta.content;
          if(delta){ full += delta; onDelta(delta, full); }
          if(j.usage) usage = j.usage; // stream_options ignored upstream => usually absent
        }catch(e){}
      }
    }
  }
  const cat = get().catalog;
  const reqModel = opts.model || get().settings.model || "auto";
  const receipt = {
    requested: reqModel,
    prompt_tokens: usage?.prompt_tokens, completion_tokens: usage?.completion_tokens,
    estCost: usage ? estCost(usage, cat, reqModel) : null,
    caveat: usage ? null : "stream: gateway does not echo final usage (stream_options ignored) — token counts unavailable",
  };
  return { content: full, receipt };
}
