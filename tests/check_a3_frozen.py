"""Frozen runtime verification; never reads credentials or contacts upstream."""
import hashlib,json,subprocess,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='d95c15323d435f19d2ff634d92484c4b9503b3f5'
files=[ROOT/'js/video.js',*sorted(p for p in (ROOT/'skills').rglob('*') if p.is_file())]
result={}
for p in files:
 rel=p.relative_to(ROOT).as_posix();data=p.read_bytes();assert data==subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT),rel
 result[rel]=hashlib.sha256(data).hexdigest()
assert result['js/video.js']=='71986db49b64763229a90e4d4fe10ae78ebfc45b27070f6d32e675e21a31450b'
runtime=[ROOT/'index.html',ROOT/'styles.css',ROOT/'proxy.py',*sorted((ROOT/'js').rglob('*.js')),*files[1:]]
secret_hits=[]
for p in runtime:
 if re.search(rb'\b(?:m[r]_|s[k]-)[A-Za-z0-9_-]{12,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY',p.read_bytes()):secret_hits.append(p.relative_to(ROOT).as_posix())
assert not secret_hits,secret_hits
print(json.dumps({'base':BASE,'frozen_count':len(result),'frozen_sha256':result,'credential_pattern_hits':secret_hits},indent=2))
