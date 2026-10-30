import importlib.util
from pathlib import Path
import struct
import unittest

spec=importlib.util.spec_from_file_location("uf2",Path(__file__).resolve().parents[1]/"tools/uf2.py")
uf2=importlib.util.module_from_spec(spec); spec.loader.exec_module(uf2)

def synthetic():
    # Synthetic, unauthenticated fixture generated in memory; never flash this.
    d=bytearray((i*29+7)&255 for i in range(572))
    d[3]=0x88^d[0]^d[1]^d[2]; d[8]=d[4]^d[5]^d[6]^d[7]
    return bytes(d)

class UF2Tests(unittest.TestCase):
    def template(self): return uf2.pack(bytes(256)+uf2.EMPTY_SLOT+bytes(256))
    def test_empty(self): self.assertEqual(uf2.inspect(self.template())["loaded_bytes"],0)
    def test_round_trip_540_and_572(self):
        for n in (540,572):
            d=synthetic()[:n]; result=uf2.provision(self.template(),d)
            self.assertEqual(uf2.inspect(result)["loaded_bytes"],n)
            image=uf2.unpack(result); self.assertEqual(image[288:288+n],d)
            self.assertEqual(image[:256],uf2.unpack(self.template())[:256])
            self.assertEqual(image[864:],uf2.unpack(self.template())[864:])
    def test_reject_malformed_tag(self):
        for d in (b"",bytes(532),bytes(541),bytes(2048),synthetic()[:3]+b"\0"+synthetic()[4:]):
            with self.assertRaises(ValueError): uf2.provision(self.template(),d)
    def test_reject_reprovision(self):
        with self.assertRaises(ValueError): uf2.provision(uf2.provision(self.template(),synthetic()),synthetic())
    def test_reject_duplicate_slot(self):
        with self.assertRaises(ValueError): uf2.provision(uf2.pack(uf2.EMPTY_SLOT*2),synthetic())
    def test_reject_bad_uf2_headers(self):
        for offset,value in ((0,0),(8,0),(12,0x20000000),(16,257),(20,2),(24,999),(28,1),(508,0)):
            bad=bytearray(self.template()); struct.pack_into("<I",bad,offset,value)
            with self.assertRaises(ValueError): uf2.unpack(bad)
    def test_detect_tag_corruption(self):
        result=bytearray(uf2.provision(self.template(),synthetic()))
        result[512+32+100]^=1
        with self.assertRaises(ValueError): uf2.inspect(result)
    def test_reject_truncated_uf2(self):
        with self.assertRaises(ValueError): uf2.unpack(self.template()[:-1])

if __name__ == "__main__": unittest.main()
