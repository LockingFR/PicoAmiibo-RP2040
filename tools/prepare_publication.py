"""Export a clean tracked source snapshot into a new, independent Git repository."""
import argparse
from pathlib import Path
import subprocess
from audit_publication import audit,ROOT

def run(*args,cwd=ROOT):
    return subprocess.check_output(args,cwd=cwd,text=True).strip()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args();destination=args.destination.resolve()
    if run('git','status','--porcelain'):raise SystemExit('Commit the reviewed sources before export')
    if destination==ROOT or ROOT.is_relative_to(destination):raise SystemExit('Destination cannot contain the source repository')
    if destination.exists() and any(destination.iterdir()):raise SystemExit('Destination must be new or empty; nothing will be replaced')
    checked=audit();destination.mkdir(parents=True,exist_ok=True)
    for name in checked['files']:
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
        # Use committed blobs, preserving exact upstream hashes and excluding ignored files.
        path.write_bytes(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT))
    run('git','init','-b','main',cwd=destination)
    run('git','config','user.name','LockingFR',cwd=destination)
    run('git','config','user.email','105942155+LockingFR@users.noreply.github.com',cwd=destination)
    run('git','add','--all',cwd=destination)
    audit(destination)
    run('git','commit','-m','Release English PicoAmiibo firmware project and Manager 1.1.0',cwd=destination)
    print('Prepared publication:',destination)
    print('Commit:',run('git','rev-parse','HEAD',cwd=destination))
    print('No remotes created or network writes performed.')

if __name__=='__main__':main()
