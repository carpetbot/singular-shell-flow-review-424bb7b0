"""A2 integration: real Chromium/IndexedDB, loopback fixtures only."""
from test_video_browser import VideoBrowser
import unittest

class DurableVideoBrowser(VideoBrowser):
 # Reuse fixture setup, not the inherited legacy acceptance cases.
 def test_durable_saved_before_post_and_plan_before_chat(self):
  self.open();self.plan()
  rows=self.rows()
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]['status'],'done')
  self.assertEqual(rows[0]['inputs']['topic'],'An offline paper boat')
  self.assertTrue(rows[0]['receipts'])
  self.page.route('**/v1/videos',self.check_post)
  self.checked=False
  self.page.locator('#video-quote').click()
  self.page.wait_for_function("!document.querySelector('#video-generate').disabled")
  self.page.locator('#video-generate').click()
  self.page.wait_for_selector('#video-player[src^="blob:"]')
  self.assertTrue(self.checked)
  render=[r for r in self.rows() if r['idempotency_key']][0]
  self.assertEqual(render['status'],'done');self.assertEqual(render['video_job_id'],'vid_offline')
  self.assertEqual(render['prompt'],'A paper boat drifts on a calm pond.')
 def rows(self):
  return self.page.evaluate("async()=>{const a=await(await import('/js/run-store.js')).openRunStore({key:'offline-not-real-key'});try{return await a.list();}finally{a.close();}}")
 def check_post(self,r):
  rows=self.rows();row=[x for x in rows if x['idempotency_key']==r.request.headers.get('idempotency-key')][0]
  self.assertEqual(row['video_status'],'creating');self.assertEqual(row['status'],'rendering')
  self.assertEqual(row['prompt'],r.request.post_data_json['prompt']);self.checked=True
  r.fulfill(status=202,json={'id':'vid_offline','status':'queued'})

# Exclude inherited tests, whose modal-owned polling expectations are superseded.
for name in list(vars(VideoBrowser)):
 if name.startswith('test_') and name not in vars(DurableVideoBrowser):
  setattr(DurableVideoBrowser,name,None)
del VideoBrowser
if __name__=='__main__':unittest.main()
