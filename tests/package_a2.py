"""Deterministic runtime-only A2 ZIP, frozen-byte and extracted-server checks.
Run: python3 tests/package_a2.py
Then: python3 tests/verify_a2.py --runtime reports/a2/c3-package-check --label c3-packaged
No upstream, key lookup, paid requests, push or deploy.
"""
import hashlib,http.client,importlib.util,json,shutil,subprocess,threading,zipfile
from pathlib import Path
from offline_browser import offline_server
ROOT=Path(__file__).resolve().parents[1]
BASE='d95c15323d435f19d2ff634d92484c4b9503b3f5'
files=[ROOT/'index.html',ROOT/'styles.css',ROOT/'proxy.py']
files+=sorted((ROOT/'js').rglob('*.js'))
files+=sorted(p for p in (ROOT/'skills').rglob('*') if p.is_file() and (p.name in ('singular.flow.json','singular.skill.json') or ('prompts' in p.parts and p.suffix=='.md')))
assert all(not p.is_symlink() for p in files)
names={p.relative_to(ROOT).as_posix() for p in files}
assert {'js/run-store.js','js/video-runtime.js','js/poster-cache.js','js/views/work.js'}<=names
frozen=[p for p in files if 'skills' in p.relative_to(ROOT).parts or p==ROOT/'js/video.js']
for p in frozen:assert p.read_bytes()==subprocess.check_output(['git','show',BASE+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT),p
archive=ROOT/'dist/shell-ux-v1-a2.zip';archive.parent.mkdir(exist_ok=True)
def build(path):
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for p in files:
   info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2026,10,28,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
build(archive)
evidence=ROOT/'reports/a2';evidence.mkdir(exist_ok=True)
rebuilt=evidence/'c3-rebuild.zip';build(rebuilt);assert archive.read_bytes()==rebuilt.read_bytes();rebuilt.unlink()
digest=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
check=evidence/'c3-package-check'
if check.exists():shutil.rmtree(check)
check.mkdir()
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None and len(z.namelist())==len(files) and set(z.namelist())==names
 assert not any(n.startswith(('tests/','reports/','.git/')) for n in z.namelist())
 for p in files:assert z.read(p.relative_to(ROOT).as_posix())==p.read_bytes(),p
 z.extractall(check)
spec=importlib.util.spec_from_file_location('packaged_a2_proxy',check/'proxy.py')
assert spec and spec.loader
proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
server=offline_server(proxy.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
checks=0
try:
 # Every runtime JS import (including IDB + watcher + posters) is publicly served.
 public=['/','/styles.css',*['/'+n for n in sorted(names) if n.startswith(('js/','skills/'))]]
 private=['/proxy.py','/%70roxy.py?x=1','/js/','/tests/test_work_browser.py','/reports/a2/c3-source-python.log']
 for method in ['GET','HEAD']:
  for path in public+private:
   c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3);c.request(method,path);r=c.getresponse();r.read();status=r.status;c.close();checks+=1
   assert status==(200 if path in public else 404),(method,path,status)
finally:server.shutdown();server.server_close();thread.join()
assert server.unexpected_upstream==[]
markers=[p.relative_to(ROOT).as_posix() for p in files if b'mr_' in p.read_bytes() or b'sk-' in p.read_bytes()]
assert set(markers)=={'js/views/chat.js','js/views/settings.js','js/views/skills.js'}
for name in markers:assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
result={'archive':str(archive),'sha256':digest,'runtime_files':len(files),'frozen_files':len(frozen),'baseline':BASE,'all_zip_bytes_equal_source':True,'deterministic_rebuild_equal':True,'static_GET_HEAD_checks':checks,'extracted_root':str(check),'unexpected_upstream':server.unexpected_upstream,'baseline_literal_prefix_files':markers,'baseline_marker_note':'Only unchanged baseline prefix labels/placeholders, not credentials. Do not claim zero marker hits.','manifest':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(evidence/'c3-package-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='manifest'},indent=2))
