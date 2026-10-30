"""Read-only Windows USB enumeration. VID/PID alone is not a Pico identity."""
import ctypes
from ctypes import wintypes
from dataclasses import dataclass,asdict
import os
import re
from serial.tools import list_ports

@dataclass(frozen=True)
class Device:
    kind:str
    port:str=""
    serial:str=""
    version:str=""
    description:str=""
    def to_dict(self):return asdict(self)

def version_from_serial(serial):
    match=re.search(r"PicoAmiibo[ _](\d+\.\d+\.\d+)[ _]",serial or "",re.I)
    return match.group(1) if match else ""

def usb_instances():
    if os.name!="nt":return []
    class GUID(ctypes.Structure):
        _fields_=[("a",wintypes.DWORD),("b",wintypes.WORD),("c",wintypes.WORD),("d",ctypes.c_ubyte*8)]
    class Info(ctypes.Structure):
        _fields_=[("cbSize",wintypes.DWORD),("ClassGuid",GUID),("DevInst",wintypes.DWORD),("Reserved",ctypes.c_size_t)]
    api=ctypes.WinDLL("setupapi",use_last_error=True)
    api.SetupDiGetClassDevsW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR,wintypes.HWND,wintypes.DWORD]
    api.SetupDiGetClassDevsW.restype=wintypes.HANDLE
    api.SetupDiEnumDeviceInfo.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.POINTER(Info)]
    api.SetupDiGetDeviceInstanceIdW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Info),wintypes.LPWSTR,wintypes.DWORD,ctypes.c_void_p]
    api.SetupDiDestroyDeviceInfoList.argtypes=[wintypes.HANDLE]
    handle=api.SetupDiGetClassDevsW(None,None,None,6)
    if handle==ctypes.c_void_p(-1).value:raise OSError("Windows USB enumeration is unavailable")
    results=[]
    try:
        for index in range(8192):
            info=Info();info.cbSize=ctypes.sizeof(Info)
            if not api.SetupDiEnumDeviceInfo(handle,index,ctypes.byref(info)):
                if ctypes.get_last_error()!=259:raise OSError("Windows USB enumeration was interrupted")
                break
            buffer=ctypes.create_unicode_buffer(1024)
            if api.SetupDiGetDeviceInstanceIdW(handle,ctypes.byref(info),buffer,len(buffer),None):
                value=buffer.value.upper()
                if value.startswith("USB\\VID_") and "&MI_" not in value:results.append(value)
    finally:api.SetupDiDestroyDeviceInfoList(handle)
    return results

def discover(ports=None,instances=None):
    devices=[]
    for p in (list_ports.comports() if ports is None else ports):
        if p.vid==0xcafe and p.pid==0x4013:
            sn=p.serial_number or ""
            devices.append(Device("cdc",p.device,sn,version_from_serial(sn),p.description or "PicoAmiibo Config"))
    for identity in (usb_instances() if instances is None else instances):
        if identity.startswith("USB\\VID_2E8A&PID_0003\\"):
            devices.append(Device("bootloader",description="RPI-RP2 · BOOTSEL"))
        elif identity.startswith("USB\\VID_057E&PID_2069\\"):
            devices.append(Device("controller_candidate",description="Pro Controller 2 · Pico identity not confirmed"))
    return devices
