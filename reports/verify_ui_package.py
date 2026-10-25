"""Read-back verification of deploy ZIP bytes and packaged loopback HTTP serving."""
from pathlib import Path
import hashlib
import http.client
import http.server
import importlib.util
import json
import threading
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'dist/singular-shell-ui'
ARCHIVE=ROOT/'dist/singular-shell-ui.zip'
files={name:ROOT/name for name in ('index.html','styles.css','proxy.py')}
files.update({str(p.relative_to(ROOT)):p for folder in ('js','skills') for p in (ROOT/folder).rglob('*') if p.is_file()})
files['README.md']=ROOT/'UI_README.md'
expected=set(files)
actual={str(p.relative_to(DEST)) for p in DEST.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert expected==actual,(expected-actual,actual-expected)
with zipfile.ZipFile(ARCHIVE) as archive:
    assert archive.testzip() is None
    assert set(archive.namelist())=={'singular-shell-ui/'+name for name in expected}
    for name,source in files.items():
        assert (DEST/name).read_bytes()==source.read_bytes(),name
        assert archive.read('singular-shell-ui/'+name)==source.read_bytes(),name
    assert not any(name.startswith(('tests/','reports/','dist/')) or name.endswith(('.env','.pyc')) for name in expected)
    assert {name for name in expected if name.endswith('.py')}=={'proxy.py'}
print('ZIP CRC passed; source/extracted/ZIP byte equivalence:',len(expected),'files; no tests, fixtures, logs, credentials or review screens in runtime.')
spec=importlib.util.spec_from_file_location('ui_packaged_proxy',DEST/'proxy.py')
proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
def status(method,path):
    connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
    connection.request(method,path);response=connection.getresponse();result=response.status;response.read();connection.close();return result
try:
    public=sorted(expected-{'proxy.py','README.md'})
    for path in public:
        for method in ('GET','HEAD'):assert status(method,'/'+path)==200,(method,path)
    assert status('GET','/')==200
    denied=['proxy.py','%70roxy%2epy?download=1','js/','skills/','README.md','UI_TEST_REPORT.md','tests/test_lite_pro.py','reports/review/01-lite-gallery.png','dist/singular-shell-ui.zip','../proxy.py','%2e%2e/proxy.py']
    for method in ('GET','HEAD'):
        for path in denied:assert status(method,'/'+path)==404,(method,path)
    print('Packaged proxy: GET/HEAD public files:',len(public),'; GET/HEAD denied paths:',len(denied),'; root 200. No gateway requests.')
finally:server.shutdown();server.server_close();thread.join()
receipt=json.loads((ROOT/'reports/ui-package.json').read_text())
assert receipt['sha256']==hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
print('Archive bytes:',ARCHIVE.stat().st_size)
print('SHA256:',receipt['sha256'])
