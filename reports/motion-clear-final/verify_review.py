"""Local runtime packaging and relocation checks; no network/model calls."""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, tempfile, zipfile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/motion-clear-final'
files=[Path(p) for p in ['index.html','styles.css','proxy.py','MOTION_VIDEO_REVIEW.md']]
files+=sorted(p.relative_to(ROOT) for p in (ROOT/'js').rglob('*.js'))
for name in ['claw__motion-trimmer','impossibuild__prospect-to-cold-email','impossibuild__model-jury','claw__motion-trimmer-video']:
 files+=sorted(p.relative_to(ROOT) for p in (ROOT/'skills'/name).rglob('*') if p.is_file() and p.suffix in {'.json','.md'})
assert len(files)==len(set(files))==40
archive=ROOT/'dist/motion-trimmer-video-review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(ROOT/name,str(name))
work=Path(tempfile.mkdtemp(prefix='motion-clear-check-',dir=os.environ['TMPDIR']))
package=work/'runtime'
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert z.namelist()==[str(n) for n in files]
 z.extractall(package)
 for n in files:assert z.read(str(n))==(ROOT/n).read_bytes()==(package/n).read_bytes()
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(sha+'  '+archive.name+'\n')
manifest=[{'file':str(n),'source_sha256':hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),'extracted_sha256':hashlib.sha256((package/n).read_bytes()).hexdigest()} for n in files]
(OUT/'package-manifest.json').write_text(json.dumps({'sha256':sha,'files':manifest,'regular_files':len(files),'crc_ok':True},indent=2)+'\n')
protected=json.loads((ROOT/'reports/motion-video/protected-hashes.json').read_text())
for item in protected:
 data=(ROOT/item['file']).read_bytes()
 assert data==subprocess.check_output(['git','show','378d6f4:'+item['file']],cwd=ROOT)
 assert hashlib.sha256(data).hexdigest()==item['sha256']
assert (ROOT/'proxy.py').read_bytes()==subprocess.check_output(['git','show','HEAD:proxy.py'],cwd=ROOT)
copy=work/'relocated-source';copy.mkdir()
for name in files+[Path('README.md'),Path('reports/catalog-live.json')]:
 target=copy/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
shutil.copytree(ROOT/'tests',copy/'tests',ignore=shutil.ignore_patterns('__pycache__'))
forbidden=[str(ROOT),str(ROOT.parent/'motion-trimmer-video-pricing.json'),str(ROOT.parent/'video-defaults-pricing.json')]
(copy/'deny-original.cjs').write_text("const fs=require('node:fs');const {syncBuiltinESMExports}=require('node:module');const forbidden="+json.dumps(forbidden)+";function check(p){const s=p instanceof URL?require('node:url').fileURLToPath(p):String(p);if(forbidden.some(x=>s===x||s.startsWith(x+'/')))throw Error('ORIGINAL PATH DENIED '+s);}for(const k of ['readFileSync','readFile','openSync','open']){const f=fs[k];fs[k]=function(p,...a){check(p);return f.call(this,p,...a);};}const f=fs.promises.readFile;fs.promises.readFile=function(p,...a){check(p);return f.call(this,p,...a);};syncBuiltinESMExports();\n")
(copy/'sitecustomize.py').write_text('import sys,os\nFORBIDDEN='+repr(forbidden)+'\ndef audit(event,args):\n if event=="open" and isinstance(args[0],(str,bytes)):\n  p=os.path.abspath(os.fsdecode(args[0]))\n  if any(p==x or p.startswith(x+"/") for x in FORBIDDEN): raise PermissionError("ORIGINAL PATH DENIED "+p)\nsys.addaudithook(audit)\n')
def run(label,cmd,cwd,env=None):
 with (OUT/(label+'.log')).open('w') as log:
  result=subprocess.run([str(x) for x in cmd],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
 assert result.returncode==0,label
run('source-node',['node','--test',*sorted((ROOT/'tests').glob('*.test.mjs'))],ROOT)
run('relocated-node',['node','--require',copy/'deny-original.cjs','--test',*sorted((copy/'tests').glob('*.test.mjs'))],Path.home())
env=os.environ.copy();env['PYTHONPATH']=str(copy);env['VIDEO_EVIDENCE']=str(copy/'reports/verification/video')
Path(env['VIDEO_EVIDENCE']).mkdir(parents=True)
run('relocated-python-targeted',['python3','-m','unittest','discover','-s',copy/'tests','-p','test_video_browser.py','-k','test_clear_finished_selection_preserves_pending','-v'],Path.home(),env)
env=os.environ.copy();env['VIDEO_APP_ROOT']=str(package);env['VIDEO_EVIDENCE']=str(OUT/'packaged/video')
Path(env['VIDEO_EVIDENCE']).mkdir(parents=True,exist_ok=True)
run('packaged-python-targeted',['python3','-m','unittest','discover','-s','tests','-p','test_video_browser.py','-k','test_clear_finished_selection_preserves_pending','-v'],ROOT,env)
# The original-path guard must actually refuse original fixture reads.
run('portability-guard-node',['node','--require',copy/'deny-original.cjs','-e',"const fs=require('node:fs');try{fs.readFileSync("+json.dumps(str(ROOT/'tests/fixtures/video-pricing.json'))+");process.exit(1)}catch(e){if(!e.message.includes('ORIGINAL PATH DENIED'))throw e;console.log(e.message)}"],Path.home())
env=os.environ.copy();env['PYTHONPATH']=str(copy)
run('portability-guard-python',['python3','-c',"try:\n open("+repr(str(ROOT/'tests/fixtures/video-pricing.json'))+")\n raise AssertionError('original read allowed')\nexcept PermissionError as e:\n print(e)"],Path.home(),env)
def count(label,node=False):
 text=(OUT/(label+'.log')).read_text()
 if node:
  match=re.search(r'(?:ℹ |# )pass (\d+)',text);assert match
  n=int(match[1])
  assert re.search(r'(?:ℹ |# )fail 0',text) and re.search(r'(?:ℹ |# )skipped 0',text)
 else:
  match=re.search(r'Ran (\d+) tests? in',text);assert match
  n=int(match[1]);assert '\nOK\n' in text and 'skipped=' not in text
 return n
counts={'source_node':count('source-node',True),'source_python':count('source-python'),'relocated_node':count('relocated-node',True),'relocated_python_targeted':count('relocated-python-targeted'),'packaged_python_targeted':count('packaged-python-targeted')}
assert counts=={'source_node':94,'source_python':45,'relocated_node':94,'relocated_python_targeted':1,'packaged_python_targeted':1},counts
summary={'archive':str(archive.relative_to(ROOT)),'sha256':sha,'runtime_files':len(files),'crc_ok':True,'all_source_archive_extracted_bytes_equal':True,'protected_legacy_files':len(protected),'proxy_unchanged_from_HEAD':True,**counts,'relocated_full_python_rerun':False,'workspaces_outside_evidence':str(work)}
(OUT/'verification-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
