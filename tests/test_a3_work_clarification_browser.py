"""Part A My work clarification — offline fixtures only."""
import unittest
from test_a3_clarifications_browser import Clarifications
class WorkClarification(unittest.TestCase):
 setUp=Clarifications.setUp
 tearDown=Clarifications.tearDown
 route=Clarifications.route
 mount=Clarifications.mount
 def test_empty_work_connect_refresh_and_first_visit_copy(self):
  self.mount('work','');self.assertEqual(self.page.locator('#view h1').inner_text(),'Your work')
  self.assertTrue(self.page.locator('#inline-key').is_visible());self.assertFalse(self.page.locator('#work-refresh').is_visible())
  self.assertIn('Videos you make here',self.page.locator('#view').inner_text())
  for word in ['Recover videos','recovery unavailable','Checking connected key']:
   self.assertNotIn(word,self.page.locator('#view').inner_text())
  self.page.locator('#inline-key').fill('offline-work-connect');self.page.locator('#inline-connect').click()
  self.page.wait_for_selector('#work-refresh');self.assertEqual(len([c for c in self.calls if c['path']=='/v1/videos']),0)

del Clarifications
