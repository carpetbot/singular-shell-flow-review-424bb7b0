"""Build and verify a local runtime ZIP; no upload or deployment operations."""
from pathlib import Path
import hashlib
import http.client
import http.server
import importlib.util
import json
import shutil
import threading
import zipfile

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'reports/model-jury'
DEST=ROOT/'dist/model-jury-shell'
ARCHIVE=ROOT/'dist/model-jury-review.zip'
files={name:ROOT/name for name in ('index.html','styles.css','proxy.py')}
for folder in ('js','skills'):
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and p.suffix in ('.js','.json','.md'):files[str(p.relative_to(ROOT))]=p
files['README.md']=ROOT/'MODEL_JURY_README.md'
if DEST.exists():shutil.rmtree(DEST)
DEST.mkdir(parents=True)
for name,source in files.items():
 target=DEST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
with zipfile.ZipFile(ARCHIVE,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,source in sorted(files.items()):
  info=zipfile.ZipInfo('model-jury-shell/'+name,date_time=(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
  z.writestr(info,source.read_bytes())
with zipfile.ZipFile(ARCHIVE) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(files)
 for name,source in files.items():assert z.read('model-jury-shell/'+name)==source.read_bytes()==(DEST/name).read_bytes(),name
 assert not any(any(s in name for s in ('DESIGN.md','CODEX-BRIEF.md','rules.py','test_rules.py','__pycache__','tests/')) for name in z.namelist())
# Verify original seven prompt bytes against the private archive without packaging it.
original=ROOT.parent/'model-jury/prompts'
for source in (ROOT/'skills/impossibuild__model-jury/prompts').glob('*.md'):assert source.read_bytes()==(original/source.name).read_bytes()
statuses=[]
for root in (ROOT,DEST):
 spec=importlib.util.spec_from_file_location('verify_proxy',root/'proxy.py');assert spec and spec.loader
 proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  for method in ('GET','HEAD'):
   for path in ('/proxy.py','/%70roxy%2epy?x=1','/tests/graph.test.mjs','/tests/test_model_jury.py','/README.md','/MODEL_JURY_README.md','/MODEL_JURY_REVIEW.md','/reports/model-jury/legacy_compare.py','/js/','/js/%2e%2e/proxy.py'):
    c=http.client.HTTPConnection('127.0.0.1',server.server_port);c.request(method,path);r=c.getresponse();r.read();assert r.status==404,(root,method,path,r.status);statuses.append({'root':str(root),'method':method,'path':path,'status':r.status});c.close()
   for path in ('/','/js/graph.js','/js/graph-ui.js','/skills/impossibuild__model-jury/singular.flow.json','/skills/impossibuild__model-jury/prompts/3-judge.user.md'):
    c=http.client.HTTPConnection('127.0.0.1',server.server_port);c.request(method,path);r=c.getresponse();r.read();assert r.status==200,(root,method,path,r.status);c.close()
 finally:server.shutdown();server.server_close();thread.join()
sha=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
ARCHIVE.with_suffix('.zip.sha256').write_text(sha+'  '+ARCHIVE.name+'\n')
receipt={'archive':str(ARCHIVE),'sha256':sha,'bytes':ARCHIVE.stat().st_size,'runtime_files':len(files),'crc':'PASS','all_bytes_equal':True,'verbatim_new_prompts':7,'private_design_sources_packaged':False,'external_push':False,'deployed':False,'public_url':None,'files':sorted(files)}
(REPORT/'package.json').write_text(json.dumps(receipt,indent=2)+'\n')
(REPORT/'static-denials.json').write_text(json.dumps(statuses,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
