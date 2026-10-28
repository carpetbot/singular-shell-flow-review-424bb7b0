"""Repeated focused poster probe with callback/decode diagnostics."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tests'))
from test_work_cards_browser import WorkCards
for i in range(10):
 case=WorkCards('test_poster_only_after_open_persists_and_is_account_scoped');case.setUp()
 case.page.add_init_script("""(()=>{
 window.posterTrace=[];
 const frame=HTMLVideoElement.prototype.requestVideoFrameCallback;
 HTMLVideoElement.prototype.requestVideoFrameCallback=function(cb){window.posterTrace.push({event:'registered'});return frame.call(this,(now,meta)=>{
 window.posterTrace.push({event:'callback',state:this.readyState,w:this.videoWidth,h:this.videoHeight,rect:this.getBoundingClientRect().toJSON()});cb(now,meta);});};
 const data=HTMLCanvasElement.prototype.toDataURL;
 HTMLCanvasElement.prototype.toDataURL=function(...args){window.posterTrace.push({event:'encoded',pixel:[...this.getContext('2d').getImageData(10,10,1,1).data]});return data.apply(this,args);};
 })();""")
 try:
  case.test_poster_only_after_open_persists_and_is_account_scoped();print(i,'PASS',flush=True)
 except Exception:
  print(i,'FAIL',json.dumps(case.page.evaluate("({trace:window.posterTrace,video:document.querySelector('#work-player')&&{state:document.querySelector('#work-player').readyState,rect:document.querySelector('#work-player').getBoundingClientRect().toJSON()},status:document.querySelector('#work-status')?.textContent})")),flush=True)
  case.page.screenshot(path=str(ROOT/'reports/a2/c3-poster-failure.png'),full_page=True)
  raise
 finally:case.tearDown()
