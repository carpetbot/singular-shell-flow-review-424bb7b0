"""Gateway detail metadata is one authenticated status read, not a list walk."""
import unittest
import test_a3_detail_browser as fixtures
class GatewayDetail(fixtures.Detail):
 setUp=fixtures.Detail.setUp
 tearDown=fixtures.Detail.tearDown
 route=fixtures.Detail.route
 mount=fixtures.Detail.mount
 def test_single_status_metadata_known_cost_and_no_unrelated_refetch(self):
  requests=[]
  self.page.route('**/v1/videos?*',lambda r:(requests.append('list'),r.fulfill(json={'items':[],'next_cursor':None})))
  def status(r):
   requests.append(r.request.headers.get('authorization'))
   r.fulfill(json={'id':'gateway_metadata','status':'completed','model':'fixture/gateway-model','params':{'prompt':'OFFLINE FIXTURE recorded gateway prompt'},'created_at':'2026-10-28T01:00:00Z','cost_usd':1.25})
  self.page.route('**/v1/videos/gateway_metadata',status)
  self.page.route('**/v1/videos/gateway_metadata/content',lambda r:r.fulfill(body=(fixtures.ROOT/'tests/fixtures/offline-video.mp4').read_bytes(),content_type='video/mp4'))
  self.mount(identity='gateway:gateway_metadata');self.page.wait_for_selector('#work-player')
  self.assertIn('OFFLINE FIXTURE recorded gateway prompt',self.page.locator('.detail-meta').inner_text());self.assertIn('$1.25',self.page.locator('.detail-meta').inner_text())
  for _ in range(3):self.page.evaluate("async()=>{const c=await(await import('/js/video-runtime.js')).videoContext();window.dispatchEvent(new CustomEvent('singular:runs',{detail:{account_id:c.store.account_id}}));}")
  self.page.wait_for_timeout(250)
  self.assertEqual(requests,['Bearer offline-not-real-key']);self.assertEqual(self.errors,[])
 def test_status_identity_mismatch_and_unknown_cost_fail_honestly(self):
  self.page.route('**/v1/videos/wrong_identity',lambda r:r.fulfill(json={'id':'another_job','status':'completed','cost_usd':0,'params':{'prompt':'Must not leak mismatched job'}}))
  self.mount(identity='gateway:wrong_identity');self.page.wait_for_function("document.querySelector('#detail-status').textContent.includes('Could not load')")
  self.assertNotIn('Must not leak',self.page.locator('#detail-body').inner_text())
  self.page.route('**/v1/videos/unknown_money',lambda r:r.fulfill(json={'id':'unknown_money','status':'queued','cost_usd':'0','params':{}}))
  self.mount(identity='gateway:unknown_money');self.page.wait_for_selector('.detail-meta');self.assertIn('Not recorded',self.page.locator('.detail-meta').inner_text());self.assertNotIn('$0',self.page.locator('.detail-meta').inner_text())
def load_tests(loader,tests,pattern):return unittest.TestSuite(GatewayDetail(name) for name in GatewayDetail.__dict__ if name.startswith('test_'))
if __name__=='__main__':unittest.main()
