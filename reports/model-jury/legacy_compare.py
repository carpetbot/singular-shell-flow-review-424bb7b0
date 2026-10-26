"""Compare actual legacy browser request bodies with the approved base; offline only."""
from pathlib import Path
import difflib
import hashlib
import http.server
import importlib.util
import json
import threading
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT.parent/'base-e064eeb'
REPORT=ROOT/'reports/model-jury'
catalog=json.loads((ROOT/'reports/catalog-live.json').read_text())
outputs=[{'company_does':'Widgets','signals':[]},{'fit_score':4,'reason':'Specific signal'},{'email':{'subject':'team plans','body':'Offline fixture only'},'follow_ups':[]},{'verdict':'pass','issues':[]},{'legacy':'shot list'}]

def capture(root):
 spec=importlib.util.spec_from_file_location('legacy_proxy',root/'proxy.py');proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 calls=[];errors=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=browser.new_context()
   def route(r):
    u=urlsplit(r.request.url)
    if u.path=='/pricing.json':r.fulfill(json=catalog)
    elif u.path=='/v1/chat/completions':
     body=r.request.post_data_json;calls.append(body);out=outputs[len(calls)-1]
     r.fulfill(json={'model':body['model'],'choices':[{'message':{'content':json.dumps(out)}}],'usage':{'prompt_tokens':15,'completion_tokens':20,'total_tokens':35}})
    elif u.hostname=='127.0.0.1':r.continue_()
    else:r.abort()
   context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(f'http://127.0.0.1:{server.server_port}/#/skills');page.wait_for_selector('.skill-card');page.get_by_role('button',name='Pro',exact=True).click()
   page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-fixture-not-a-real-key';}")
   page.locator('.skill-card').filter(has_text='prospect-to-cold-email').click()
   for key in ('prospect_name','company','research_notes','your_offer','sender_name'):page.locator('#fld-'+key).fill('Example '+key)
   page.locator('#preview').click();assert not calls
   page.locator('#run').click();page.wait_for_selector('#skout .audit-badge.pass');assert len(calls)==4
   page.keyboard.press('Escape');page.locator('.skill-card').filter(has_text='motion-trimmer').click();page.locator('#fld-topic').fill('Legacy topic');page.locator('#preview').click();assert len(calls)==4
   page.locator('#run').click();page.wait_for_function("document.querySelector('#skout').textContent.includes('shot list')");assert len(calls)==5;assert not errors,errors
   browser.close()
 finally:server.shutdown();server.server_close();thread.join()
 return calls

before=capture(BASE);after=capture(ROOT)
for label,body in [('base',before),('current',after)]:
 (REPORT/f'legacy-{label}-bodies.offline.json').write_text(json.dumps(body,indent=2)+'\n')
diff=''.join(difflib.unified_diff(json.dumps(before,indent=2).splitlines(True),json.dumps(after,indent=2).splitlines(True),fromfile='e064eeb',tofile='model-jury-graph'))
(REPORT/'legacy-request-bodies.diff').write_text(diff)
assert before==after,diff
protected=['js/flow.js','js/api.js','js/store.js','proxy.py']+[str(p.relative_to(BASE)) for p in (BASE/'skills').rglob('*') if p.is_file()]
hashes=[]
for name in protected:
 a=(BASE/name).read_bytes();b=(ROOT/name).read_bytes();assert a==b,name
 hashes.append({'file':name,'base_sha256':hashlib.sha256(a).hexdigest(),'current_sha256':hashlib.sha256(b).hexdigest(),'byte_identical':True})
(REPORT/'protected-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(json.dumps({'fixture':'Offline Chromium requests, no paid calls','cold_email_requests_equal':len(before[:4]),'motion_trimmer_requests_equal':len(before[4:]),'diff_bytes':len(diff),'protected_files_identical':len(hashes)},indent=2))
