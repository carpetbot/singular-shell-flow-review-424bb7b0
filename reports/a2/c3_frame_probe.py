"""Compare loadeddata and first compositor frame; no runtime changes."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tests'))
from test_work_cards_browser import WorkCards
case=WorkCards('test_poster_only_after_open_persists_and_is_account_scoped');case.setUp()
try:
 case.open();case.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
 case.page.evaluate("""()=>{window.frameProbe=[];const create=document.createElement.bind(document);document.createElement=(tag,...args)=>{const e=create(tag,...args);if(tag==='video'){
 const sample=name=>{const c=create('canvas');c.width=320;c.height=180;const x=c.getContext('2d');x.drawImage(e,0,0);window.frameProbe.push({name,state:e.readyState,time:e.currentTime,pixel:[...x.getImageData(10,10,1,1).data]});};
 e.addEventListener('loadeddata',()=>sample('loadeddata'),{once:true});e.requestVideoFrameCallback(()=>sample('compositor'));
 }return e;};}""")
 case.page.get_by_role('button',name='Open video vid_first').click()
 case.page.wait_for_function('window.frameProbe.length===2')
 print(json.dumps(case.page.evaluate('window.frameProbe'),indent=2))
finally:case.tearDown()
