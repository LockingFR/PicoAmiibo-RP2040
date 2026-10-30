from pathlib import Path
import hashlib,json,shutil,struct,subprocess,sys,runpy

ROOT=Path(__file__).resolve().parents[1];PACKAGE=ROOT/'dist/PicoAmiibo-Manager'
VERSION=runpy.run_path(str(ROOT/'manager/__init__.py'))['__version__']
if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
    raise SystemExit('Commit the application sources/docs before producing a release package')
exe=PACKAGE/'PicoAmiibo-Manager.exe'
exe_hash=hashlib.sha256(exe.read_bytes()).hexdigest()
evidence=ROOT/'artifacts/manager-v1/exe-smoke-result.json'
result=json.loads(evidence.read_text(encoding='utf-8-sig'))
if not (result.get('success') and result.get('frozen') and result.get('usb_disabled')
        and len(result.get('pages',[]))==6 and result.get('exe_sha256')==exe_hash):
    raise SystemExit('Test this exact frozen EXE before release: tools/test_manager.ps1 -Frozen')
shutil.copy2(evidence,PACKAGE/'exe-smoke-result.json')
with exe.open('rb') as f:
    if f.read(2)!=b'MZ':raise SystemExit('Not a Windows executable')
    f.seek(60);offset=struct.unpack('<I',f.read(4))[0];f.seek(offset)
    if f.read(4)!=b'PE\0\0' or struct.unpack('<H',f.read(2))[0]!=0x8664:raise SystemExit('EXE is not Windows x64')
for name in ('README.md','MANAGER_USAGE.md','MANAGER_ARCHITECTURE.md','MANAGER_REVIEW_CHATGPT.md','LICENSE','THIRD_PARTY_NOTICES.md'):
    source=ROOT/name
    if not source.is_file():raise SystemExit('Missing distribution document: '+name)
    shutil.copy2(source,PACKAGE/name)
shutil.copy2(ROOT/'firmware/README.md',PACKAGE/'FIRMWARE_README.md')
shutil.copy2(ROOT/'CHANGELOG_MANAGER.md',PACKAGE/'CHANGELOG_MANAGER.md')
for folder in ('prototype-p1','prototype-p2'):
    src=ROOT/'firmware/backups/manager-v1-20261030'/folder
    if not (src/'manifest.json').is_file():
        print('Optional recovery backup unavailable:',folder)
        continue
    dst=PACKAGE/'firmware'/folder;dst.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((src/'manifest.json').read_text());name='PicoAmiibo-RP2040-pico-empty.uf2'
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=manifest['files'][name]['sha256']:raise SystemExit('Firmware backup hash mismatch')
    shutil.copy2(src/name,dst/name);shutil.copy2(src/'manifest.json',dst/'manifest.json')
# Ship reviewable application/loader sources, not profiles, caches or dumps.
source_zip=PACKAGE/'sources-manager.zip'
import zipfile
with zipfile.ZipFile(source_zip,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for source in (ROOT/'manager').rglob('*.py'):
        if '__pycache__' not in source.parts:z.write(source,source.relative_to(ROOT))
    for name in ('manager_entry.py','tools/__init__.py','tools/load_amiibo.py','tools/uf2.py','manager/requirements.txt',
                 'tools/build_manager.ps1','tools/package_manager.py','tools/manager_assets.py','tools/build_totk_catalog.py',
                 'tools/manager_test_profile.py','tools/test_manager.ps1','LICENSE','THIRD_PARTY_NOTICES.md',
                 'README.md','MANAGER_USAGE.md','MANAGER_ARCHITECTURE.md','MANAGER_REVIEW_CHATGPT.md'):
        z.write(ROOT/name,name)
    for source in (ROOT/'manager/assets').glob('*'):z.write(source,source.relative_to(ROOT))
licenses=PACKAGE/'licenses';licenses.mkdir(exist_ok=True)
site=Path(sys.prefix)/'Lib/site-packages'
for dist in ('pyside6_essentials','pyside6_addons','shiboken6','pyserial'):
    for directory in site.glob(dist+'-*.dist-info'):
        for source in directory.rglob('*'):
            if source.is_file() and ('license' in str(source).lower() or 'copying' in source.name.lower()):
                destination=licenses/dist/source.relative_to(directory);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
for source in (ROOT/'docs/licenses').glob('*'):shutil.copy2(source,licenses/source.name)
for source in (ROOT/'artifacts/manager-v1/screenshots/release').glob('*.png'):
    destination=PACKAGE/'screenshots'/source.name;destination.parent.mkdir(exist_ok=True);shutil.copy2(source,destination)
files={str(p.relative_to(PACKAGE)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in PACKAGE.rglob('*') if p.is_file() and p.name!='distribution.json'}
if any(name.lower().endswith('.bin') for name in files):raise SystemExit('Unexpected .bin in public distribution')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
manifest={'app_version':VERSION,'platform':'Windows x64','source_commit':commit,'source_dirty':False,
    'python':sys.version,'exe_ui_smoke':'PASS: six views, USB disabled, artificial library',
    'console_validation':'Manager not yet hardware-qualified','files':files}
(PACKAGE/'distribution.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
output=ROOT/'artifacts/manager-v1';output.mkdir(parents=True,exist_ok=True)
archive=shutil.make_archive(str(output/f'PicoAmiibo-Manager-{VERSION}-windows-x64'),'zip',PACKAGE)
(output/'manifest.json').write_text(json.dumps({'exe_sha256':files[exe.name]['sha256'],'zip_sha256':hashlib.sha256(Path(archive).read_bytes()).hexdigest(),'archive_bytes':Path(archive).stat().st_size,'source_commit':commit,'hardware':'UNTESTED'},indent=2)+'\n')
print('Windows x64 portable package verified:',exe)
