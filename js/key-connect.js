// Uses the existing settings lifecycle. Connecting never validates or submits a call.
import {get,setSettings} from './store.js';
export function keyConnectMarkup(){
 return get().settings.apiKey.trim()?'<p>Key connected · runs save to My work</p>':`<form class="inline-key-form"><strong>Connect your Singular key</strong><label for="inline-key">Singular key</label><div class="inline-key-actions"><input id="inline-key" type="password" autocomplete="off" spellcheck="false" maxlength="4096" required><button type="submit" class="btn" id="inline-connect">Connect</button></div><p class="note">Saved in this browser’s Settings. Connecting does not make a paid call.</p><p class="note" id="inline-key-status" role="status"></p></form>`;
}
export function bindKeyConnect(root){
 const form=root.querySelector('.inline-key-form');if(!form)return()=>{};
 const connect=event=>{event.preventDefault();const input=form.querySelector('#inline-key'),key=input.value.trim();
  if(!key||key.length>4096||/[\s\u0000-\u001f\u007f]/.test(key)){form.querySelector('#inline-key-status').textContent='Enter a valid key without spaces.';return;}
  input.value='';setSettings({apiKey:key});
 };
 form.addEventListener('submit',connect);return()=>form.removeEventListener('submit',connect);
}
