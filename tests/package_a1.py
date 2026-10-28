"""Build/verify A1 runtime ZIP. Run from any cwd; no network or paid calls."""
import hashlib, http.client, http.server, importlib.util, json, shutil, subprocess, threading, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='d95c15323d435f19d2ff634d92484c4b9503b3f5'
files=[ROOT/'index.html',ROOT/'styles.css',ROOT/'proxy.py']
files+=sorted((ROOT/'js').rglob('*.js'))
files+=sorted(p for p in (ROOT/'skills').rglob('*') if p.is_file() and (p.name in ('singular.flow.json','singular.skill.json') or ('prompts' in p.parts and p.suffix=='.md')))
assert all(not p.is_symlink() for p in files)
frozen=[p for p in files if 'skills' in p.relative_to(ROOT).parts or p==ROOT/'js/video.js']
for p in frozen:
 assert p.read_bytes()==subprocess.check_output(['git','show',BASE+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT),p
archive=ROOT/'dist/shell-ux-v1-a1.zip';archive.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:
  info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2026,10,28,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
check=ROOT.parent/'a1-package-check'
if check.exists():shutil.rmtree(check)
check.mkdir()
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(files)
 assert set(z.namelist())=={p.relative_to(ROOT).as_posix() for p in files}
 for p in files:assert z.read(p.relative_to(ROOT).as_posix())==p.read_bytes(),p
 z.extractall(check)
spec=importlib.util.spec_from_file_location('packaged_a1_proxy',check/'proxy.py');proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
class Quiet(proxy.Handler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 for method in ['GET','HEAD']:
  for path in ['/','/js/work-api.js','/js/views/work.js','/proxy.py','/%70roxy.py?x=1','/js/','/tests/test_work_browser.py']:
   c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3);c.request(method,path);r=c.getresponse();r.read();status=r.status;c.close()
   assert status==(200 if path in ['/','/js/work-api.js','/js/views/work.js'] else 404),(method,path,status)
finally:server.shutdown();server.server_close()
result={'archive':str(archive),'sha256':digest,'runtime_files':len(files),'frozen_files':len(frozen),'all_zip_bytes_equal_source':True,'static_GET_HEAD_checks':14,'extracted_root':str(check),'secret_marker_hits':[p.relative_to(ROOT).as_posix() for p in files if b'mr_' in p.read_bytes() or b'sk-' in p.read_bytes()]}
# Literal prefix labels already exist in the pinned baseline; do not restyle legacy views in A1.
assert set(result['secret_marker_hits'])=={'js/views/chat.js','js/views/settings.js','js/views/skills.js'}
for name in result['secret_marker_hits']:
 assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
result['secret_marker_note']='Baseline-only literal key-prefix labels/placeholders; these three files are byte-identical to base. No credentials used in build.'
(ROOT/'reports/a1/package-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
