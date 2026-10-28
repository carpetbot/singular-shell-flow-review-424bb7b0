"""Capture opened-media poster evidence without changing earlier screenshots."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from test_work_cards_browser import WorkCards
case=WorkCards('test_poster_only_after_open_persists_and_is_account_scoped')
case.setUp()
try:
 case.open();case.page.get_by_text('1 video jobs loaded.',exact=True).wait_for()
 assert case.page.locator('.work-poster').count()==0
 case.page.get_by_role('button',name='Open video vid_first').click();case.page.wait_for_selector('.work-poster')
 case.page.evaluate('scrollTo(0,0)');case.page.screenshot(path=str(ROOT/'reports/a2/c3-opened-poster-mobile.png'),full_page=True)
 assert case.page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert case.errors==[]
 print('Real offline Chromium: no initial poster; opened-player poster captured; mobile no overflow; no page errors.')
finally:case.tearDown()
