"""Real loopback mock-upstream media checks; never calls the public gateway."""
import http.client, http.server, importlib.util, io, json, os, threading, unittest
from unittest.mock import patch
from urllib.error import HTTPError
from email.message import Message
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=Path(os.environ.get('VIDEO_APP_ROOT',str(ROOT)))
class VideoProxy(unittest.TestCase):
 def setUp(self):
  spec=importlib.util.spec_from_file_location('media_proxy',APP/'proxy.py');self.p=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.p)
  self.received=[];self.release=threading.Event();outer=self
  class Upstream(http.server.BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def do_POST(self):self.do_GET()
   def do_GET(self):
    n=int(self.headers.get('Content-Length') or 0);body=self.rfile.read(n);outer.received.append({'path':self.path,'method':self.command,'token':self.headers.get('Idempotency-Key'),'auth':self.headers.get('Authorization'),'body':body.decode()})
    if self.path.endswith('/content'):
     if 'redirect' in self.path:self.send_response(302);self.send_header('Location','http://127.0.0.1:1/steal');self.end_headers();return
     self.send_response(200);self.send_header('Content-Type','video/mp4')
     if 'huge' in self.path:self.send_header('Content-Length','104857601');self.end_headers();return
     if 'unknown' not in self.path:self.send_header('Content-Length','131072')
     self.end_headers();self.wfile.write(b'a'*65536);self.wfile.flush();outer.release.wait(3)
     try:
      if 'overflow' in self.path:
       for _ in range(1600):self.wfile.write(b'b'*65536)
      elif 'short' not in self.path:self.wfile.write(b'b'*65536)
     except (BrokenPipeError,ConnectionResetError):pass
    else:
     data=json.dumps({'id':'vid_loopback','status':'queued'}).encode();self.send_response(202 if self.command=='POST' else 200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  self.up=http.server.ThreadingHTTPServer(('127.0.0.1',0),Upstream);threading.Thread(target=self.up.serve_forever,daemon=True).start();self.p.GATEWAY='http://127.0.0.1:'+str(self.up.server_port)
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),self.p.Handler);threading.Thread(target=self.server.serve_forever,daemon=True).start()
 def tearDown(self):
  self.release.set();self.server.shutdown();self.server.server_close();self.up.shutdown();self.up.server_close()
 def req(self,path,method='GET',body=None):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=1);c.request(method,path,body=body,headers={'Authorization':'Bearer offline-loopback','Idempotency-Key':'fixture-idempotency','Content-Type':'application/json'});r=c.getresponse();status=r.status;data=r.read();c.close();return status,data
 def test_video_errors_are_bounded_sanitized_and_closed(self):
  for path,code in [('/v1/videos',500),('/v1/videos/vid_error',401),('/v1/videos/vid_error/content',502)]:
   class ErrorBody(io.BytesIO):
    sizes=[]
    def read(self,size=-1):
     self.sizes.append(size)
     return super().read(size)
   body=ErrorBody(b'private-upstream-detail'*10000);headers=Message();headers['X-Private']='must-not-forward'
   err=HTTPError('http://offline.invalid',code,'private reason',headers,body)
   with patch.object(self.p.urllib.request.OpenerDirector,'open',side_effect=err):
    status,data=self.req(path,'POST' if path=='/v1/videos' else 'GET','{}' if path=='/v1/videos' else None)
   self.assertEqual(status,code)
   self.assertTrue(all(0<=n<=4096 for n in body.sizes),body.sizes)
   self.assertLess(len(data),512);self.assertNotIn(b'private',data);self.assertTrue(body.closed)
   self.assertEqual(json.loads(data)['error_message'],'Video gateway request failed')

 def test_01_token_only_create_and_legacy_body(self):
  self.assertEqual(self.req('/v1/videos','POST','{"model":"fixture"}')[0],202)
  self.assertEqual(self.received[-1]['token'],'fixture-idempotency');self.assertEqual(self.received[-1]['body'],'{"model":"fixture"}')
  for path,method in [('/v1/videos/vid_a','GET'),('/v1/chat/completions','POST')]:
   self.req(path,method,'{}' if method=='POST' else None);self.assertIsNone(self.received[-1]['token'])
 def test_02_streams_before_upstream_finishes(self):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=1);c.request('GET','/v1/videos/vid_stream/content');r=c.getresponse();self.assertEqual(r.status,200);self.assertEqual(r.read(100),b'a'*100);self.assertFalse(self.release.is_set());self.release.set();self.assertEqual(len(r.read()),131072-100);c.close()
 def test_03_bound_and_redirect(self):
  self.assertEqual(self.req('/v1/videos/vid_huge/content')[0],413)
  self.assertEqual(self.req('/v1/videos/vid_redirect/content')[0],502)
 def test_04_invalid_video_paths_do_not_forward(self):
  for path in ['/v1/videos/../content','/v1/videos/a/content?url=https://evil.test','/v1/videos/a%2Fcontent','/v1/videos/a/content/extra','/v1/videos/a\\content']:
   self.assertEqual(self.req(path)[0],404,path)
  self.assertEqual(self.received,[])

 def test_05_unknown_size_stream_is_bounded(self):
  self.p.MAX_VIDEO_BYTES=70000;self.release.set()
  with self.assertRaises(http.client.IncompleteRead) as failed:self.req('/v1/videos/vid_unknown/content')
  self.assertGreater(len(failed.exception.partial),0);self.assertLessEqual(len(failed.exception.partial),70000)

 def test_unknown_length_success_and_exact_bound_complete_normally(self):
  self.release.set();self.p.MAX_VIDEO_BYTES=131072
  status,data=self.req('/v1/videos/vid_unknown/content')
  self.assertEqual(status,200);self.assertEqual(data,b'a'*65536+b'b'*65536)

 def test_unknown_overflow_browser_fetch_and_download_reject_without_blob(self):
  from playwright.sync_api import sync_playwright
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   try:
    page=browser.new_page()
    page.route('**/*',lambda route:route.continue_() if route.request.url.startswith('http://127.0.0.1:') else route.abort())
    page.goto('http://127.0.0.1:'+str(self.server.server_port))
    page.evaluate('''()=>{window.transfer=(async()=>{let size=0;try{const r=await fetch('/v1/videos/vid_unknown_overflow/content');const reader=r.body.getReader();while(true){const {done,value}=await reader.read();if(done)return {ok:true,size};size+=value.length;window.firstByte=true;}}catch{return {ok:false,size};}})();}''')
    page.wait_for_function('window.firstByte===true',timeout=2000)
    self.assertFalse(self.release.is_set(),'must stream before upstream completes');self.release.set()
    result=page.evaluate('window.transfer');self.assertFalse(result['ok'],'overflow must not be a successful truncated download');self.assertLessEqual(result['size'],100*1024*1024)
    for job in ['vid_unknown_overflow','vid_short']:
     outcome=page.evaluate('''async id=>{const {VideoSession}=await import('/js/video.js');let blobs=0;const s=new VideoSession({key:'offline',storage:localStorage,urlAPI:{createObjectURL(){blobs++;return 'blob:invalid';}}});s.record={id,status:'completed'};s.sameKey=async()=>{};try{await s.download();return {ok:true,blobs};}catch(e){return {ok:false,blobs,message:e.message};}}''',job)
     self.assertEqual(outcome,{'ok':False,'blobs':0,'message':'Download incomplete, retry download'})
   finally:browser.close()
