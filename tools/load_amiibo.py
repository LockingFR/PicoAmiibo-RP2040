"""Load one local amiibo through an explicitly selected PicoAmiibo Config COM port.

Does not install firmware. No device auto-selection, network or saved tag copies.
"""
import argparse
from pathlib import Path
import sys
import time
import zlib
try:
    from .uf2 import validate_tag
except ImportError:  # Direct CLI execution, kept compatible with the original tool.
    from uf2 import validate_tag

ROOT=Path(__file__).resolve().parents[1]

def write_all(port,data,on_progress=None):
    offset=0
    while offset<len(data):
        n=port.write(data[offset:])
        if not n: raise RuntimeError("Serial write made no progress")
        offset+=n
        if on_progress: on_progress(offset,len(data))
    port.flush()

def read_exact(port,size,timeout=8,on_progress=None):
    result=bytearray();deadline=time.monotonic()+timeout
    while len(result)<size:
        chunk=port.read(size-len(result))
        if chunk:
            result.extend(chunk)
            if on_progress: on_progress(len(result),size)
        elif time.monotonic()>deadline: raise RuntimeError("Serial read timed out")
    return bytes(result)

def line(port,timeout=8):
    result=bytearray();deadline=time.monotonic()+timeout
    while len(result)<256:
        remaining=deadline-time.monotonic()
        if remaining<=0:raise RuntimeError("Serial read timed out")
        byte=read_exact(port,1,timeout=remaining)
        if byte==b"\n": return result.decode("ascii").rstrip("\r")
        result+=byte
    raise RuntimeError("Oversized device response")

def info(port):
    write_all(port,b"INFO\n");response=line(port)
    if not response.startswith("PA1 "): raise RuntimeError("Selected port is not a PicoAmiibo Config device")
    return response

def upload(port,data,progress=None):
    def emit(stage,done=0,total=0):
        if progress: progress(stage,done,total)
    validate_tag(data)
    emit("identify")
    info(port) # Check the peer before sending any user data.
    write_all(port,f"LOAD {len(data)} {zlib.crc32(data):08x}\n".encode("ascii"))
    ready=line(port)
    if ready!="READY": raise RuntimeError(f"Device refused upload: {ready}")
    emit("write",0,len(data))
    write_all(port,data,lambda done,total:emit("write",done,total))
    emit("commit")
    response=line(port)
    if response!="OK": raise RuntimeError(f"Device did not commit upload: {response}")
    emit("committed",len(data),len(data))
    # Destination reread, not just transfer/ACK success.
    write_all(port,b"READ\n");header=line(port).split()
    if len(header)!=3 or header[0]!="DATA": raise RuntimeError("Device did not return stored data")
    try: n=int(header[1]);crc=int(header[2],16)
    except ValueError as error: raise RuntimeError("Invalid readback header") from error
    if n!=len(data) or crc!=zlib.crc32(data): raise RuntimeError("Stored size/CRC differs from input")
    emit("readback",0,n)
    actual=read_exact(port,n,on_progress=lambda done,total:emit("readback",done,total))
    if actual!=data: raise RuntimeError("Stored bytes differ from input")
    emit("compare",n,n)
    result=info(port)
    emit("verified",n,n)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",required=True,help="Explicit COM port shown for PicoAmiibo Config")
    parser.add_argument("--info",action="store_true")
    parser.add_argument("--stay-config",action="store_true")
    parser.add_argument("amiibo",type=Path,nargs="?")
    args=parser.parse_args()
    if not args.info and not args.amiibo: parser.error("Provide a local 540/572-byte dump or --info")
    try:
        data=args.amiibo.read_bytes() if args.amiibo else None
        if data is not None: validate_tag(data)
        sys.path.insert(0,str(ROOT/".deps/python"))
        import serial
        with serial.Serial(args.port,115200,timeout=0.25,write_timeout=8) as port:
            port.reset_input_buffer()
            if data is not None:
                status=upload(port,data)
                print(f"Flash commit and destination byte-for-byte reread verified ({len(data)} bytes).")
            else: status=info(port)
            print(status)
            if not args.stay_config:
                write_all(port,b"EXIT\n")
                if line(port)!="BYE": raise RuntimeError("Device did not acknowledge mode change")
                print("Returning to controller mode. Tag remains ejected until a short BOOTSEL press.")
    except ImportError:
        parser.exit(2,"Missing pyserial 3.5. Run tools/setup.ps1 first.\n")
    except (OSError,RuntimeError,ValueError) as error:
        parser.exit(2,f"Error: {error}\n")

if __name__=="__main__": main()
