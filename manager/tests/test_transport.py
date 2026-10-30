import threading
import zlib
import pytest
from manager.transport.cdc import Transport,Cancelled,parse_info,friendly_error
from conftest import make_tag

class Model:
    def __init__(self,error=''):
        self.data=make_tag(seed=11);self.error=error;self.commands=[];self.writes=0
    def open(self,*args,**kwargs):return Port(self)

class Port:
    def __init__(self,model):self.m=model;self.rx=bytearray();self.tx=bytearray();self.expected=0
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def reset_input_buffer(self):self.rx.clear()
    def flush(self):pass
    def write(self,data):
        part=data[:11]
        if self.expected and self.m.error=='disconnect_write' and len(self.tx)>100:raise OSError('disconnected')
        self.tx+=part
        if self.expected:
            if len(self.tx)==self.expected:
                if self.m.error=='write_fail':self.rx+=b'ERR store\n'
                else:self.m.data=bytes(self.tx);self.rx+=b'OK\n'
                self.expected=0;self.tx.clear()
        elif b'\n' in self.tx:
            command=bytes(self.tx).strip();self.tx.clear();self.m.commands.append(command)
            if command==b'INFO':
                self.rx+=b'OTHER\n' if self.m.error=='wrong_peer' else f'PA1 loaded=1 size={len(self.m.data)} crc={zlib.crc32(self.m.data):08x} generation=1 presented=0\n'.encode()
            elif command.startswith(b'LOAD '):
                self.expected=int(command.split()[1]);self.m.writes+=1;self.rx+=b'READY\n'
            elif command==b'READ':
                if self.m.error=='disconnect_read':raise OSError('disconnected')
                self.rx+=f'DATA {len(self.m.data)} {zlib.crc32(self.m.data):08x}\n'.encode()
                data=bytearray(self.m.data)
                if self.m.error=='corrupt_read':data[-1]^=1
                self.rx+=data
            elif command==b'EXIT':self.rx+=b'BYE\n'
            elif command==b'CAPS':self.rx+=b'ERR command\n'
            else:raise AssertionError(command)
        return len(part)
    def read(self,n):
        result=bytes(self.rx[:min(n,7)]);del self.rx[:len(result)];return result

def test_measured_transfer_and_progress(tag):
    model=Model();events=[]
    r=Transport(model.open).upload('COM5',tag,lambda *x:events.append(x))
    assert r['verified'] and r['exit_ok'] and model.data==tag
    writes=[x for x in events if x[0]=='write'];reads=[x for x in events if x[0]=='readback']
    assert writes[-1][1:]==(540,540) and reads[-1][1:]==(540,540)
    assert events[-1][0]=='verified' and model.commands[-1]==b'EXIT'

def test_probe_is_read_only():
    model=Model();r=Transport(model.open).probe('COM5')
    assert r['readback_verified'] and model.writes==0 and b'EXIT' not in model.commands

@pytest.mark.parametrize('failure',['wrong_peer','write_fail','corrupt_read','disconnect_read','disconnect_write'])
def test_failure_never_returns_verified(tag,failure):
    model=Model(failure);old=model.data;events=[]
    with pytest.raises((ValueError,RuntimeError,OSError)):
        Transport(model.open).upload('COM5',tag,lambda *x:events.append(x))
    assert not any(x[0]=='verified' for x in events)
    if failure in ('wrong_peer','write_fail','disconnect_write'):assert model.data==old

def test_cancel_before_write(tag):
    cancel=threading.Event();cancel.set();model=Model()
    with pytest.raises(Cancelled):Transport(model.open).upload('COM5',tag,lambda *x:None,cancel)
    assert model.writes==0

def test_info_and_redacted_error():
    with pytest.raises(ValueError):parse_info('PA1 loaded=1 size=2048 crc=0 generation=1 presented=0')
    assert 'private-bytes' not in friendly_error(RuntimeError('private-bytes'))
