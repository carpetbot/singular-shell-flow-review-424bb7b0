"""Real Chromium UI smoke; every gateway call is an offline route fixture."""
import http.server
import importlib.util
import json
from pathlib import Path
import shutil
import threading
import unittest
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ui_proxy',ROOT/'proxy.py')
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

class BrowserSmoke(unittest.TestCase):
    def test_flow_and_legacy_panels_with_offline_gateway(self):
        server = http.server.ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler)
        thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        calls=[]; errors=[]; blocked=[]
        # Recorded public prices, not a network fetch or low-price stand-in.
        catalog=json.loads((ROOT/'reports/catalog-live.json').read_text())
        outputs=[{'company_does':'Widgets','signals':[]},{'fit_score':4,'reason':'Specific signal'}, {'email':{'subject':'team plans','body':'<img src=x onerror=alert(1)> Can I send details?'},'follow_ups':[{'send_after_days':3,'body':'A useful follow-up'},{'send_after_days':7,'body':'Polite close'}]},{'verdict':'fix','issues':[{'where':'email','problem':'Example issue','fix':'Review before sending'}]}]
        def route(r):
            path=urlsplit(r.request.url).path
            if path=='/pricing.json':r.fulfill(json=catalog)
            elif path=='/v1/chat/completions':
                body=r.request.post_data_json; calls.append(body)
                output=outputs[len(calls)-1] if len(calls)<=4 else {'legacy':'shot list'}
                r.fulfill(json={'model':body['model'],'choices':[{'message':{'content':json.dumps(output)}}],'usage':{'prompt_tokens':15,'completion_tokens':20,'total_tokens':35}})
            elif urlsplit(r.request.url).hostname=='127.0.0.1':r.continue_()
            else:blocked.append(r.request.url);r.abort()
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                context=browser.new_context(permissions=['clipboard-read','clipboard-write'])
                context.route('**/*',route)
                page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}/#/skills')
                page.wait_for_selector('.skill-card',timeout=10000)
                page.get_by_role('button',name='Pro',exact=True).click()
                page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-demo';}")
                self.assertEqual(page.locator('.skill-card').count(),2)
                self.assertIn('4 AI steps',page.locator('.skill-card').filter(has_text='prospect-to-cold-email').inner_text())
                page.locator('.skill-card').filter(has_text='prospect-to-cold-email').click()
                self.assertEqual(page.locator('#flow-steps li').count(),4)
                for key in ('prospect_name','company','research_notes','your_offer','sender_name'):
                    page.locator('#fld-'+key).fill('Example '+key)
                page.locator('#preview').click()
                self.assertIn('Example research_notes',page.locator('#skout').inner_text())
                self.assertNotIn('Facts about the prospect:',page.locator('#skout').inner_text())
                self.assertEqual(len(calls),0)
                page.evaluate("async()=>{const {get}=await import('/js/store.js');get().settings.apiKey='offline-demo';}")
                self.assertIn('Run flow',page.locator('#run').inner_text())
                page.locator('#run').click()
                page.wait_for_function("document.querySelector('#skout').textContent.includes('team plans')")
                self.assertEqual(len(calls),4)
                self.assertIn('Widgets',calls[1]['messages'][1]['content'])
                self.assertEqual(calls[2]['response_format'],{'type':'json_object'})
                self.assertEqual(page.locator('#skout img').count(),0)
                self.assertIn('<img',page.locator('#skout').inner_text())
                self.assertIn('Check found issues',page.locator('#skout').inner_text())
                self.assertIn('Example issue',page.locator('#skout').inner_text())
                self.assertEqual(page.locator('#flow-steps li[data-status=done]').count(),4)
                page.locator('#skout button[data-copy]').first.click()
                self.assertEqual(page.evaluate('navigator.clipboard.readText()'),'team plans')
                page.locator('#skout details summary').click()
                self.assertIn('company_does',page.locator('#skout details').inner_text())
                report=ROOT/'reports';report.mkdir(exist_ok=True)
                page.screenshot(path=str(report/'flow-ui.png'),full_page=True)
                page.locator('.modal').evaluate('(el)=>el.scrollTop=0')
                page.screenshot(path=str(report/'flow-ui-top.png'),full_page=True)
                # Re-run with numeric text: stop after angle, never draft/check.
                first_run_calls=list(calls)
                calls.clear()
                outputs[1]={'fit_score':'2','reason':'Weak signal'}
                page.locator('#run').click()
                page.wait_for_function("document.querySelector('#skout').textContent.includes('Weak fit. Find a stronger signal before writing.')")
                self.assertEqual(len(calls),2)
                self.assertEqual(page.locator('#flow-steps li[data-status=done]').count(),2)
                self.assertEqual(page.locator('#flow-steps li[data-status=skipped]').count(),2)
                page.screenshot(path=str(report/'fit-score-string-stop.png'),full_page=True)
                calls[:]=first_run_calls
                page.keyboard.press('Escape')
                page.locator('.skill-card').filter(has_text='motion-trimmer').click()
                page.locator('#fld-topic').fill('Legacy topic')
                page.locator('#preview').click()
                self.assertIn('Legacy topic',page.locator('#skout').inner_text())
                page.locator('#run').click()
                page.wait_for_function("document.querySelector('#skout').textContent.includes('shot list')")
                self.assertEqual(len(calls),5)
                self.assertNotIn('response_format',calls[-1])
                self.assertEqual(errors,[])
                print('Chromium UI: flow preview, four chained steps, copy, escaping, raw outputs, legacy preview/run PASS; external requests blocked:',len(blocked))
                browser.close()
        finally:
            server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
