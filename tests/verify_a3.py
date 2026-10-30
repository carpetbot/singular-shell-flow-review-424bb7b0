"""Isolated A3 regression runner; labels preserve earlier checkpoint evidence."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--label',default='full');p.add_argument('--runtime',type=Path);p.add_argument('--checkpoint2',action='store_true');a=p.parse_args()
if not a.label.replace('-','').replace('_','').isalnum():p.error('simple evidence label required')
evidence=ROOT/'reports/a3';evidence.mkdir(exist_ok=True)
copy=evidence/('regression-'+a.label+'-app')
if copy.exists():shutil.rmtree(copy)
copy.mkdir();runtime=a.runtime or ROOT
if a.checkpoint2:
 for rel in subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=ROOT,text=True).splitlines():
  if rel in ['index.html','styles.css','proxy.py','reports/catalog-live.json'] or rel.startswith(('js/','skills/','tests/')):
   dest=copy/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT))
 for rel in ['index.html','styles.css','proxy.py','js/app.js','js/views/skills.js','js/views/create.js','tests/test_a3_create_browser.py','tests/test_lite_pro.py']:
  shutil.copy2(ROOT/rel,copy/rel)
else:
 for name in ['index.html','styles.css','proxy.py']:shutil.copy2(runtime/name,copy/name)
 for name in ['js','skills']:shutil.copytree(runtime/name,copy/name)
 shutil.copytree(ROOT/'tests',copy/'tests',ignore=shutil.ignore_patterns('__pycache__'))
 (copy/'reports').mkdir(exist_ok=True);shutil.copy2(ROOT/'reports/catalog-live.json',copy/'reports/catalog-live.json')
env=os.environ.copy()
for k in ['VIDEO_APP_ROOT','SINGULAR_UI_APP_ROOT','JURY_APP_ROOT','VIDEO_EVIDENCE','VIDEO_JURY_EVIDENCE']:env.pop(k,None)
results=[]
for kind,cmd in [('node',['node','--test',*[str(p.relative_to(copy)) for p in sorted((copy/'tests').glob('*.test.mjs'))]]),('python',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'])]:
 log=evidence/(a.label+'-'+kind+'.log')
 if log.exists():raise RuntimeError('Evidence already exists: '+str(log))
 with log.open('w') as f:r=subprocess.run(cmd,cwd=copy,env=env,stdout=f,stderr=subprocess.STDOUT)
 print(kind,'exit',r.returncode,'log',log,flush=True);print(log.read_text()[-3000:],flush=True)
 results.append({'suite':kind,'exit':r.returncode,'log':str(log)})
(evidence/(a.label+'-results.json')).write_text(json.dumps(results,indent=2)+'\n')
sys.exit(any(x['exit'] for x in results))
