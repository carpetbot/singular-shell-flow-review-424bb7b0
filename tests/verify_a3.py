"""Run checkpoint suites in reports/a3 only; leave baseline evidence intact."""
import json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
evidence=ROOT/'reports/a3';evidence.mkdir(exist_ok=True)
copy=evidence/'regression-app'
if copy.exists():shutil.rmtree(copy)
copy.mkdir()
for name in ['index.html','styles.css','proxy.py']:shutil.copy2(ROOT/name,copy/name)
for name in ['js','skills']:shutil.copytree(ROOT/name,copy/name)
shutil.copytree(ROOT/'tests',copy/'tests',ignore=shutil.ignore_patterns('__pycache__'))
(copy/'reports').mkdir();shutil.copy2(ROOT/'reports/catalog-live.json',copy/'reports/catalog-live.json')
env=os.environ.copy()
for k in ['VIDEO_APP_ROOT','SINGULAR_UI_APP_ROOT','JURY_APP_ROOT','VIDEO_EVIDENCE','VIDEO_JURY_EVIDENCE']:env.pop(k,None)
results=[]
for kind,cmd in [('node',['node','--test',*[str(p.relative_to(copy)) for p in sorted((copy/'tests').glob('*.test.mjs'))]]),('python',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'])]:
 log=evidence/('full-'+kind+'.log')
 with log.open('w') as f:r=subprocess.run(cmd,cwd=copy,env=env,stdout=f,stderr=subprocess.STDOUT)
 print(kind,'exit',r.returncode,'log',log,flush=True);print(log.read_text()[-2400:],flush=True)
 results.append({'suite':kind,'exit':r.returncode,'log':str(log)})
(evidence/'full-results.json').write_text(json.dumps(results,indent=2)+'\n')
sys.exit(any(x['exit'] for x in results))
