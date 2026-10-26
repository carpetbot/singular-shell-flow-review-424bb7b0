"""Model Jury real Chromium tests: explicit offline fixtures, no paid calls."""
import http.server
import importlib.util
import json
import os
from pathlib import Path
import re
import threading
import unittest
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
APP_ROOT=Path(os.environ.get('JURY_APP_ROOT',str(ROOT)))
REPORT=ROOT/'reports/model-jury'
spec=importlib.util.spec_from_file_location('jury_proxy',APP_ROOT/'proxy.py')
proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)

class ModelJury(unittest.TestCase):
 def setUp(self):
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler)
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
  self.pw=sync_playwright().start();self.browser=self.pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  self.context=self.browser.new_context(viewport={'width':1440,'height':1000})
  self.catalog=json.loads((ROOT/'reports/catalog-live.json').read_text())
  candidates=[m for m in self.catalog['models'] if m.get('kind')=='chat' and m.get('routable') is True and re.fullmatch(r'[\w.-]+/[\w.-]+',m['id']) and isinstance(m.get('promptPerMillionUsd'),(int,float)) and isinstance(m.get('completionPerMillionUsd'),(int,float))]
  chosen={}
  for m in candidates:
   family=m['id'].split('/')[0]
   if family not in chosen:chosen[family]=m
  cheapest=sorted(chosen.values(),key=lambda m:m['promptPerMillionUsd']+m['completionPerMillionUsd'])[:5]
  self.models=[m['id'] for m in cheapest];self.answers=['Ship Friday; fix payments first.','Ship on Friday. The risk is the payment bug.','We could consider many options.']
  self.calls=[];self.errors=[];self.blocked=[];self.failures=0;self.judges=0
  self.context.route('**/*',self.route)
  self.page=self.context.new_page();self.page.set_default_timeout(2500)
  self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.url=f'http://127.0.0.1:{self.server.server_port}'
 def tearDown(self):
  self.browser.close();self.pw.stop();self.server.shutdown();self.server.server_close();self.thread.join()
 def route(self,r):
  u=urlsplit(r.request.url)
  if u.path=='/pricing.json':r.fulfill(json=self.catalog)
  elif u.path=='/v1/chat/completions':
   b=r.request.post_data_json;self.calls.append(b);model=b['model']
   if model in self.models[:self.failures]:r.fulfill(status=500,json={'error':{'message':'Explicit offline HTTP500 fixture'}});return
   if model==self.models[4]:out={'criteria':[{'name':'clear','weight':3},{'name':'short','weight':1}],'must_haves':[]}
   elif model==self.models[3]:
    self.judges+=1;pairs=re.findall(r'Answer ([123]):\n([\s\S]*?)(?=\n\nAnswer [123]:|$)',b['messages'][1]['content'])
    out={'scores':[{'answer':label,'must_haves_failed':[],'criteria':[{'name':'clear','score':3 if self.judges==2 else 5,'quote':answer.strip()},{'name':'short','score':4,'quote':answer.strip()}]} for label,answer in pairs if answer.strip()!='(no answer)'],'reason':'Explicit offline fixture: supported shipping recommendation.'}
   else:out=self.answers[self.models.index(model)]
   if model==self.models[3] and isinstance(out,dict):
    for score in out['scores']:
     if score['criteria'][0]['quote']==self.answers[0]:
      if getattr(self,'must_have_pass',None)==self.judges:score['must_haves_failed']=['under 10 words']
      if getattr(self,'quote_failure_pass',None)==self.judges:
       for criterion in score['criteria']:criterion['quote']='invented words'
   r.fulfill(json={'model':model,'choices':[{'message':{'content':out if isinstance(out,str) else json.dumps(out)}}],'usage':{'prompt_tokens':20,'completion_tokens':20,'total_tokens':40}})
  elif u.hostname=='127.0.0.1':r.continue_()
  else:self.blocked.append(r.request.url);r.abort()
 def open(self):
  self.page.goto(self.url+'/#/skills')
  self.page.wait_for_selector('.skill-card')
  self.page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-fixture-not-a-real-key';}")
  self.page.locator('.skill-card').filter(has_text='Model Jury').click()
  self.page.locator('#fld-task').fill('Recommend a shipping date.')
  for key,model in zip(['contestant_1','contestant_2','contestant_3','judge','rubric_writer'],self.models):self.page.locator('#fld-'+key).select_option(model)
 def run_jury(self):
  self.page.locator('#run').click();self.page.wait_for_selector('#skout h3')
 def test_01_blinded_browser_and_lite_pro(self):
  self.open();self.run_jury()
  self.assertEqual(len(self.calls),5);self.assertIn('Comparison complete',self.page.locator('#skout').inner_text())
  judges=[b for b in self.calls if b['model']==self.models[3]];body=json.dumps(judges[0])
  for token in self.models[:3]+['slot_1','slot_2','slot_3','private_map']:self.assertNotIn(token,body)
  REPORT.mkdir(exist_ok=True);(REPORT/'judge-request.offline.json').write_text(json.dumps({'fixture':'Explicit offline fake replies; not real inference','contestants':self.models[:3],'body':judges[0]},indent=2))
  self.assertFalse(self.page.get_by_text('Slot map · revealed after judging',exact=True).is_visible())
  self.assertIn('Winner',self.page.locator('#skout').inner_text());self.assertIn('Best value',self.page.locator('#skout').inner_text())
  self.page.locator('.modal').evaluate("e=>e.scrollTop=e.scrollHeight")
  self.page.screenshot(path=str(REPORT/'lite-result.offline.png'))
  self.page.get_by_role('button',name='Pro',exact=True).click()
  self.assertTrue(self.page.get_by_text('Slot map · revealed after judging',exact=True).is_visible());self.assertEqual(len(self.calls),5)
  self.page.locator('.modal').evaluate("e=>{const h=[...e.querySelectorAll('h4')].find(h=>h.textContent.startsWith('Score table'));e.scrollTop+=h.getBoundingClientRect().top-e.getBoundingClientRect().top-24;}")
  self.page.screenshot(path=str(REPORT/'pro-result.offline.png'))
  self.assertEqual(self.errors,[])

 def test_02_same_maker_zero_calls(self):
  self.open();self.page.locator('#fld-judge').select_option(self.models[0]);self.run_jury()
  self.assertEqual(self.calls,[]);self.assertIn('different model maker',self.page.locator('#skout').inner_text())
  (REPORT/'same-maker.offline.json').write_text(json.dumps({'calls':len(self.calls),'result':self.page.locator('#skout').inner_text(),'fixture':'Offline Chromium; no inference'},indent=2))
 def test_03_one_http500_ranks_two(self):
  self.failures=1;self.open();self.run_jury()
  self.assertEqual(len(self.calls),5);self.assertIn('Comparison complete',self.page.locator('#skout').inner_text())
  self.page.get_by_role('button',name='Pro',exact=True).click()
  self.assertEqual(self.page.locator('#skout tbody tr').count(),2)
  self.assertIn('HTTP500 fixture',self.page.locator('#skout').inner_text())
  (REPORT/'one-http500.offline.json').write_text(json.dumps({'calls':self.calls,'ranked_answers':2,'result':self.page.locator('#skout').inner_text(),'fixture':'Offline Chromium'},indent=2))
 def test_04_two_http500_stop_before_judge(self):
  self.failures=2;self.open();self.run_jury()
  self.assertEqual(len(self.calls),4);self.assertEqual(self.judges,0)
  self.assertIn('Fewer than 2 models answered',self.page.locator('#skout').inner_text())
  (REPORT/'two-http500.offline.json').write_text(json.dumps({'calls':self.calls,'judge_calls':self.judges,'result':self.page.locator('#skout').inner_text(),'fixture':'Offline Chromium'},indent=2))
 def test_05_careful_exact_extra_call_and_gap_two(self):
  self.open();self.page.locator('#fld-careful_mode').check();self.run_jury()
  self.assertEqual(len(self.calls),6);self.assertEqual(self.judges,2)
  self.page.get_by_role('button',name='Pro',exact=True).click()
  text=self.page.locator('#skout').inner_text();self.assertRegex(text,r'"scores":\s*\[\s*5,\s*3')
  judge_calls=[b for b in self.calls if b['model']==self.models[3]]
  first=re.findall(r'Answer ([123]):\n',judge_calls[0]['messages'][1]['content']);second=re.findall(r'Answer ([123]):\n',judge_calls[1]['messages'][1]['content']);self.assertEqual(first,list(reversed(second)))
  pairs=[dict(re.findall(r'Answer ([123]):\n([\s\S]*?)(?=\n\nAnswer [123]:|$)',b['messages'][1]['content'])) for b in judge_calls]
  self.assertEqual({k:v.strip() for k,v in pairs[0].items()},{k:v.strip() for k,v in pairs[1].items()})
  for b in judge_calls:
   for model in self.models[:3]:self.assertNotIn(model,json.dumps(b))
  (REPORT/'careful.offline.json').write_text(json.dumps({'calls':self.calls,'result':text,'fixture':'Offline Chromium; scores differ by exactly 2'},indent=2))
 def test_06_mobile_no_horizontal_overflow(self):
  self.page.set_viewport_size({'width':390,'height':844});self.open();self.run_jury()
  self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
  self.assertLessEqual(self.page.locator('.modal').evaluate('e=>e.scrollWidth'),self.page.locator('.modal').evaluate('e=>e.clientWidth')+1)
  self.page.get_by_role('button',name='Pro',exact=True).click()
  self.assertLessEqual(self.page.locator('.modal').evaluate('e=>e.scrollWidth'),self.page.locator('.modal').evaluate('e=>e.clientWidth')+1)
  self.page.locator('.modal').evaluate('e=>e.scrollTop=e.scrollHeight')
  self.page.screenshot(path=str(REPORT/'mobile-result.offline.png'))

 def test_07_search_models_preserves_exact_selection_and_excludes_latest(self):
  alias={**self.catalog['models'][0],'id':'fixture/mutable-latest','kind':'chat','routable':True}
  self.catalog['models'].append(alias)
  self.open()
  picker=self.page.locator('#fld-contestant_1')
  self.assertNotIn(alias['id'],picker.locator('option').evaluate_all('(options)=>options.map(o=>o.value)'))
  search=self.page.get_by_role('searchbox',name='Filter contestant 1 models',exact=True)
  self.assertEqual(search.count(),1,'model picker needs a type-to-filter searchbox')
  search.fill(self.models[1].upper())
  visible=picker.locator('option:not([hidden])').evaluate_all('(options)=>options.map(o=>o.value)')
  self.assertIn(self.models[1],visible)
  self.assertLess(len(visible),picker.locator('option').count())
  self.assertEqual(picker.input_value(),self.models[0])
  picker.select_option(self.models[1])
  search.fill('no-such-model-filter')
  self.assertEqual(picker.input_value(),self.models[1])
  search.fill('')
  self.assertEqual(picker.locator('option[hidden]').count(),0)
  self.assertEqual(self.calls,[]);self.assertEqual(self.errors,[])

 def test_08_careful_second_pass_must_have_cannot_win(self):
  self.must_have_pass=2;self.open();self.page.locator('#fld-careful_mode').check();self.run_jury()
  self.assertEqual(len(self.calls),6)
  cards=self.page.locator('#skout > article.jury-answer')
  self.assertEqual(cards.count(),2)
  for card in cards.all():self.assertNotIn(self.models[0],card.inner_text())
  self.page.get_by_role('button',name='Pro',exact=True).click()
  row=self.page.locator('#skout tbody tr').last
  self.assertIn('slot_1',row.inner_text());self.assertIn('under 10 words',row.inner_text())
  flags=self.page.locator('#skout h4').filter(has_text='Disagreement flags').locator('+ pre').inner_text()
  self.assertIn('"must_haves"',flags);self.assertIn('under 10 words',flags)
  self.assertEqual(self.errors,[])

 def test_09_careful_second_pass_quote_error_is_retained_not_disqualified(self):
  self.quote_failure_pass=2;self.open();self.page.locator('#fld-careful_mode').check();self.run_jury()
  self.assertEqual(len(self.calls),6)
  self.page.get_by_role('button',name='Pro',exact=True).click()
  row=self.page.locator('#skout tbody tr').filter(has_text='slot_1')
  evidence=json.loads(row.locator('td').nth(3).inner_text())
  self.assertEqual(evidence['quote_failures'],['clear','short'])
  self.assertEqual(evidence['must_haves_failed'],[])
  self.assertEqual(row.locator('td').nth(1).inner_text(),'3.38')
  self.assertEqual(self.errors,[])

 def test_10_lite_gateway_failure_and_same_winner_value_copy(self):
  self.failures=1;self.open();self.run_jury()
  text=self.page.locator('#skout').inner_text()
  self.assertIn(self.models[0]+': no answer (gateway error 500)',text)
  self.assertNotIn('slot_1:',text);self.assertNotIn('HTTP500 fixture',text)
  self.assertNotRegex(text,r'(?<![\d.])0\.0% cheaper')
  # Force equal result IDs through the real renderer to cover the exact copy.
  html=self.page.evaluate("""async()=>{const {renderGraphResult}=await import('/js/graph-ui.js');
   const manifest={runtime:{graph:[{id:'slot_1',model_from_input:'contestant_1'}]}};
   const ctx={status:'done',contestant_1:'fixture/exact',estCost:0,steps:{tally:{status:'done',attempts:[],json:{best_overall:'slot_1',best_value:'slot_1',ranking:[{slot:'slot_1',avg:5,cost_usd:0}],disagreements:[]}},slot_1:{output:'answer',attempts:[]},rubric:{json:{},attempts:[]},judge:{json:{reason:'fixture',scores:[]},attempts:[]},blind:{private_map:{'1':'slot_1'},attempts:[]}}};
   return renderGraphResult(manifest,ctx);} """)
  self.assertIn('The winner is also the best value.',html);self.assertNotIn('0.0% cheaper',html)
  self.assertEqual(self.errors,[])

if __name__=='__main__':unittest.main()
