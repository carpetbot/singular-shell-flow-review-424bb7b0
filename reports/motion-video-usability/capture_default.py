"""Supplementary offline Chromium default-mode wire/screenshot evidence."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from test_video_browser import VideoBrowser
out=ROOT/'reports/motion-video-usability/default-mode';out.mkdir(exist_ok=True)
t=VideoBrowser('test_01_gallery_five_second_default_mode');t.setUp()
try:
 t.page.set_viewport_size({'width':1280,'height':1100});t.open();t.plan()
 t.page.locator('#video-quote').click();t.page.wait_for_function("!document.querySelector('#video-generate').disabled")
 t.page.locator('#video-shot-list').screenshot(path=str(out/'lite-shot-list.png'))
 t.page.locator('#video-price').scroll_into_view_if_needed();t.page.screenshot(path=str(out/'wan-five-seconds.png'))
 quote=t.page.locator('#video-price').inner_text();assert '$0.53' in quote
 t.page.locator('#video-generate').click();t.page.wait_for_selector('#video-player[src^="blob:"]')
 posts=[c for c in t.calls if c['path']=='/v1/videos'];assert len(posts)==1;assert set(posts[0]['body'])=={'model','prompt','resolution'}
 t.page.locator('#video-new').click();t.page.locator('#video-model').select_option('minimax/h3-max-turbo');t.page.locator('#video-quote').click();t.page.wait_for_function("document.querySelector('#video-price').textContent.includes('$0.21')")
 t.page.locator('#video-price').scroll_into_view_if_needed();t.page.screenshot(path=str(out/'minimax-five-seconds.png'))
 (out/'default-wire.offline.json').write_text(json.dumps({'fixture':'OFFLINE FAKE INFERENCE, synthetic MP4; not a paid model render','wan_quote':quote,'minimax_quote':t.page.locator('#video-price').inner_text(),'requests':[{k:(bool(v) if k=='auth' else v) for k,v in c.items()} for c in t.calls],'plan':json.loads(t.page.locator('#video-plan-json').input_value()),'errors':t.errors},indent=2)+'\n')
 assert not t.errors;print('PASS: five-second default-only body, Wan $0.53 / MiniMax $0.21; no external inference')
finally:t.tearDown()
