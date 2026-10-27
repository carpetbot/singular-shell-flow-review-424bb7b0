import http.client
import http.server
import importlib.util
import os
from pathlib import Path
import tempfile
import threading
import unittest

SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('shell_proxy', SOURCE / 'proxy.py')
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

class StaticSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR', SOURCE))
        root = Path(cls.tmp.name)
        (root/'index.html').write_text('<h1>shell</h1>')
        (root/'proxy.py').write_text('private-source-marker')
        (root/'js').mkdir()
        (root/'js/app.js').write_text('export {};')
        (root/'js/leak.js').symlink_to(root/'proxy.py')
        (root/'tests').mkdir()
        (root/'tests/leak.js').write_text('private-test-marker')
        cls.old_root = proxy.ROOT
        proxy.ROOT = str(root)
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), proxy.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
        proxy.ROOT = cls.old_root
        cls.tmp.cleanup()
    def request(self, method, path):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        c.request(method, path)
        r = c.getresponse(); status = r.status; body = r.read(); c.close()
        return status, body
    def test_blocks_python_encoded_queries_symlinks_directories_tests(self):
        for method in ('GET', 'HEAD'):
            for path in ('/proxy.py','/proxy.py?download=1','/%70roxy%2epy?x=1','/%2570roxy%252epy','/js/leak.js','/js/','/tests/leak.js','/../proxy.py','/js/%2e%2e/proxy.py'):
                with self.subTest(method=method,path=path):
                    status, body = self.request(method,path)
                    self.assertIn(status, (403,404))
                    self.assertNotIn(b'private-source-marker',body)
    def test_static_shell_still_serves(self):
        for method in ('GET','HEAD'):
            for path in ('/','/index.html?x=1','/js/app.js'):
                with self.subTest(method=method,path=path):
                    self.assertEqual(self.request(method,path)[0],200)

if __name__ == '__main__': unittest.main()
