"""Verify and package a clean-revision firmware build. No hardware access."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from uf2 import inspect,unpack,LIMIT,BASE

ROOT=Path(__file__).resolve().parents[1]

def command(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True).strip()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build",type=Path,default=ROOT/"build/pico")
    p.add_argument("--output",type=Path,default=ROOT/"artifacts/prototype-p0")
    p.add_argument("--toolchain",type=Path,default=Path("C:/devkitPro/devkitARM"))
    args=p.parse_args()
    git=Path("C:/Program Files/Git/cmd/git.exe")
    if not git.is_file():git=Path("git")
    if command(str(git),"status","--porcelain"):
        raise SystemExit("Refusing to package a dirty/untracked source tree")
    commit=command(str(git),"rev-parse","HEAD")
    binary=(args.build/"picoamiibo.bin").read_bytes()
    uf2=args.build/"PicoAmiibo-RP2040-pico-empty.uf2"
    info=inspect(uf2.read_bytes())
    if info["loaded_bytes"]!=0 or binary.count(b"PICOAMIIBO-V001!"+bytes(608-16))!=1:
        raise SystemExit("Firmware must contain exactly one EMPTY factory slot")
    if len(binary)>LIMIT-BASE or unpack(uf2.read_bytes())!=binary.ljust(info["image_bytes_padded"],b"\0"):
        raise SystemExit("UF2 differs from binary or overlaps reserved flash")
    version=re.search(r"project\(PicoAmiiboRP2040 VERSION ([0-9.]+)",(ROOT/"CMakeLists.txt").read_text()).group(1)
    if f"{version}-{commit[:12]}".encode() not in binary or b"+dirty" in binary:
        raise SystemExit("Firmware build identity does not match clean HEAD")
    nm=args.toolchain/"bin/arm-none-eabi-nm.exe"
    size=args.toolchain/"bin/arm-none-eabi-size.exe"
    symbols=command(str(nm),str(args.build/"picoamiibo.elf"))
    if re.search(r"\b(?:cyw43|btstack|bluepad32|hci_|ble_|malloc|calloc|realloc)[A-Za-z0-9_]*",symbols,re.I):
        raise SystemExit("Unexpected radio or dynamic allocation symbol in firmware")
    sizes=command(str(size),"-A",str(args.build/"picoamiibo.elf"))
    allocated_sram=0
    for line in sizes.splitlines():
        parts=line.split()
        if len(parts)==3 and parts[1].isdigit() and parts[2].isdigit():
            n,address=int(parts[1]),int(parts[2])
            if 0x20000000<=address<0x20042000:allocated_sram+=n
    if allocated_sram>264*1024:raise SystemExit("SRAM allocation exceeds Pico")
    previous_manifest=args.output/"manifest.json"
    if previous_manifest.is_file() and json.loads(previous_manifest.read_text())["source_commit"]!=commit:
        raise SystemExit("Use a new output directory; preserving the previous firmware delivery")
    args.output.mkdir(parents=True,exist_ok=True)
    files={}
    for source in (uf2,args.build/"picoamiibo.elf",args.build/"picoamiibo.bin",args.build/"picoamiibo.elf.map"):
        if source.is_file():
            shutil.copy2(source,args.output/source.name)
            files[source.name]={"bytes":source.stat().st_size,"sha256":hashlib.sha256(source.read_bytes()).hexdigest()}
    for name in ("LICENSE","THIRD_PARTY_NOTICES.md","USER_TEST.md","STATUS.md","HANDOFF.md"):
        shutil.copy2(ROOT/name,args.output/name)
    shutil.copytree(ROOT/"docs/licenses",args.output/"docs/licenses",dirs_exist_ok=True)
    for name in ("host-tests.log","build.log","artifact-smoke.log"):
        source=ROOT/"artifacts"/name
        if source.is_file():shutil.copy2(source,args.output/name)
    manifest={"source_commit":commit,"firmware_version":version,"board":"pico","platform":"rp2040",
        "pico_sdk":"2.2.0 a1438dff1d38bd9c65dbd693f0e5db4b9ae91779",
        "tinyusb":"86ad6e56c1700e85f1c5678607a762cfe3aa2f47",
        "compiler":command(str(args.toolchain/"bin/arm-none-eabi-gcc.exe"),"--version").splitlines()[0],
        "flash_firmware_bytes":len(binary),"sram_linked_including_heap_and_stack_reservations":allocated_sram,
        "reserved_tag_flash_bytes":8192,"source_tree":"clean","radio_symbols":"absent",
        "dynamic_allocation_symbols":"absent","console_hardware":"UNTESTED","files":files}
    (args.output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    (args.output/"sizes.txt").write_text(sizes+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))

if __name__=="__main__":main()
