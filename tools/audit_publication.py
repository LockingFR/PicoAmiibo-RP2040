"""Audit tracked publication inputs without inspecting private profiles."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN={'.bin','.nfc','.uf2','.elf','.map','.zip','.sqlite','.sqlite3','.db','.pcap','.pcapng'}
PATTERNS={
    'workstation user path':re.compile(rb'[A-Za-z]:[/\\]{1,2}Users[/\\]{1,2}[^/\\\s]+',re.I),
    'GitHub access token':re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{30,})'),
    'private key':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}

def audit(root=ROOT):
    names=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    files={};errors=[]
    for name in filter(None,names):
        path=root/name
        if path.suffix.lower() in FORBIDDEN or any(p in {'private','.deps','build','dist','artifacts'} for p in path.relative_to(root).parts):
            errors.append(name+': forbidden publication input')
            continue
        raw=path.read_bytes()
        if path.suffix.lower() not in {'.png','.ico','.jpg','.jpeg'}:
            for label,pattern in PATTERNS.items():
                if pattern.search(raw):errors.append(name+': '+label)
        files[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    if errors:raise SystemExit('\n'.join(errors))
    return {'result':'PASS','files_checked':len(files),'files':files}

if __name__=='__main__':
    result=audit()
    print(json.dumps({'result':result['result'],'files_checked':result['files_checked']}))
