from pathlib import Path
import sys
import unittest
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import load_amiibo as loader

class Port:
    def __init__(self,corrupt=False,bad_peer=False):
        self.incoming=bytearray();self.outgoing=bytearray();self.stored=b""
        self.expected=0;self.crc=0;self.commands=[];self.corrupt=corrupt;self.bad_peer=bad_peer
    def flush(self): pass
    def write(self,data):
        part=data[:7];self.incoming+=part
        if self.expected:
            if len(self.incoming)>=self.expected:
                self.stored=bytes(self.incoming[:self.expected]);del self.incoming[:self.expected];self.expected=0
                self.outgoing+=b"OK\n" if zlib.crc32(self.stored)==self.crc else b"ERR crc\n"
        elif b"\n" in self.incoming:
            line,_,rest=self.incoming.partition(b"\n");self.incoming=bytearray(rest);self.commands.append(bytes(line))
            if line==b"INFO": self.outgoing+=b"OTHER\n" if self.bad_peer else b"PA1 loaded=1\n"
            elif line.startswith(b"LOAD "):
                _,n,crc=line.split();self.expected=int(n);self.crc=int(crc,16);self.outgoing+=b"READY\n"
            elif line==b"READ":
                self.outgoing+=f"DATA {len(self.stored)} {zlib.crc32(self.stored):08x}\n".encode()
                data=bytearray(self.stored)
                if self.corrupt:data[-1]^=1
                self.outgoing+=data
            else:raise AssertionError(line)
        return len(part)
    def read(self,n):
        result=bytes(self.outgoing[:min(n,3)]);del self.outgoing[:len(result)];return result

def fixture(n):
    data=bytearray((i*29+7)&255 for i in range(n));data[3]=0x88^data[0]^data[1]^data[2];data[8]=data[4]^data[5]^data[6]^data[7]
    return bytes(data)

class LoaderTests(unittest.TestCase):
    def test_both_sizes_and_short_transfers(self):
        for n in (540,572):
            p=Port();data=fixture(n);self.assertTrue(loader.upload(p,data).startswith("PA1"));self.assertEqual(p.stored,data)
    def test_readback_corruption_is_failure(self):
        with self.assertRaisesRegex(RuntimeError,"Stored bytes differ"):loader.upload(Port(corrupt=True),fixture(572))
    def test_peer_checked_before_tag_transmission(self):
        p=Port(bad_peer=True)
        with self.assertRaisesRegex(RuntimeError,"not a PicoAmiibo"):loader.upload(p,fixture(540))
        self.assertEqual(p.commands,[b"INFO"]);self.assertEqual(p.stored,b"")
    def test_invalid_file_never_opens_protocol(self):
        p=Port()
        with self.assertRaises(ValueError):loader.upload(p,b"bad")
        self.assertEqual(p.commands,[])
    def test_timeout(self):
        with self.assertRaisesRegex(RuntimeError,"timed out"):loader.read_exact(Port(),1,timeout=0)

if __name__=="__main__":unittest.main()
