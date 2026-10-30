"""Adapter around the existing loader; no new firmware commands."""
from contextlib import contextmanager
from dataclasses import dataclass
import threading
import zlib
import serial
from tools import load_amiibo as loader
from manager.core.library import describe

class Cancelled(RuntimeError):pass

class CheckedPort:
    def __init__(self,port,cancel):self.port=port;self.cancel=cancel
    def check(self):
        if self.cancel.is_set():raise Cancelled("Operation cancelled")
    def read(self,n):self.check();return self.port.read(n)
    def write(self,data):self.check();return self.port.write(data)
    def flush(self):self.check();return self.port.flush()

def parse_info(line):
    if not line.startswith("PA1 "):raise ValueError("The port does not respond to the PicoAmiibo protocol.")
    parts=dict(field.split("=",1) for field in line.split()[1:] if "=" in field)
    result={}
    for key in ("loaded","size","generation","presented"):
        result[key]=int(parts[key])
    result["crc"]=f"{int(parts['crc'],16):08x}"
    if result["loaded"] not in (0,1) or result["presented"] not in (0,1):raise ValueError("Inconsistent Pico state")
    if result["loaded"] and result["size"] not in (540,572):raise ValueError("Unsupported reported size")
    return result

class Transport:
    def __init__(self,opener=None):self.opener=opener or serial.Serial
    @contextmanager
    def connection(self,port,cancel):
        with self.opener(port,115200,timeout=0.25,write_timeout=8) as raw:
            raw.reset_input_buffer()
            yield CheckedPort(raw,cancel or threading.Event())
    def probe(self,port,cancel=None):
        with self.connection(port,cancel) as p:
            status=parse_info(loader.info(p))
            if status["loaded"]:
                loader.write_all(p,b"READ\n");header=loader.line(p).split()
                if len(header)!=3 or header[0]!="DATA":raise ValueError("Pico readback is unavailable")
                size=int(header[1]);crc=int(header[2],16)
                if size not in (540,572) or size!=status["size"]:raise ValueError("Inconsistent readback size")
                data=loader.read_exact(p,size)
                if zlib.crc32(data)!=crc or f"{crc:08x}"!=status["crc"]:raise ValueError("Inconsistent readback CRC")
                status.update(describe(data))
                status["readback_verified"]=True
            return status
    def upload(self,port,data,progress,cancel=None):
        # Existing loader validates the input before issuing LOAD.
        describe(data)
        with self.connection(port,cancel) as p:
            status=parse_info(loader.upload(p,data,progress))
            if status["loaded"]!=1 or status["size"]!=len(data) or status["crc"]!=f"{zlib.crc32(data):08x}":
                raise ValueError("The final state does not match the verified data")
            status.update(describe(data));status["readback_verified"]=True
            status["verified"]=True;status["exit_ok"]=False
            # A failed mode change does not erase a measured successful readback.
            try:
                loader.write_all(p,b"EXIT\n");status["exit_ok"]=loader.line(p)=="BYE"
            except (OSError,RuntimeError,ValueError):pass
            return status

def friendly_error(error):
    if isinstance(error,Cancelled):return "Operation cancelled. Reconnect the Pico to check its contents before trying again."
    text=str(error)
    if "Stored bytes differ" in text or "CRC" in text or "crc" in text:
        return "Data comparison failed. The load is not verified; reconnect the Pico and retry using the original file."
    if "not a PicoAmiibo" in text or "protocol" in text:return "This port did not confirm its PicoAmiibo identity. No load has been verified."
    if "refused" in text or "commit" in text:return "The Pico did not confirm the save. Read the tag state again before continuing."
    if isinstance(error,(serial.SerialException,OSError)):
        return "The USB port is disconnected, busy, or inaccessible. Reconnect the Pico and close other tools using this port."
    if "timed out" in text:return "The Pico did not respond in time. Hold BOOTSEL for two seconds to enter configuration, then retry."
    return "The operation was not verified. Check the connection and file format, then retry."
