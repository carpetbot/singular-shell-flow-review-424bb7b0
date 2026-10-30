"""Deterministic runtime-only A3 ZIP; all-byte/frozen/static denial verification.
No network forwarding, credential lookup, deployment or modifications to A2 ZIP.
"""
import hashlib,http.client,importlib.util,json,shutil,subprocess,threading,zipfile,re
from pathlib import Path
from offline_browser import offline_server
ROOT=Path(__file__).resolve().parents[1]
BASE='d95c15323d435f19d2ff634d92484c4b9503b3f5'
files=[ROOT/'index.html',ROOT/'styles.css',ROOT/'proxy.py',*sorted((ROOT/'js').rglob('*.js'))]
files+=sorted(p for p in (ROOT/'skills').rglob('*') if p.is_file() and (p.name in ('singular.flow.json','singular.skill.json') or ('prompts' in p.parts and p.suffix=='.md')))
names={p.relative_to(ROOT).as_posix() for p in files};assert len(names)==len(files)
required={'js/views/create.js','js/views/video-flow.js','js/views/work-detail.js','js/key-connect.js','js/media-cache.js','js/video-runtime.js','js/run-store.js','js/poster-cache.js','js/work-api.js','js/views/work.js'}
assert required<=names
assert all(not p.is_symlink() for p in files)
frozen=[p for p in files if 'skills' in p.relative_to(ROOT).parts or p==ROOT/'js/video.js']
for p in frozen:assert p.read_bytes()==subprocess.check_output(['git','show',BASE+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT),p
assert hashlib.sha256((ROOT/'js/video.js').read_bytes()).hexdigest()=='71986db49b64763229a90e4d4fe10ae78ebfc45b27070f6d32e675e21a31450b'
markers={};secret_hits=[]
for p in files:
 rel=p.relative_to(ROOT).as_posix();data=p.read_bytes()
 if re.search(rb'\b(?:m[r]_|s[k]-)[A-Za-z0-9_-]{12,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY',data):secret_hits.append(rel)
 lines=re.findall(rb'[^\n]*(?:mr_|sk-)[^\n]*',data)
 if lines:
  baseline=subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT)
  assert lines==re.findall(rb'[^\n]*(?:mr_|sk-)[^\n]*',baseline),rel
  markers[rel]=len(lines)
assert not secret_hits,secret_hits
assert set(markers)=={'js/views/chat.js','js/views/settings.js','js/views/skills.js'}
archive=ROOT/'dist/shell-ux-v1-a3.zip';archive.parent.mkdir(exist_ok=True)
evidence=ROOT/'reports/a3/package-a3';evidence.mkdir(parents=True,exist_ok=True)
def build(path):
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in files:
   info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2026,10,28,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes(),compresslevel=9)
build(archive);rebuilt=evidence/'deterministic-rebuild.zip';build(rebuilt);assert archive.read_bytes()==rebuilt.read_bytes();rebuilt.unlink()
digest=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
initial=evidence/'initial-extract';relocated=evidence/'relocated/runtime'
for p in [initial,relocated]:
 if p.exists():shutil.rmtree(p)
initial.mkdir();relocated.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None and len(z.namelist())==len(files) and set(z.namelist())==names
 assert not any(n.startswith(('tests/','reports/','.git/')) or any(part.startswith('.') for part in Path(n).parts) or (n.endswith('.py') and n!='proxy.py') for n in z.namelist())
 for p in files:assert z.read(p.relative_to(ROOT).as_posix())==p.read_bytes(),p
 z.extractall(initial)
shutil.move(str(initial),relocated)
for p in files:assert (relocated/p.relative_to(ROOT)).read_bytes()==p.read_bytes(),p
spec=importlib.util.spec_from_file_location('packaged_a3_proxy',relocated/'proxy.py');assert spec and spec.loader
proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
assert proxy.STATIC_ASSETS==names-{'proxy.py'},(proxy.STATIC_ASSETS^(names-{'proxy.py'}))
# These explicit fake files prove that denial is policy, not merely nonexistence.
injected={'tests/private.js':'// OFFLINE FIXTURE private test','reports/private.js':'// OFFLINE FIXTURE private report','js/unapproved.js':'// OFFLINE FIXTURE unapproved source','.env':'OFFLINE_FIXTURE_ONLY=1'}
for name,data in injected.items():(relocated/name).parent.mkdir(parents=True,exist_ok=True);(relocated/name).write_text(data)
server=offline_server(proxy.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();checks=[]
public=['/','/index.html','/styles.css',*['/'+n for n in sorted(names) if n.startswith(('js/','skills/'))]]
private=['/proxy.py','/%70roxy.py?x=1','/%2570roxy%252epy','/js/','/tests/private.js','/reports/private.js','/js/unapproved.js','/js/%75napproved.js?download=1','/.env','/../proxy.py']
try:
 for method in ['GET','HEAD']:
  for path in public+private:
   c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3);c.request(method,path);r=c.getresponse();r.read();status=r.status;c.close();expected=200 if path in public else 404
   assert status==expected,(method,path,status);checks.append({'method':method,'path':path,'status':status})
finally:server.shutdown();server.server_close();thread.join()
assert server.unexpected_upstream==[]
for name in injected:(relocated/name).unlink()
for name in ['tests','reports']:(relocated/name).rmdir()
# Import creates only Python bytecode; remove it from the relocated production tree.
if (relocated/'__pycache__').exists():shutil.rmtree(relocated/'__pycache__')
assert {p.relative_to(relocated).as_posix() for p in relocated.rglob('*') if p.is_file()}==names
manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
result={'archive':str(archive),'sha256':digest,'runtime_files':len(files),'frozen_files':len(frozen),'base':BASE,'all_zip_and_relocated_bytes_equal_source':True,'deterministic_rebuild_equal':True,'static_GET_HEAD_checks':len(checks),'checks':checks,'relocated_runtime':str(relocated),'unexpected_upstream':server.unexpected_upstream,'credential_pattern_hits':secret_hits,'unchanged_baseline_literal_prefix_lines':markers,'manifest':manifest}
(evidence/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['manifest','checks']},indent=2))
