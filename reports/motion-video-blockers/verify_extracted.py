"""Offline tests run against a fresh ZIP extraction, not worktree runtime."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
APP=REPORT/'package-check-final'
assert not APP.exists(), 'Use a fresh extraction path'
with zipfile.ZipFile(ROOT/'dist/motion-trimmer-video-review.zip') as archive:
 assert archive.testzip() is None
 archive.extractall(APP)
 members=archive.namelist()
 assert all((APP/name).read_bytes()==(ROOT/name).read_bytes() for name in members)
 assert not any(name.startswith(('tests/','reports/','.git/')) for name in members)
shutil.copytree(ROOT/'tests',APP/'tests',ignore=shutil.ignore_patterns('__pycache__'))
(APP/'reports').mkdir()
shutil.copyfile(ROOT/'reports/catalog-live.json',APP/'reports/catalog-live.json')
env=os.environ.copy()
# All generated evidence is isolated from both original and prior review reports.
for name,folder in [('VIDEO_EVIDENCE','video'),('VIDEO_LEGACY_EVIDENCE','legacy'),('VIDEO_LITE_EVIDENCE','lite'),('VIDEO_JURY_EVIDENCE','jury')]:
 destination=APP/'reports/verification-evidence'/folder;destination.mkdir(parents=True,exist_ok=True);env[name]=str(destination)
commands=[('packaged-node.txt',['node','--test',*[str(p.relative_to(APP)) for p in sorted((APP/'tests').glob('*.test.mjs'))]]),('packaged-python.txt',['python3','-m','unittest','discover','-s','tests','-p','test_*.py','-v'])]
results=[]
for filename,command in commands:
 with (REPORT/filename).open('w') as log:
  result=subprocess.run(command,cwd=APP,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 results.append({'command':command,'exit':result.returncode,'log':filename})
 assert result.returncode==0, results[-1]
# Test fixtures are never written into the distributable archive.
with zipfile.ZipFile(ROOT/'dist/motion-trimmer-video-review.zip') as archive:
 assert archive.namelist()==members
 assert all(archive.read(name)==(ROOT/name).read_bytes()==(APP/name).read_bytes() for name in members)
summary={'runtime_source_zip_extraction_bytes':'PASS','regular_files':len(members),'sha256':hashlib.sha256((ROOT/'dist/motion-trimmer-video-review.zip').read_bytes()).hexdigest(),'tests':results}
(REPORT/'extracted-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
