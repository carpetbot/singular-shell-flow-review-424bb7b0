"""Presentation-only guard against the reviewed deployed commit. Read-only."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE='9f5beb17e33a82d67b41ab3085bece985ef1d75c'
def original(path):
    return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)
locked=['js/flow.js','js/api.js','proxy.py','js/store.js','skills/claw__motion-trimmer/singular.skill.json']
locked+=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'skills').glob('**/prompts/*') if p.is_file())
hashes={}
for path in locked:
    current=(ROOT/path).read_bytes()
    assert current==original(path),f'LOCKED FILE CHANGED: {path}'
    hashes[path]=hashlib.sha256(current).hexdigest()
flow='skills/impossibuild__prospect-to-cold-email/singular.flow.json'
current=json.loads((ROOT/flow).read_text())
for step in current['runtime']['steps']:
    step.pop('plain_label',None);step.pop('why',None)
assert current==json.loads(original(flow)),'Manifest changed beyond optional presentation metadata'
# The rest of the JSON is also literally unchanged, not merely semantically equal.
stripped=re.sub(rb'^        "(?:plain_label|why)": .*\n',b'',(ROOT/flow).read_bytes(),flags=re.M)
assert stripped==original(flow),'Non-metadata manifest bytes changed'
original_zip='dist/singular-shell-flow.zip'
assert (ROOT/original_zip).read_bytes()==original(original_zip),'Original reviewed archive was modified'
expected=json.loads((ROOT/'reports/ui-locked-baseline.json').read_text())
assert expected==hashes,'Before/after locked hashes differ'
print(json.dumps({'baseline':BASE,'locked_files_verified':len(locked),'sha256':hashes,'manifest':'Only steps[].plain_label and why added; all other bytes unchanged','original_reviewed_zip_sha256':hashlib.sha256((ROOT/original_zip).read_bytes()).hexdigest()},indent=2))
