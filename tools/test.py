"""Rebuild and run the declared host tests; does not touch any device."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
OUT=ROOT/"build/host-tests"
OUT.mkdir(parents=True,exist_ok=True)
VENDOR=list((ROOT/"src/vendor").glob("*.c"))
TESTS=sorted((ROOT/"tests/upstream").glob("test_*.c"))+sorted((ROOT/"tests").glob("test_*.c"))
cc=os.environ.get("CC","gcc")
for test in TESTS:
    exe=OUT/(test.stem + (".exe" if os.name == "nt" else ""))
    cmd=[cc,"-std=c11","-Wall","-Wextra","-Werror","-g","-O1","-Iinclude"]
    if os.name != "nt":
        cmd += ["-fsanitize=address,undefined","-fno-omit-frame-pointer","-fno-pie","-no-pie"]
    cmd += [str(test),"src/device.c","src/identity.c","src/store.c","src/playlist.c","src/cycle.c","src/config.c","src/input.c",*map(str,VENDOR),"-o",str(exe)]
    subprocess.run(cmd,check=True)
    subprocess.run([str(exe)],check=True)
suite=unittest.defaultTestLoader.discover("tests",pattern="test_*.py")
result=unittest.TextTestRunner(verbosity=2,stream=sys.stdout).run(suite)
if not result.wasSuccessful(): sys.exit(1)
print(f"PASS: {len(TESTS)} rebuilt C executables; {result.testsRun} Python tests. Host evidence only.")
