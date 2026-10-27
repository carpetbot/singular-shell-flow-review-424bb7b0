"""Explicit runtime allowlist; CRC/source bytes; exact copied server GET/HEAD probes."""
from pathlib import Path
import hashlib,http.client,http.server,importlib.util,json,shutil,threading,zipfile
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent
COPY=ROOT/'dist/motion-trimmer-video-review';ZIP=ROOT/'dist/motion-trimmer-video-review.zip'
files=['index.html','styles.css','proxy.py','MOTION_VIDEO_REVIEW.md']
files += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'js').rglob('*.js'))]
for skill in ['claw__motion-trimmer','impossibuild__prospect-to-cold-email','impossibuild__model-jury','claw__motion-trimmer-video']:
 files += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'skills'/skill).rglob('*')) if p.is_file() and (p.name in ['singular.flow.json','singular.skill.json'] or p.suffix=='.md')]
assert len(files)==len(set(files))
if COPY.exists():shutil.rmtree(COPY)
COPY.mkdir(parents=True)
for name in files:
 dst=COPY/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dst)
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(COPY/name,name)
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None
 assert sorted(z.namelist())==sorted(files)
 for name in files:assert z.read(name)==(COPY/name).read_bytes()==(ROOT/name).read_bytes(),name
sha=hashlib.sha256(ZIP.read_bytes()).hexdigest();(ZIP.with_suffix('.zip.sha256')).write_text(sha+'  '+ZIP.name+'\n')
spec=importlib.util.spec_from_file_location('packaged_proxy',COPY/'proxy.py');proxy=importlib.util.module_from_spec(spec);spec.loader.exec_module(proxy)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler);threading.Thread(target=server.serve_forever,daemon=True).start();probes=[]
try:
 for method in ['GET','HEAD']:
  for path in ['/','/index.html?x=1','/js/video.js','/proxy.py','/%70roxy%2epy?x=1','/%2570roxy%252epy','/js/','/tests/video.test.mjs','/MOTION_VIDEO_REVIEW.md','/reports/','/../proxy.py','/js/%2e%2e/proxy.py']:
   c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3);c.request(method,path);r=c.getresponse();status=r.status;r.read();c.close();expected=200 if path in ['/','/index.html?x=1','/js/video.js'] else 404;assert status==expected,(method,path,status);probes.append({'method':method,'path':path,'status':status})
finally:server.shutdown();server.server_close()
result={'zip':str(ZIP),'sha256':sha,'regular_files':len(files),'crc':'PASS','source_copy_zip_bytes':'PASS','runtime_allowlist':files,'copied_server_probes':probes}
(REPORT/'package-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
