"""A1 list query allowlist, tested against a real loopback upstream."""
import unittest
import test_video_proxy as media_tests

class WorkProxy(unittest.TestCase):
 setUp = media_tests.VideoProxy.setUp
 tearDown = media_tests.VideoProxy.tearDown
 req = media_tests.VideoProxy.req
 def test_list_query_allowlist(self):
  for path in ['/v1/videos','/v1/videos?limit=1','/v1/videos?limit=100&cursor=abc_=-','/v1/videos?cursor=abc&limit=50']:
   self.assertEqual(self.req(path)[0],200,path)
   self.assertEqual(self.received[-1]['path'],path)
   self.assertEqual(self.received[-1]['auth'],'Bearer offline-loopback')
   self.assertIsNone(self.received[-1]['token'])
 def test_list_query_rejections_never_forward(self):
  for query in ['limit=0','limit=101','limit=-1','limit=1.0','limit=+1','limit=','limit=1&limit=2','cursor=','cursor=a&cursor=b','cursor='+('a'*201),'cursor=a%2Fb','foo=1','limit=50&foo=1','limit=1&&cursor=a']:
   self.assertEqual(self.req('/v1/videos?'+query)[0],404,query)
  for path in ['/v1/videos?x=1','/v1/videos?limit=1','/v1/videos?']:
   self.assertEqual(self.req(path,'POST','{}')[0],404,path)
  self.assertEqual(self.received,[])
