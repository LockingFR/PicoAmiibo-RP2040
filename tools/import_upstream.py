"""Import only the reusable Apache-2.0 code from the exact requested revision."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REV = "cdb5bf6f85cef9998c11da280073a0c7642b712c"
ROOT = Path(__file__).resolve().parents[1]

def main():
    upstream = Path(sys.argv[1]).resolve()
    rev = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
    if rev != REV:
        raise SystemExit(f"Expected PicoSwitch2 v2.5.0 commit {REV}, got {rev}")
    modules = {
        "virtual_amiibo": "src/nfc",
        "ns2_virtual_nfc": "src/nfc",
        "ns2_virtual_nfc_runtime": "src/nfc",
        "ns2_vendor_rx": "src/switch_pro2",
        "ns2_vendor_tx": "src/switch_pro2",
        "ns2_pairing_crypto": "src",
        "ns2_firmware_profile": "src",
    }
    manifest = {}
    def copy(src, dst):
        # Read the committed blob; do not import accidental worktree modifications.
        data = subprocess.check_output(["git", "-C", str(upstream), "show", f"{REV}:{src}"])
        target = ROOT / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest[dst] = {"upstream_path": src, "sha256": hashlib.sha256(data).hexdigest()}
    for name, directory in modules.items():
        copy(f"{directory}/{name}.c", f"src/vendor/{name}.c")
        copy(f"include/{name}.h", f"include/{name}.h")
        copy(f"tools/test_{name}.c", f"tests/upstream/test_{name}.c")
    copy("LICENSE", "LICENSE")
    copy("pico_sdk_import.cmake", "pico_sdk_import.cmake")
    (ROOT / "docs/upstream-files.json").write_text(json.dumps({"repository": "https://github.com/notsosaelin/PicoSwitch2", "tag": "v2.5.0", "commit": REV, "files": manifest}, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(manifest)} files, without Bluetooth, captures or tag dumps")

if __name__ == "__main__":
    main()
