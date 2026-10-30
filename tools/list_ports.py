"""List matching configuration ports without opening or selecting a device."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/".deps/python"))
try:
    from serial.tools import list_ports
except ImportError:
    raise SystemExit("Run tools/setup.ps1 to install local pyserial 3.5")
ports=[p for p in list_ports.comports() if p.vid==0xcafe and p.pid==0x4013]
for p in ports:
    print(f"{p.device}: {p.description} [CAFE:4013]")
if not ports:
    print("No PicoAmiibo Config port found. Hold BOOTSEL 2 seconds after the Pico has booted.")
