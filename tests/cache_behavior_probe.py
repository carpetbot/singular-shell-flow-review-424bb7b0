"""Supplemental real-browser cache behavior probe; no cache-module import required.
Run against an alternate runtime with VIDEO_APP_ROOT; all calls are offline fixtures.
"""
import unittest
import test_work_browser as fixture
class CacheBehavior(unittest.TestCase):
 setUp=fixture.WorkBrowser.setUp
 tearDown=fixture.WorkBrowser.tearDown
 route=fixture.WorkBrowser.route
 open=fixture.WorkBrowser.open
 def test_reopen_completed_media_reuses_bytes_without_another_authenticated_fetch(self):
  self.open();self.page.get_by_role('button',name='Open video vid_first',exact=True).wait_for()
  self.page.get_by_role('button',name='Open video vid_first',exact=True).click();self.page.wait_for_function("document.querySelector('#work-player')?.readyState>=2")
  self.assertEqual(len([c for c in self.calls if '/content' in c[0]]),1)
  self.page.get_by_role('button',name='Open video vid_first',exact=True).click();self.page.wait_for_function("document.querySelector('#work-player')?.readyState>=2")
  self.assertEqual(len([c for c in self.calls if '/content' in c[0]]),1,'Reopening the completed video must reuse optional cached bytes')
  self.assertEqual(self.errors,[])
if __name__=='__main__':unittest.main(verbosity=2)
