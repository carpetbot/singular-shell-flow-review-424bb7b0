// Chat view: streaming against the gateway, receipts honestly labeled.
import { get, pushMsg, replaceLast, clearChat, setSettings } from "../store.js";
import { chatStream } from "../api.js";
import { esc, toast, fmtUsd } from "../ui.js";

let sending = false;

function receiptHTML(r){
  if(!r) return "";
  const bits = [];
  bits.push(`<b>${esc(r.requested)}</b>`);
  if(r.prompt_tokens != null) bits.push(`${r.prompt_tokens}→${r.completion_tokens} tok`);
  bits.push(r.estCost != null ? "est " + fmtUsd(r.estCost) : "cost —");
  if(r.caveat) bits.push("⚠ " + esc(r.caveat));
  return `<div class="receipt">${bits.join(" · ")}</div>`;
}

export function view(){
  const s = get();
  const msgs = s.chat.map(m => {
    if(m.role === "note") return `<div class="msg system-note">${esc(m.content)}</div>`;
    return `<div class="msg ${m.role}">${esc(m.content)}</div>` + (m.receipt ? receiptHTML(m.receipt) : "");
  }).join("");
  return `
    <div class="card" style="display:flex;gap:10px;align-items:center;padding:10px 16px">
      <span class="kv">routing:</span>
      <select id="qmodel" style="width:auto;flex:0 1 260px">
        <option value="auto">auto (difficulty-scored)</option>
        ${(s.catalog?.models||[]).filter(m=>["chat","text"].includes(m.kind)&&m.routable).slice(0,120).map(m=>`<option ${s.settings.model===m.id?"selected":""} value="${esc(m.id)}">${esc(m.id)}</option>`).join("")}
      </select>
      <select id="qprof" style="width:auto">
        ${["auto","eco","premium","agentic"].map(p=>`<option ${s.settings.routingProfile===p?"selected":""} value="${p}">${p}</option>`).join("")}
      </select>
      <button class="btn ghost sm" id="clear">clear</button>
    </div>
    <div id="chatlog">${msgs || '<div class="msg system-note">Skeleton demo — messages stream from Singular via the local proxy. Set your mr_ key in Settings.</div>'}</div>
    <div id="composer">
      <textarea id="input" placeholder="Ask anything… (⏎ send, ⇧⏎ newline)"></textarea>
      <button class="btn" id="send">Send ▸</button>
    </div>`;
}

export function bind(root){
  const sel = root.querySelector("#qmodel");
  if(sel) sel.onchange = () => setSettings({ model: sel.value });
  const prof = root.querySelector("#qprof");
  if(prof) prof.onchange = () => setSettings({ routingProfile: prof.value });
  root.querySelector("#clear").onclick = () => { clearChat(); rerender(); };
  const input = root.querySelector("#input");
  input.onkeydown = e => { if(e.key === "Enter" && !e.shiftKey){ e.preventDefault(); send(); } };
  root.querySelector("#send").onclick = send;
  input.focus();
  const log = root.querySelector("#chatlog");
  log.scrollTop = log.scrollHeight;
}

function rerender(){
  const root = document.getElementById("view");
  root.innerHTML = view(); bind(root);
}

async function send(){
  if(sending) return;
  const s = get();
  const text = document.getElementById("input").value.trim();
  if(!text) return;
  if(!s.settings.apiKey){ toast("set your mr_ API key in Settings first", "err"); location.hash = "#/settings"; return; }
  sending = true;
  pushMsg({ role: "user", content: text });
  pushMsg({ role: "assistant", content: "" });
  const holder = document.querySelector("#chatlog").lastElementChild;
  document.getElementById("input").value = "";
  const history = get().chat.slice(0, -1).filter(m => m.role !== "note");
  try{
    const { content, receipt } = await chatStream(history, {}, (delta, full) => {
      holder.textContent = full;
    });
    replaceLast({ role: "assistant", content, receipt });
    rerender();
  }catch(e){
    replaceLast({ role: "note", content: `✗ [${e.kind || "error"}] ${e.message}${e.kind==="balance"?" — top up balance, do not retry":""}` });
    rerender();
    toast(e.message, "err");
  }finally{ sending = false; }
}
