"""Run complete suites in an evidence-only copy; never mutate baseline reports.
python3 tests/verify_a2.py [--runtime extracted-root] [--label c3-source]
"""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--runtime',type=Path,default=ROOT);a.add_argument('--label',default='c3-source');args=a.parse_args()
assert args.label.replace('-','').isalnum()
evidence=ROOT/'reports/a2';evidence.mkdir(exist_ok=True)
copy=evidence/(args.label+'-app')
if copy.exists():shutil.rmtree(copy)
copy.mkdir()
for name in ['index.html','styles.css','proxy.py']:shutil.copy2(args.runtime/name,copy/name)
for name in ['js','skills']:shutil.copytree(args.runtime/name,copy/name)
shutil.copytree(ROOT/'tests',copy/'tests',ignore=shutil.ignore_patterns('__pycache__'))
(copy/'reports').mkdir();shutil.copy2(ROOT/'reports/catalog-live.json',copy/'reports/catalog-live.json')
env=os.environ.copy()
# Runtime roots must be the relocated copy, not inherited source overrides.
for k in ['VIDEO_APP_ROOT','SINGULAR_UI_APP_ROOT','JURY_APP_ROOT','VIDEO_EVIDENCE','VIDEO_JURY_EVIDENCE']:env.pop(k,None)
results=[]
for kind,cmd in [('node',['node','--test',*[str(p.relative_to(copy)) for p in sorted((copy/'tests').glob('*.test.mjs'))]]),('python',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'])]:
 log=evidence/(args.label+'-'+kind+'.log')
 with log.open('w') as f:r=subprocess.run(cmd,cwd=copy,env=env,stdout=f,stderr=subprocess.STDOUT)
 print(kind,'exit',r.returncode,'log',log,flush=True);print(log.read_text()[-2400:],flush=True)
 results.append({'suite':kind,'exit':r.returncode,'log':str(log)})
(evidence/(args.label+'-results.json')).write_text(json.dumps(results,indent=2)+'\n')
sys.exit(any(x['exit'] for x in results))
