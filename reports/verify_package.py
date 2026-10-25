"""Verify the packaged artifact using only source reads and loopback HTTP."""
from pathlib import Path
import hashlib
import http.client
import http.server
import importlib.util
import threading
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'dist/singular-shell'
ARCHIVE=ROOT/'dist/singular-shell-flow.zip'
expected=[ROOT/name for name in ('index.html','styles.css','proxy.py','README.md','DEPLOYMENT.md','TEST_REPORT.md')]
expected += sorted(p for folder in ('js','skills') for p in (ROOT/folder).rglob('*') if p.is_file())
expected_names={str(p.relative_to(ROOT)) for p in expected}
actual_names={str(p.relative_to(DEST)) for p in DEST.rglob('*') if p.is_file()}
assert actual_names==expected_names,(actual_names-expected_names,expected_names-actual_names)
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    names={name.removeprefix('singular-shell/') for name in z.namelist() if not name.endswith('/')}
    assert names==expected_names
    for p in expected:
        relative=str(p.relative_to(ROOT))
        source=p.read_bytes()
        assert (DEST/relative).read_bytes()==source
        assert z.read('singular-shell/'+relative)==source
    assert not any('tests/' in name or '__pycache__' in name or name.endswith('.env') for name in names)
    assert {name for name in names if name.endswith('.py')}=={'proxy.py'}
print('Source/deployment/ZIP bytes identical for',len(expected),'files; ZIP CRC valid; tests/caches/credentials files excluded.')

spec=importlib.util.spec_from_file_location('packaged_proxy',DEST/'proxy.py')
proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
def status(method,path):
    c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
    c.request(method,path);r=c.getresponse();code=r.status;r.read();c.close();return code
try:
    public=[p for p in expected_names if p not in {'proxy.py','README.md','DEPLOYMENT.md','TEST_REPORT.md'}]
    for path in public:
        assert status('GET','/'+path)==200,path
        assert status('HEAD','/'+path)==200,path
    assert status('GET','/')==200
    for method in ('GET','HEAD'):
        for path in ('proxy.py','%70roxy%2epy?download=1','js/','README.md','TEST_REPORT.md','tests/flow.test.mjs','dist/singular-shell-flow.zip'):
            assert status(method,'/'+path)==404,(method,path)
    print('Packaged proxy: GET/HEAD served',len(public),'public files; source/docs/test/archive/directory denial passed. No gateway requests.')
finally:
    server.shutdown();server.server_close();thread.join()
print('Archive bytes:',ARCHIVE.stat().st_size)
print('SHA256:',hashlib.sha256(ARCHIVE.read_bytes()).hexdigest())
