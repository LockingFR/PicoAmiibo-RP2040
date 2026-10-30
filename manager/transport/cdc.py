"""Legacy single-tag loader plus explicitly negotiated playlist support."""
from contextlib import contextmanager
from dataclasses import dataclass
import threading
import zlib
import serial
from tools import load_amiibo as loader
from manager.core.library import describe
from manager.core.playlist import encode_playlist,MAX_SLOTS

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
    protocol=int(parts.get('protocol','1'));maximum=int(parts.get('max_slots','1'))
    count=int(parts.get('slots',str(result['loaded'])));index=int(parts.get('index','0'))
    if protocol not in (1,2) or not 1<=maximum<=MAX_SLOTS or not 0<=count<=maximum or not 0<=index<max(1,count):
        raise ValueError('Inconsistent playlist state')
    result.update(supports_playlist=protocol==2,max_slots=maximum,slot_count=count,slot_index=index)
    return result

def parse_caps(line):
    if not line.startswith('PA2 '):raise RuntimeError('This firmware does not support playlists. No tag data was sent.')
    parts=dict(field.split('=',1) for field in line.split()[1:] if '=' in field)
    values={key:int(parts[key]) for key in ('protocol','max_slots','slot_size','count','index')}
    if values['protocol']!=2 or values['slot_size']!=608 or not 1<=values['max_slots']<=MAX_SLOTS:
        raise ValueError('Unsupported playlist capability')
    if not 0<=values['count']<=values['max_slots'] or not 0<=values['index']<max(1,values['count']):
        raise ValueError('Inconsistent playlist capability')
    return values

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
    def upload_playlist(self,port,images,progress,cancel=None):
        # Build/validate every input before opening a device.
        images=[bytes(data) for data in images];payload=encode_playlist(images)
        if len(images)==1:return self.upload(port,images[0],progress,cancel)
        with self.connection(port,cancel) as p:
            progress('identify',0,0);parse_info(loader.info(p))
            progress('capability',0,0);loader.write_all(p,b'CAPS\n');caps=parse_caps(loader.line(p))
            if len(images)>caps['max_slots']:raise ValueError('The selected playlist exceeds device capacity.')
            crc=zlib.crc32(payload)
            loader.write_all(p,f'BATCH {len(images)} {len(payload)} {crc:08x}\n'.encode('ascii'))
            if loader.line(p)!='READY':raise RuntimeError('Device refused playlist upload')
            progress('write',0,len(payload))
            loader.write_all(p,payload,lambda done,total:progress('write',done,total))
            progress('commit',0,0)
            if loader.line(p,timeout=30)!='OK':raise RuntimeError('Device did not commit playlist')
            progress('committed',len(payload),len(payload))
            total=sum(map(len,images));completed=0;progress('readback',0,total)
            for index,data in enumerate(images):
                loader.write_all(p,f'READ {index}\n'.encode('ascii'));header=loader.line(p).split()
                if len(header)!=3 or header[0]!='DATA':raise ValueError('Playlist readback unavailable')
                n=int(header[1]);expected_crc=int(header[2],16)
                if n!=len(data) or expected_crc!=zlib.crc32(data):raise ValueError('Playlist size/CRC mismatch')
                actual=loader.read_exact(p,n,on_progress=lambda done,_,base=completed:progress('readback',base+done,total))
                if actual!=data:raise ValueError('Stored bytes differ from playlist input')
                completed+=n
            progress('compare',total,total)
            status=parse_info(loader.info(p))
            if not status['supports_playlist'] or not status['loaded'] or status['slot_count']!=len(images) or status['slot_index']!=0:
                raise ValueError('Final playlist state differs from the verified input')
            if status['size']!=len(images[0]) or status['crc']!=f'{zlib.crc32(images[0]):08x}':
                raise ValueError('First playlist tag CRC differs')
            status.update(describe(images[0]));status.update(verified=True,readback_verified=True,exit_ok=False)
            progress('verified',total,total)
            try:
                loader.write_all(p,b'EXIT\n');status['exit_ok']=loader.line(p)=='BYE'
            except (OSError,RuntimeError,ValueError):pass
            return status

def friendly_error(error):
    if isinstance(error,Cancelled):return "Operation cancelled. Reconnect the Pico to check its contents before trying again."
    text=str(error)
    if 'does not support playlists' in text:return 'This firmware does not support playlists. No tag data was sent.'
    if 'capacity' in text:return 'Maximum 64 tags; reduce the checked selection.'
    if "Stored bytes differ" in text or "CRC" in text or "crc" in text:
        return "Data comparison failed. The load is not verified; reconnect the Pico and retry using the original file."
    if "not a PicoAmiibo" in text or "protocol" in text:return "This port did not confirm its PicoAmiibo identity. No load has been verified."
    if "refused" in text or "commit" in text:return "The Pico did not confirm the save. Read the tag state again before continuing."
    if isinstance(error,(serial.SerialException,OSError)):
        return "The USB port is disconnected, busy, or inaccessible. Reconnect the Pico and close other tools using this port."
    if "timed out" in text:return "The Pico did not respond in time. Hold BOOTSEL for two seconds to enter configuration, then retry."
    return "The operation was not verified. Check the connection and file format, then retry."
