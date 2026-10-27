"""Capture actual three legacy flow POST bodies against 378d6f4. Offline only."""
import hashlib,http.server,importlib.util,json,re,threading
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent;BASE=ROOT.parent/'motion-trimmer-video-base-378d6f4'
catalog=json.loads((ROOT/'reports/catalog-live.json').read_text())
def capture(app):
 spec=importlib.util.spec_from_file_location('legacy_proxy',app/'proxy.py');proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler);threading.Thread(target=server.serve_forever,daemon=True).start();calls=[];errors=[];flow=''
 candidates=[m for m in catalog['models'] if m.get('kind')=='chat' and m.get('routable') is True and re.fullmatch(r'[\w.-]+/[\w.-]+',m['id']) and isinstance(m.get('promptPerMillionUsd'),(int,float)) and isinstance(m.get('completionPerMillionUsd'),(int,float))];families={}
 for m in candidates:families.setdefault(m['id'].split('/')[0],m)
 models=[m['id'] for m in sorted(families.values(),key=lambda m:m['promptPerMillionUsd']+m['completionPerMillionUsd'])[:5]]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);ctx=browser.new_context();ctx.add_init_script('Math.random=()=>0.314159;')
   def route(r):
    u=urlsplit(r.request.url)
    if u.path=='/pricing.json':r.fulfill(json=catalog)
    elif u.path=='/v1/chat/completions':
     b=r.request.post_data_json;calls.append({'flow':flow,'body':b});n=len([c for c in calls if c['flow']==flow]);model=b['model']
     if flow=='cold-email':out=[{'company_does':'Widgets','signals':[]},{'fit_score':4,'reason':'Specific signal'},{'email':{'subject':'team plans','body':'Offline fixture only'},'follow_ups':[]},{'verdict':'pass','issues':[]}][n-1]
     elif flow=='motion-trimmer':out={'legacy':'shot list'}
     elif model==models[4]:out={'criteria':[{'name':'clear','weight':1}],'must_haves':[]}
     elif model==models[3]:out={'scores':[{'answer':str(i),'must_haves_failed':[],'criteria':[{'name':'clear','score':4,'quote':'Offline answer.'}]} for i in [1,2,3]],'reason':'Offline fixture'}
     else:out='Offline answer.'
     r.fulfill(json={'model':model,'choices':[{'message':{'content':json.dumps(out) if not isinstance(out,str) else out}}],'usage':{'prompt_tokens':15,'completion_tokens':20,'total_tokens':35}})
    elif u.hostname=='127.0.0.1':r.continue_()
    else:r.abort()
   ctx.route('**/*',route);page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}/#/skills');page.wait_for_selector('.skill-card');page.get_by_role('button',name='Pro',exact=True).click();page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-fixture-not-real';}")
   flow='cold-email';page.locator('.skill-card').filter(has_text='prospect-to-cold-email').click()
   for key in ['prospect_name','company','research_notes','your_offer','sender_name']:page.locator('#fld-'+key).fill('Example '+key)
   page.locator('#preview').click();assert len(calls)==0;page.locator('#run').click();page.wait_for_selector('#skout .audit-badge.pass');assert len(calls)==4;page.keyboard.press('Escape')
   flow='motion-trimmer';page.locator('.skill-card').filter(has=page.get_by_text('Motion Trimmer',exact=True)).click();page.locator('#fld-topic').fill('Legacy topic');page.locator('#preview').click();assert len(calls)==4;page.locator('#run').click();page.wait_for_function("document.querySelector('#skout').textContent.includes('shot list')");assert len(calls)==5;page.keyboard.press('Escape')
   flow='model-jury';page.locator('.skill-card').filter(has_text='Model Jury').click();page.locator('#fld-task').fill('Recommend a shipping date.')
   for key,model in zip(['contestant_1','contestant_2','contestant_3','judge','rubric_writer'],models):page.locator('#fld-'+key).select_option(model)
   page.locator('#run').click();page.wait_for_function("document.querySelector('#skout').textContent.includes('Comparison complete')");assert len(calls)==10;assert not errors,errors;browser.close()
 finally:server.shutdown();server.server_close()
 return calls
before=capture(BASE);after=capture(ROOT)
for label,bodies in [('base',before),('current',after)]:(REPORT/f'legacy-{label}-bodies.offline.json').write_text(json.dumps(bodies,indent=2)+'\n')
assert before==after,'Actual legacy POST bodies changed'
protected=['js/flow.js','js/flow-ui.js','js/api.js','js/store.js','js/graph.js','js/graph-ui.js','js/ui.js','js/presentation.js','styles.css','index.html']+[str(p.relative_to(BASE)) for p in (BASE/'skills').rglob('*') if p.is_file()]
hashes=[]
for name in protected:
 a=(BASE/name).read_bytes();b=(ROOT/name).read_bytes();assert a==b,name;hashes.append({'file':name,'sha256':hashlib.sha256(b).hexdigest(),'byte_identical':True})
(REPORT/'protected-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(json.dumps({'base':'378d6f4','fixture':'Explicit offline fake inference','cold_email_equal':4,'motion_trimmer_equal':1,'model_jury_equal':5,'protected_byte_identical':len(hashes),'actual_bodies_identical':before==after},indent=2))
