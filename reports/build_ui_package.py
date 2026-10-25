"""Build the review runtime only; never deploys or writes outside this repository."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'dist/singular-shell-ui'
ARCHIVE=ROOT/'dist/singular-shell-ui.zip'
files={name:ROOT/name for name in ('index.html','styles.css','proxy.py')}
files.update({str(p.relative_to(ROOT)):p for folder in ('js','skills') for p in (ROOT/folder).rglob('*') if p.is_file()})
files['README.md']=ROOT/'UI_README.md'
if DEST.exists():shutil.rmtree(DEST)
DEST.mkdir(parents=True)
for name,source in files.items():
    path=DEST/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,path)
with zipfile.ZipFile(ARCHIVE,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for name in sorted(files):
        info=zipfile.ZipInfo('singular-shell-ui/'+name,date_time=(2026,10,25,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
        archive.writestr(info,files[name].read_bytes())
receipt={'archive':str(ARCHIVE),'bytes':ARCHIVE.stat().st_size,'sha256':hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),'runtime_files':len(files),'files':sorted(files)}
(ROOT/'reports/ui-package.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
