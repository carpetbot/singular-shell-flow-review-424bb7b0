"""Static module allowlist, using the real packaged-handler boundary offline."""
import http.client,importlib.util,tempfile,threading,unittest,os
from pathlib import Path
from offline_browser import offline_server
ROOT=Path(__file__).resolve().parents[1]
class StaticAllowlist(unittest.TestCase):
 def test_unknown_javascript_and_source_denied_get_and_head(self):
  spec=importlib.util.spec_from_file_location('a3_static_proxy',ROOT/'proxy.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR',str(ROOT/'reports/a3'))) as folder:
   path=Path(folder);(path/'js').mkdir();(path/'tests').mkdir();(path/'reports').mkdir();(path/'index.html').write_text('OFFLINE FIXTURE');(path/'js/app.js').write_text('// approved module');(path/'js/unapproved.js').write_text('// unapproved source');(path/'tests/leak.js').write_text('// private');(path/'proxy.py').write_text('# private');(path/'reports/source.js').write_text('// private')
   module.ROOT=folder;server=offline_server(module.Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
   try:
    for method in ['GET','HEAD']:
     for uri in ['/js/app.js','/js/unapproved.js','/js/%75napproved.js?x=1','/tests/leak.js','/proxy.py','/%70roxy.py?download=1','/reports/source.js','/js/']:
      c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3);c.request(method,uri);response=c.getresponse();response.read();status=response.status;c.close()
      self.assertEqual(status,200 if uri=='/js/app.js' else 404,(method,uri))
   finally:server.shutdown();server.server_close();t.join()
   self.assertEqual(server.unexpected_upstream,[])
if __name__=='__main__':unittest.main()
