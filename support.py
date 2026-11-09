"""Local reproducibility helpers; no network or provider calls."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def dump(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())

def manifest(output):
    paths=[ROOT/'core.py',ROOT/'generate.py',ROOT/'run.py',ROOT/'support.py']
    paths += sorted(p for folder in ['data','models'] for p in (ROOT/folder).rglob('*') if p.is_file())
    paths += sorted(p for p in Path(output).rglob('*') if p.is_file() and p.name!='manifest.json')
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    dump(Path(output)/'manifest.json',{'sha256':hashes})

def verify_manifest():
    record=json.loads((ROOT/'results/manifest.json').read_text())
    for path,digest in record['sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
