"""Read back final suite counts, runtime bytes and protected-source boundaries."""
import collections,hashlib,json,re,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'reports/a2'
package=json.loads((E/'c3-package-verification.json').read_text())
archive=ROOT/'dist/shell-ux-v1-a2.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==package['sha256']
assert (archive.with_suffix('.zip.sha256')).read_text().split()[0]==package['sha256']
results={}
for label in ['c3-source','c3-packaged']:
 node=(E/(label+'-node.log')).read_text();py=(E/(label+'-python.log')).read_text()
 assert re.search(r'tests 98\s',node) and re.search(r'pass 98\s',node) and re.search(r'fail 0\s',node) and re.search(r'skipped 0\s',node)
 assert re.search(r'Ran 95 tests in [\d.]+s\s+OK\s',py)
 assert not any(x in py for x in ['Traceback (most recent call last)','BrokenPipeError','Unexpected upstream','FAILED ('])
 cases=re.findall(r'^test_\w+ \(([^)]+)\)',py,re.M)
 counts=collections.Counter(x.split('.')[1] for x in cases)
 assert len(cases)==95 and counts['DurableVideoBrowser']==19 and counts['RunStoreBrowser']==13 and counts['WorkCards']==7
 results[label]={'node':{'tests':98,'pass':98,'fail':0,'skipped':0},'python':{'tests':95,'pass':95,'fail':0,'skipped':0,'classes':dict(counts)},'no_teardown_tracebacks':True}
for name in ['js/video.js','js/run-store.js','js/video-runtime.js']:
 assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show','f6106f059d9f0749aaf1e078159d6f38ee4fc77f:'+name],cwd=ROOT)
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(package['manifest'])
 for name,digest in package['manifest'].items():
  for p in [ROOT/name,E/'c3-package-check'/name,E/'c3-source-app'/name,E/'c3-packaged-app'/name]:
   assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,p
  assert hashlib.sha256(z.read(name)).hexdigest()==digest
new_runtime=[ROOT/'js/poster-cache.js',ROOT/'js/views/work.js']
patterns={'dynamic_execution':r'\beval\(|\bexec\(|new Function\(', 'raw_html':r'innerHTML\s*=', 'credential_literal':r'(?:apiKey|api_key|password|authorization)\s*[:=]\s*[\"\'][^\"\']{6,}[\"\']'}
scan={k:[str(p.relative_to(ROOT)) for p in new_runtime if re.search(pattern,p.read_text(),re.I)] for k,pattern in patterns.items()}
assert not any(scan.values())
result={'sha256':package['sha256'],'runtime_files':package['runtime_files'],'frozen_files':package['frozen_files'],'static_GET_HEAD_checks':package['static_GET_HEAD_checks'],'suite_results':results,'all_source_extracted_and_tested_runtime_hashes_match':True,'protected_engine_store_runtime_equal_reviewed_start':True,'new_runtime_static_scan':scan,'baseline_literal_prefix_files':package['baseline_literal_prefix_files']}
(E/'c3-final-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
