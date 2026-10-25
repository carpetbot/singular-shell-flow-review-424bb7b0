// Settings: key (localStorage only), routing defaults, ceiling, honest limits.
import { get, setSettings, clearChat } from "../store.js";
import { esc, toast } from "../ui.js";

export function view(){
  const s = get().settings;
  return `
    <h2>Settings</h2>
    <div class="card">
      <h3>API key</h3>
      <label>Singular mr_ key</label>
      <input type="password" id="apikey" placeholder="mr_…" value="${esc(s.apiKey)}">
      <div class="note" style="margin-top:8px">Stored only in this browser's localStorage; sent as Bearer on each request through the local proxy. Claim keys at singular.impossibuild.ai → Settings.</div>
      <div style="margin-top:10px;display:flex;gap:8px">
        <button class="btn sm" id="savekey">Save</button>
        <button class="btn sm ghost" id="testkey">Test with 1-token call</button>
      </div>
    </div>
    <div class="card">
      <h3>Routing defaults</h3>
      <div class="panel-ui">
        <div class="row">
          <div><label>Model / pool</label><input type="text" id="model" value="${esc(s.model || "auto")}" placeholder="auto"></div>
          <div><label>Routing profile</label><select id="prof">
            ${["auto","eco","premium","agentic"].map(p=>`<option ${s.routingProfile===p?"selected":""}>${p}</option>`).join("")}
          </select></div>
        </div>
        <div class="row">
          <div><label>Max cost per call (USD, client-side ceiling)</label><input type="text" id="ceiling" value="${esc(s.maxCostUsd)}"></div>
          <div><label>Stream</label><select id="stream"><option ${s.stream?"selected":""} value="1">on</option><option ${!s.stream?"selected":""} value="0">off</option></select></div>
        </div>
        <button class="btn sm" id="savesettings">Save defaults</button>
      </div>
    </div>
    <div class="card">
      <h3>Honest limits of this skeleton</h3>
      <div class="note">
        · <b>auto</b> cost receipts: impossible client-side — the gateway doesn't disclose the resolved upstream.<br>
        · <b>streaming</b>: no final usage chunk (stream_options ignored upstream) — token totals only when non-streamed.<br>
        · <b>tool-bearing skills</b>: refuse to run (P3 sandbox gate).<br>
        · <b>gallery</b>: index hardcoded; real publish/install needs Sheeki's P1 endpoint.<br>
        · Suffixes (<code>:nitro :floor :exacto</code>) pass through; the rest of the contract is in SKILL-MANIFEST-SPEC.md.
      </div>
      <button class="btn sm ghost danger" id="resetall" style="margin-top:10px">Reset local data (chat + settings)</button>
    </div>`;
}

export function bind(root){
  root.querySelector("#savekey").onclick = () => {
    setSettings({ apiKey: root.querySelector("#apikey").value.trim() });
    toast("key saved locally", "ok");
  };
  root.querySelector("#testkey").onclick = async () => {
    const k = root.querySelector("#apikey").value.trim();
    setSettings({ apiKey: k });
    if(!k){ toast("paste a key first", "err"); return; }
    try{
      const { chatOnce } = await import("../api.js");
      const r = await chatOnce([{ role: "user", content: "ping" }], { model: "auto", stream: false, maxTokens: 1 });
      toast("gateway OK — " + r.receipt.requested, "ok");
    }catch(e){ toast("✗ " + (e.kind||"") + ": " + e.message, "err"); }
  };
  root.querySelector("#savesettings").onclick = () => {
    setSettings({
      model: root.querySelector("#model").value.trim() || "auto",
      routingProfile: root.querySelector("#prof").value,
      maxCostUsd: root.querySelector("#ceiling").value,
      stream: root.querySelector("#stream").value === "1",
    });
    toast("defaults saved", "ok");
  };
  root.querySelector("#resetall").onclick = () => {
    localStorage.removeItem("singular-s…r:1");
    clearChat();
    toast("reset — reload to rehydrate", "ok");
  };
}
