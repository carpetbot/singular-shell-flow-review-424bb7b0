"""Post-suite A3 provenance: archive, source, relocated runtime and tested copies."""
import hashlib,json,re,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
info=json.loads((ROOT/'reports/a3/c4/package-verification.json').read_text())
archive=ROOT/'dist/shell-ux-v1-a3.zip';digest=hashlib.sha256(archive.read_bytes()).hexdigest();assert digest==info['sha256']
assert (ROOT/'dist/shell-ux-v1-a3.zip.sha256').read_text()==digest+'  '+archive.name+'\n'
manifest=info['manifest'];runtimes=[ROOT,ROOT/'reports/a3/package-a3/relocated/runtime',ROOT/'reports/a3/regression-a3-final-source-app',ROOT/'reports/a3/regression-a3-final-packaged-app']
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(manifest)
 for name,expected in manifest.items():
  data=z.read(name);assert hashlib.sha256(data).hexdigest()==expected
  for runtime in runtimes:assert (runtime/name).read_bytes()==data,(runtime,name)
counts={}
for label in ['a3-final-source','a3-final-packaged']:
 results=json.loads((ROOT/'reports/a3'/f'{label}-results.json').read_text());assert len(results)==2 and all(r['exit']==0 for r in results)
 node=(ROOT/'reports/a3'/f'{label}-node.log').read_text();python=(ROOT/'reports/a3'/f'{label}-python.log').read_text()
 n=re.search(r'(?:ℹ|#) tests (\d+)',node);passed=re.search(r'(?:ℹ|#) pass (\d+)',node);p=re.search(r'Ran (\d+) tests? in ',python)
 assert n and passed and n[1]==passed[1] and p and re.search(r'\nOK\s*$',python)
 assert not re.search(r'\b(?:FAIL|ERROR):|\(skipped=',python)
 counts[label]={'node':int(n[1]),'python':int(p[1]),'results':str(ROOT/'reports/a3'/f'{label}-results.json')}
assert counts['a3-final-source']['node']==counts['a3-final-packaged']['node']
assert counts['a3-final-source']['python']==counts['a3-final-packaged']['python']
base='7efe1eddb28fd30d2bd93229103917102985be16';known=set(subprocess.check_output(['git','ls-tree','-r','--name-only',base],cwd=ROOT,text=True).splitlines());changed=[]
for name in sorted(manifest):
 if name not in known or (ROOT/name).read_bytes()!=subprocess.check_output(['git','show',base+':'+name],cwd=ROOT):changed.append(name)
result={'archive':str(archive),'sha256':digest,'runtime_files':len(manifest),'all_runtime_bytes_match_source_archive_relocated_and_both_tested_copies':True,'suites':counts,'changed_runtime_since_A2':changed,'frozen_files':info['frozen_files'],'static_GET_HEAD_checks':info['static_GET_HEAD_checks'],'no_deployment':True}
(ROOT/'reports/a3/c4/final-provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
