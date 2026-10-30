import struct
import threading
import zlib
import pytest
from conftest import make_tag
from test_transport import Model
from manager.core.playlist import encode_playlist
from manager.transport.cdc import Transport,Cancelled

class PlaylistModel:
    def __init__(self,error='',maximum=64):
        self.images=[make_tag(seed=11)];self.commands=[];self.error=error;self.maximum=maximum;self.writes=0
    def open(self,*args,**kwargs):return PlaylistPort(self)

class PlaylistPort:
    def __init__(self,model):self.m=model;self.tx=bytearray();self.rx=bytearray();self.expected=0;self.count=0
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def reset_input_buffer(self):self.rx.clear()
    def flush(self):pass
    def write(self,data):
        chunk=data[:37];self.tx+=chunk
        if self.expected:
            if len(self.tx)==self.expected:
                if self.m.error=='write_fail':self.rx+=b'ERR store\n'
                else:
                    self.m.images=[]
                    if not self.count:self.m.images=[bytes(self.tx)]
                    else:
                        for i in range(self.count):
                            slot=self.tx[i*608:(i+1)*608];n=struct.unpack_from('<I',slot,16)[0]
                            self.m.images.append(bytes(slot[32:32+n]))
                    self.rx+=b'OK\n'
                self.expected=0;self.tx.clear()
        elif b'\n' in self.tx:
            command=bytes(self.tx).strip();self.tx.clear();self.m.commands.append(command)
            first=self.m.images[0]
            if command==b'INFO':
                count=len(self.m.images)+(1 if self.m.error=='wrong_count' and self.m.writes else 0)
                self.rx+=f'PA1 loaded=1 size={len(first)} crc={zlib.crc32(first):08x} generation=2 presented=0 protocol=2 max_slots=64 slots={count} index=0\n'.encode()
            elif command==b'CAPS':
                self.rx+=f'PA2 protocol=2 max_slots={self.m.maximum} slot_size=608 count={len(self.m.images)} index=0\n'.encode()
            elif command.startswith(b'BATCH '):
                _,count,n,crc=command.split();self.expected=int(n);self.count=int(count);self.m.writes+=1;self.rx+=b'READY\n'
            elif command.startswith(b'LOAD '):
                self.expected=int(command.split()[1]);self.count=0;self.m.writes+=1;self.rx+=b'READY\n'
            elif command==b'READ' or command.startswith(b'READ '):
                index=0 if command==b'READ' else int(command.split()[1])
                if index==1 and self.m.error=='disconnect_later':raise OSError('disconnected')
                image=self.m.images[index];self.rx+=f'DATA {len(image)} {zlib.crc32(image):08x}\n'.encode()
                outgoing=bytearray(image)
                if index==1 and self.m.error=='corrupt_later':outgoing[-1]^=1
                self.rx+=outgoing
            elif command==b'EXIT':self.rx+=b'BYE\n'
            else:raise AssertionError(command)
        return len(chunk)
    def read(self,n):
        data=bytes(self.rx[:min(n,19)]);del self.rx[:len(data)];return data

def test_whole_playlist_readback_and_order():
    images=[make_tag(seed=1),make_tag(572,seed=2),make_tag(seed=3)]
    model=PlaylistModel();events=[]
    result=Transport(model.open).upload_playlist('COM5',images,lambda *x:events.append(x))
    assert model.images==images and result['verified'] and result['slot_count']==3 and result['slot_index']==0
    assert result['exit_ok'] and model.commands[-1]==b'EXIT'
    assert [c for c in model.commands if c.startswith(b'READ ')]==[b'READ 0',b'READ 1',b'READ 2']
    assert [e for e in events if e[0]=='write'][-1][1:]==(3*608,3*608)
    assert events[-1]==('verified',sum(map(len,images)),sum(map(len,images)))

@pytest.mark.parametrize('error',['write_fail','corrupt_later','disconnect_later','wrong_count'])
def test_later_failure_never_claims_verified(error):
    model=PlaylistModel(error);events=[]
    with pytest.raises((RuntimeError,ValueError,OSError)):
        Transport(model.open).upload_playlist('COM5',[make_tag(seed=1),make_tag(seed=2)],lambda *x:events.append(x))
    assert not any(e[0]=='verified' for e in events)

def test_legacy_rejects_batch_before_private_data():
    model=Model()
    with pytest.raises(RuntimeError,match='does not support playlists'):
        Transport(model.open).upload_playlist('COM5',[make_tag(seed=1),make_tag(seed=2)],lambda *x:None)
    assert model.writes==0 and not any(c.startswith(b'BATCH') for c in model.commands)

def test_capacity_checked_before_upload():
    model=PlaylistModel(maximum=1)
    with pytest.raises(ValueError,match='capacity'):
        Transport(model.open).upload_playlist('COM5',[make_tag(seed=1),make_tag(seed=2)],lambda *x:None)
    assert model.writes==0

def test_cancel_during_later_readback():
    model=PlaylistModel();cancel=threading.Event();events=[]
    def progress(*event):
        events.append(event)
        if event[0]=='readback' and event[1]>540:cancel.set()
    with pytest.raises(Cancelled):
        Transport(model.open).upload_playlist('COM5',[make_tag(seed=1),make_tag(seed=2)],progress,cancel)
    assert len(model.images)==2 and not any(e[0]=='verified' for e in events)

def test_bounds_and_embedded_slot_integrity():
    with pytest.raises(ValueError):encode_playlist([])
    with pytest.raises(ValueError):encode_playlist([make_tag()]*65)
    images=[make_tag(seed=1),make_tag(572,seed=2)]
    packed=encode_playlist(images)
    assert len(packed)==1216
    for i,data in enumerate(images):
        slot=packed[i*608:(i+1)*608];n,crc=struct.unpack_from('<II',slot,16)
        assert n==len(data) and crc==zlib.crc32(data) and slot[32:32+n]==data
