// Reactive store: settings + chat history + catalog cache, localStorage-backed.
const KEY = "singular-s…r:1";

function blank(){
  return { v: 1,
    savedAt: Date.now(),
    settings: { apiKey: "", model: "auto", routingProfile: "auto", maxCostUsd: "0.05", stream: true },
    chat: [],           // {role, content, receipt?}
    catalog: null,      // last-fetched pricing.json: {as_of, models:[...]}
  };
}

let state = blank();
const listeners = new Set();
const viewListeners = new Set();
export function subscribe(fn){ listeners.add(fn); return () => listeners.delete(fn); }
export function subscribeView(fn){ viewListeners.add(fn); return () => viewListeners.delete(fn); }
function persist(){ try{ localStorage.setItem(KEY, JSON.stringify({...state, savedAt: Date.now()})); }catch(e){} }
function emit(){ listeners.forEach(fn => fn()); }
function emitView(){ viewListeners.forEach(fn => fn()); }
export function touch(){ persist(); emit(); emitView(); }

export function hydrate(){
  return new Promise(res => {
    setTimeout(() => {
      try{
        const raw = localStorage.getItem(KEY);
        if(raw){
          const snap = JSON.parse(raw);
          if(snap.v === 1){
            const b = blank();
            state = { ...b, ...snap,
              settings: { ...b.settings, ...(snap.settings||{}) },
              chat: Array.isArray(snap.chat) ? snap.chat : [],
              catalog: snap.catalog || null,
            };
          }
        }
      }catch(e){ console.warn("hydrate failed", e); }
      res(state);
    }, 200);
  });
}

export function get(){ return state; }
export function set(partial){ Object.assign(state, partial); touch(); }
export function setSettings(partial){ Object.assign(state.settings, partial); touch(); }
export function pushMsg(m){ state.chat.push(m); touch(); }
export function replaceLast(m){ if(state.chat.length) state.chat[state.chat.length-1] = m; else state.chat.push(m); touch(); }
export function clearChat(){ state.chat = []; touch(); }
