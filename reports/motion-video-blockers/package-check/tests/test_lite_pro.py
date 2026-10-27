"""Offline real-Chromium acceptance tests. Never contacts a gateway."""
import http.server
import importlib.util
import json
import os
from pathlib import Path
import threading
import unittest
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT=Path(os.environ.get('SINGULAR_UI_APP_ROOT',str(ROOT)))
spec = importlib.util.spec_from_file_location('lite_proxy', APP_ROOT/'proxy.py')
assert spec and spec.loader
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

class LitePro(unittest.TestCase):
    def setUp(self):
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1',0), proxy.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        self.context = self.browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'])
        self.pause_first=False; self.pending=None
        self.calls=[]; self.errors=[]; self.blocked=[]
        self.catalog=json.loads((ROOT/'reports/catalog-live.json').read_text())
        self.outputs=[{'company_does':'Fictional paper kite studio','signals':['Opening a fictional second studio']}, {'fit_score':4,'reason':'A specific studio opening in the supplied notes'}, {'email':{'subject':'A lighter studio opening','body':'Hi Mara,\n\nYour notes mention a second studio. Could our launch checklist help?\n\nAlex'},'follow_ups':[{'send_after_days':3,'body':'Would a sample launch checklist be useful?'},{'send_after_days':7,'body':'Happy to leave this here if now is not the right time.'}]}, {'verdict':'pass','issues':[]}]
        self.context.route('**/*', self.route)
        self.page=self.context.new_page()
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.browser.close();self.pw.stop()
        self.server.shutdown();self.server.server_close();self.thread.join()
    def route(self,r):
        path=urlsplit(r.request.url).path
        if path=='/pricing.json': r.fulfill(json=self.catalog)
        elif path=='/v1/chat/completions':
            body=r.request.post_data_json;self.calls.append(body)
            if self.pause_first and len(self.calls)==1:
                self.pending=r
                return
            output=self.outputs[(len(self.calls)-1)%len(self.outputs)]
            r.fulfill(json={'model':body['model'],'choices':[{'message':{'content':json.dumps(output)}}],'usage':{'prompt_tokens':15,'completion_tokens':20,'total_tokens':35}})
        elif urlsplit(r.request.url).hostname=='127.0.0.1':r.continue_()
        else:self.blocked.append(r.request.url);r.abort()
    def gallery(self,route=''):
        self.page.goto(self.url+'/'+route)
        self.page.wait_for_selector('.skill-card')
    def mode(self,value):
        self.page.get_by_role('button',name=value,exact=True).click()
    def test_01_mode_default_persistence_and_guarded_routes(self):
        self.gallery('#/skills')
        self.assertEqual(self.page.locator('html').get_attribute('data-mode'),'lite')
        self.assertEqual(self.page.locator('#rail a:visible').all_text_contents(),['Flows','Settings'])
        self.assertEqual(self.page.locator('#syncbanner').evaluate('el=>getComputedStyle(el).display'),'none')
        self.assertIn('Flows',self.page.locator('h2').inner_text())
        self.mode('Pro')
        self.assertEqual(self.page.locator('#rail a:visible').all_text_contents(),['Flows','Chat','Models','Settings'])
        self.page.reload();self.page.wait_for_selector('.skill-card')
        self.assertEqual(self.page.locator('html').get_attribute('data-mode'),'pro')
        self.mode('Lite')
        self.page.goto(self.url+'/#/chat')
        self.page.wait_for_selector('.skill-card')
        self.assertEqual(self.page.locator('#chatlog').count(),0)
        self.page.goto(self.url+'/#/models')
        self.page.wait_for_selector('.skill-card')
        self.assertEqual(self.calls,[])
        self.assertEqual(self.errors,[])

    def test_02_gallery_and_fictional_sample_preserve_inputs(self):
        self.gallery()
        self.assertEqual(self.page.locator('.skill-card').count(),4)
        self.assertEqual(self.page.locator('.skill-card').first.evaluate('e=>e.tagName'),'BUTTON')
        self.assertNotIn('skeleton',self.page.locator('#view').inner_text())
        self.assertNotIn('ui:panel',self.page.locator('#view').inner_text())
        self.assertIn('4 AI steps · your key',self.page.locator('#view').inner_text())
        self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.assertIn('Add your Singular key to run',self.page.locator('.modal').inner_text())
        self.assertEqual(self.page.locator('.key-note a[target=_blank]').get_attribute('href'),'https://singular.impossibuild.ai/')
        self.assertFalse(self.page.locator('#fld-prospect_role').is_visible())
        self.assertFalse(self.page.locator('#preview').is_visible())
        self.assertTrue(self.page.locator('#run').is_disabled())
        self.page.get_by_role('button',name='Try with sample').click()
        self.assertIn('Fictional example',self.page.locator('.modal').inner_text())
        before=self.page.locator('#fld-research_notes').input_value()
        self.assertIn('fictional',before.lower())
        self.assertEqual(self.calls,[])
        self.mode('Pro')
        self.assertEqual(self.page.locator('#fld-research_notes').input_value(),before)
        self.assertTrue(self.page.locator('#preview').is_visible())
        self.page.locator('#preview').click()
        self.assertIn(before,self.page.locator('#skout').inner_text())
        self.page.get_by_text('More details',exact=False).click()
        self.assertTrue(self.page.locator('#fld-prospect_role').is_visible())
        self.page.locator('#fld-your_proof').fill('A fictional proof point')
        self.mode('Lite')
        self.assertEqual(self.page.locator('#fld-your_proof').input_value(),'A fictional proof point')
        self.assertEqual(self.calls,[])
        self.assertNotIn(before,self.page.evaluate('JSON.stringify(localStorage)'))
        self.assertEqual(self.errors,[])

    def test_03_toggle_midrun_retains_form_and_result_with_exactly_four_calls(self):
        self.gallery()
        self.page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-fixture-not-a-real-key';}")
        self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.page.get_by_role('button',name='Try with sample').click()
        self.assertEqual(self.page.locator('#flow-steps strong').all_text_contents(),['Reading your notes','Finding the angle','Writing the email','Fact-checking'])
        self.mode('Pro')
        self.assertGreater(self.page.locator('.modal').bounding_box()['width'],1000)
        self.assertGreater(self.page.locator('#flow-inspect').bounding_box()['x'],self.page.locator('.panel-ui').bounding_box()['x']+self.page.locator('.panel-ui').bounding_box()['width'])
        self.assertEqual(self.page.locator('#flow-inspect .step-card').count(),4)
        self.assertIn('google/gemini-3.8-flash',self.page.locator('#flow-inspect').inner_text())
        self.page.locator('#flow-inspect details').filter(has_text='Original prompt templates').first.locator('summary').click()
        self.assertIn('You extract facts',self.page.locator('#flow-inspect').inner_text())
        self.mode('Lite')
        self.pause_first=True
        self.page.locator('#run').click()
        self.page.wait_for_selector('#flow-steps li[data-status=running]')
        self.assertEqual(len(self.calls),1)
        notes=self.page.locator('#fld-research_notes').input_value()
        self.mode('Pro');self.mode('Lite');self.mode('Pro')
        self.assertEqual(len(self.calls),1)
        self.assertEqual(self.page.locator('#fld-research_notes').input_value(),notes)
        self.pending.fulfill(json={'model':self.calls[0]['model'],'choices':[{'message':{'content':json.dumps(self.outputs[0])}}],'usage':{'prompt_tokens':15,'completion_tokens':20,'total_tokens':35}})
        self.page.wait_for_selector('#skout .audit-badge.pass')
        self.assertEqual(len(self.calls),4)
        self.assertEqual(self.page.locator('#flow-steps li[data-status=done]').count(),4)
        self.assertIn('AI check passed — review before sending',self.page.locator('#skout').inner_text())
        self.assertEqual(self.page.locator('#skout [data-copy]').count(),4)
        self.assertIn('steps.extract.output',self.page.locator('#flow-inspect').inner_text())
        self.page.locator('#skout [data-copy]').first.click()
        self.assertEqual(self.page.evaluate('navigator.clipboard.readText()'),'A lighter studio opening')
        self.mode('Lite')
        self.assertFalse(self.page.locator('#flow-inspect .breakdown').is_visible())
        self.assertNotIn('google/gemini',self.page.locator('.modal').inner_text())
        self.assertNotIn('offline-fixture-not-a-real-key',self.page.locator('.modal').inner_html())
        self.assertEqual(len(self.calls),4)
        self.assertNotIn(notes,self.page.evaluate('JSON.stringify(localStorage)'))
        self.assertEqual(self.errors,[])

    def test_04_mobile_accessible_dialog_and_lite_settings(self):
        self.page.set_viewport_size({'width':390,'height':844})
        self.gallery()
        self.assertGreaterEqual(self.page.get_by_role('button',name='Lite',exact=True).bounding_box()['height'],44)
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
        self.page.locator('.skill-card').first.focus();self.page.keyboard.press('Enter')
        self.assertEqual(self.page.get_by_role('dialog').count(),1)
        self.assertIn('Add your Singular key to run',self.page.locator('.modal').inner_text())
        self.assertNotIn('ceiling',self.page.locator('.modal').inner_text())
        self.assertFalse(self.page.locator('#preview').is_visible())
        box=self.page.locator('.modal').bounding_box()
        self.assertGreaterEqual(box['x'],0);self.assertLessEqual(box['x']+box['width'],390)
        self.page.keyboard.press('Escape')
        self.assertTrue(self.page.locator('.skill-card').first.evaluate('e=>document.activeElement===e'))
        self.page.locator('#tabbar a[data-nav=settings]').click()
        self.page.wait_for_selector('#apikey')
        text=self.page.locator('#view').inner_text()
        self.assertNotIn('skeleton',text);self.assertNotIn('Sheeki',text)
        self.assertNotIn('Routing defaults',text)
        self.assertEqual(self.page.locator('#apikey').get_attribute('type'),'password')
        self.assertEqual(self.calls,[])
        self.assertEqual(self.errors,[])

    def test_05_untrusted_status_and_catalog_are_plain_text(self):
        self.catalog['models'][0]['maxContextTokens']='<img src=x onerror=alert(1)>'
        self.gallery()
        self.page.evaluate("async()=>{window.__catalogError='<img src=x onerror=alert(1)>';const {syncBanner}=await import('/js/chrome.js');syncBanner();}")
        self.assertEqual(self.page.locator('#syncbanner img').count(),0)
        self.assertIn('<img',self.page.locator('#syncbanner').inner_text())
        self.mode('Pro')
        self.page.locator('#rail a[data-nav=models]').click()
        self.page.wait_for_selector('#tbl td')
        self.assertEqual(self.page.locator('#tbl img').count(),0)
        self.assertIn('<img',self.page.locator('#tbl').inner_text())
        self.assertEqual(self.calls,[]);self.assertEqual(self.errors,[])
    def test_06_missing_catalog_models_has_recovery_not_skeleton(self):
        self.context.unroute('**/*', self.route)
        def failed_catalog(r):
            if urlsplit(r.request.url).path=='/pricing.json':r.fulfill(status=503,json={'error':'offline fixture'})
            else:self.route(r)
        self.context.route('**/*',failed_catalog)
        self.gallery()
        self.assertTrue(self.page.locator('#syncbanner').is_visible())
        self.assertIn('Retry pricing before running',self.page.locator('#syncbanner').inner_text())
        self.mode('Pro');self.page.locator('#rail a[data-nav=models]').click()
        self.page.wait_for_timeout(100)
        self.assertEqual(self.page.locator('#view .skel').count(),0)
        self.assertIn('Retry',self.page.locator('#view').inner_text())
        self.assertEqual(self.calls,[]);self.assertEqual(self.errors,[])

    def test_07_fallback_actual_receipt_and_unknown_usage_failure(self):
        self.gallery()
        self.page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-fixture-not-a-real-key';}")
        self.context.unroute('**/*',self.route)
        successful=[]
        def fallback(r):
            if urlsplit(r.request.url).path!='/v1/chat/completions':self.route(r);return
            body=r.request.post_data_json;self.calls.append(body)
            if len(self.calls)==1:r.fulfill(status=503,json={'error':{'message':'Offline fixture: primary unavailable'}});return
            output=self.outputs[len(successful)];successful.append(body)
            r.fulfill(json={'model':body['model'],'choices':[{'message':{'content':json.dumps(output)}}],'usage':{'prompt_tokens':15,'completion_tokens':20}})
        self.context.route('**/*',fallback)
        self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.page.get_by_role('button',name='Try with sample').click();self.page.locator('#run').click()
        self.page.wait_for_selector('#skout .audit-badge.pass')
        self.assertEqual(len(self.calls),5)
        self.mode('Pro')
        first=self.page.locator('[data-breakdown=extract]')
        self.assertIn('Fallback used',first.inner_text())
        self.assertIn('Receipt model: deepseek/deepseek-v4.1-flash-1017',first.inner_text())
        self.assertIn('2 attempt(s)',first.inner_text())
        self.page.keyboard.press('Escape')
        self.calls.clear();self.context.unroute('**/*',fallback)
        def unknown(r):
            if urlsplit(r.request.url).path!='/v1/chat/completions':self.route(r);return
            body=r.request.post_data_json;self.calls.append(body)
            r.fulfill(json={'model':body['model'],'choices':[{'message':{'content':json.dumps(self.outputs[0])}}]})
        self.context.route('**/*',unknown)
        self.mode('Lite');self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.page.get_by_role('button',name='Try with sample').click();self.page.locator('#run').click()
        self.page.wait_for_selector('#skout .next-action')
        self.assertEqual(len(self.calls),1)
        self.assertIn('Not checked',self.page.locator('#skout').inner_text())
        self.assertIn('Total estimated cost: unknown',self.page.locator('#skout').inner_text())
        self.assertEqual(self.page.locator('#flow-steps li[data-status=skipped] .step-cost').all_text_contents(),['—','—','—'])
        self.assertEqual(self.errors,[])
    def test_08_check_failure_leaves_draft_and_not_checked(self):
        self.gallery()
        self.page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-fixture-not-a-real-key';}")
        self.context.unroute('**/*',self.route)
        def fail_check(r):
            if urlsplit(r.request.url).path=='/v1/chat/completions' and len(self.calls)==3:
                self.calls.append(r.request.post_data_json)
                r.fulfill(status=401,json={'error':{'message':'Offline fixture: check refused'}})
            else:self.route(r)
        self.context.route('**/*',fail_check)
        self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.page.get_by_role('button',name='Try with sample').click();self.page.locator('#run').click()
        self.page.wait_for_selector('#skout .next-action')
        self.assertEqual(len(self.calls),4)
        self.assertIn('Not checked',self.page.locator('#skout').inner_text())
        self.assertIn('check refused',self.page.locator('#skout').inner_text())
        self.assertIn('A lighter studio opening',self.page.locator('#skout').inner_text())
        self.assertNotIn('AI check passed',self.page.locator('#skout').inner_text())
        self.assertEqual(self.errors,[])
    def test_09_exact_seven_review_screenshots(self):
        destination=Path(os.environ.get('VIDEO_LITE_EVIDENCE',str(ROOT/'reports/review')));destination.mkdir(exist_ok=True)
        shots=[]
        def shot(name):
            path=destination/name
            self.page.screenshot(path=str(path),full_page=False,animations='disabled')
            shots.append({'file':str(path.relative_to(ROOT)),'mode':self.page.locator('html').get_attribute('data-mode'),'viewport':self.page.viewport_size,'fixture':'Explicit offline model responses; no real inference or key'})
        def align(selector):
            self.page.locator('.modal').evaluate('(modal,selector)=>{const target=modal.querySelector(selector);modal.scrollTop+=target.getBoundingClientRect().top-modal.getBoundingClientRect().top-24}',selector)
        self.gallery()
        shot('01-lite-gallery.png')
        self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.page.get_by_role('button',name='Try with sample').click()
        shot('02-lite-form.png')
        self.page.keyboard.press('Escape')
        self.page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-fixture-not-a-real-key';const {renderTopbar}=await import('/js/chrome.js');renderTopbar();}")
        self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.page.get_by_role('button',name='Try with sample').click();self.page.locator('#run').click()
        self.page.wait_for_selector('#skout .audit-badge.pass')
        align('#skout');shot('03-lite-completed-result.png')
        self.mode('Pro')
        align('#skout');shot('06-pro-completed-breakdown.png')
        self.page.keyboard.press('Escape');self.page.locator('h2').click();shot('04-pro-gallery.png')
        self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.page.get_by_role('button',name='Try with sample').click()
        self.page.locator('.modal').evaluate('(el)=>el.scrollTop=0');shot('05-pro-form-breakdown.png')
        self.page.keyboard.press('Escape')
        self.mode('Lite');self.page.set_viewport_size({'width':390,'height':844})
        self.page.locator('.skill-card').filter(has_text='Cold Email').click()
        self.page.get_by_role('button',name='Try with sample').click()
        self.calls.clear();self.pause_first=True;self.page.locator('#run').click()
        self.page.wait_for_selector('#flow-steps li[data-status=running]')
        align('#fld-your_offer');shot('07-mobile-lite-form-progress.png')
        self.pending.fulfill(json={'model':self.calls[0]['model'],'choices':[{'message':{'content':json.dumps(self.outputs[0])}}],'usage':{'prompt_tokens':15,'completion_tokens':20}})
        self.page.wait_for_selector('#skout .audit-badge.pass')
        self.assertEqual(len(self.calls),4);self.assertEqual(self.errors,[])
        self.assertEqual(len(shots),7)
        self.assertEqual(len(list(destination.glob('*.png'))),7)
        (destination/'screenshots.json').write_text(json.dumps(sorted(shots,key=lambda shot:shot['file']),indent=2))
        print('Seven offline review screenshots:',destination)

if __name__=='__main__':unittest.main()
