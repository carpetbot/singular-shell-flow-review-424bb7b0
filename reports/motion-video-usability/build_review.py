"""Build runtime-only review ZIP and portable source verification copy."""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/motion-video-usability'
files=[Path(p) for p in ['index.html','styles.css','proxy.py','MOTION_VIDEO_REVIEW.md']]
files+=sorted(p.relative_to(ROOT) for p in (ROOT/'js').rglob('*.js'))
for name in ['claw__motion-trimmer','impossibuild__prospect-to-cold-email','impossibuild__model-jury','claw__motion-trimmer-video']:
 files+=sorted(p.relative_to(ROOT) for p in (ROOT/'skills'/name).rglob('*') if p.is_file() and p.suffix in {'.json','.md'})
assert len(files)==len(set(files))==40
archive=ROOT/'dist/motion-trimmer-video-review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(ROOT/name,str(name))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert z.namelist()==[str(n) for n in files]
 for name in files:assert z.read(str(name))==(ROOT/name).read_bytes()
 package=OUT/'packaged-runtime';package.mkdir(parents=True,exist_ok=True);z.extractall(package)
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(sha+'  '+archive.name+'\n')
manifest=[{'file':str(n),'source_sha256':hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),'copied_sha256':hashlib.sha256((package/n).read_bytes()).hexdigest()} for n in files]
(OUT/'package-manifest.json').write_text(json.dumps({'sha256':sha,'regular_files':len(files),'crc_ok':True,'files':manifest},indent=2)+'\n')
# A source checkout equivalent: no reports except the legacy public fixture,
# no nested runtime builds, screenshots, private design, cache or original paths.
copy=OUT/'relocated-source';copy.mkdir(exist_ok=True)
for name in files+[Path('README.md'),Path('reports/catalog-live.json')]:
 target=copy/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
shutil.copytree(ROOT/'tests',copy/'tests',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
# Fail rather than accidentally loading original source or home pricing files.
forbidden=[str(ROOT),str(ROOT.parent/'motion-trimmer-video-pricing.json'),str(ROOT.parent/'video-defaults-pricing.json')]
(copy/'deny-original.cjs').write_text("const fs=require('node:fs');const {syncBuiltinESMExports}=require('node:module');const forbidden="+json.dumps(forbidden)+";function check(p){const s=p instanceof URL?require('node:url').fileURLToPath(p):String(p);if(forbidden.some(x=>s===x||s.startsWith(x+'/'))&&!s.startsWith(__dirname+'/'))throw Error('ORIGINAL PATH DENIED '+s);}for(const k of ['readFileSync','readFile','openSync','open']){const f=fs[k];fs[k]=function(p,...a){check(p);return f.call(this,p,...a);};}const f=fs.promises.readFile;fs.promises.readFile=function(p,...a){check(p);return f.call(this,p,...a);};syncBuiltinESMExports();\n")
(copy/'sitecustomize.py').write_text('import sys,os\nROOT=os.path.dirname(__file__)\nFORBIDDEN='+repr(forbidden)+'\ndef audit(event,args):\n if event=="open" and isinstance(args[0],(str,bytes)):\n  p=os.path.abspath(os.fsdecode(args[0]))\n  if any(p==x or p.startswith(x+"/") for x in FORBIDDEN) and not p.startswith(ROOT+"/"): raise PermissionError("ORIGINAL PATH DENIED "+p)\nsys.addaudithook(audit)\n')
for name in ['lite','jury','legacy','video']:(copy/'reports/verification'/name).mkdir(parents=True,exist_ok=True)
# Frozen old three-flow UI, engines and templates are exact deployment-base bytes.
protected=json.loads((ROOT/'reports/motion-video/protected-hashes.json').read_text())
for item in protected:
 data=(ROOT/item['file']).read_bytes();base=subprocess.check_output(['git','show','378d6f4:'+item['file']],cwd=ROOT)
 assert data==base,item['file'];assert hashlib.sha256(data).hexdigest()==item['sha256']
(OUT/'protected-hashes.json').write_text(json.dumps(protected,indent=2)+'\n')
print(json.dumps({'archive':str(archive),'sha256':sha,'files':len(files),'protected_files':len(protected),'relocated_source':str(copy),'package':str(package)},indent=2))
