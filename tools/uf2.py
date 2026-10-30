"""Standard-library-only Windows preloader for one user-owned 540/572-byte tag.

Never flashes hardware. Never downloads/generates amiibo data or keys.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

MAGIC = b"PICOAMIIBO-V001!"
SLOT_SIZE = 608
EMPTY_SLOT = MAGIC + bytes(SLOT_SIZE - len(MAGIC))
FAMILY = 0xE48BFF56
BASE = 0x10000000
LIMIT = BASE + 2 * 1024 * 1024 - 8192 - 2 * 65536  # preserve playlist and legacy stores
HEADER = (0x0A324655, 0x9E5D5157)

def pack(binary):
    if not 256 <= len(binary) <= LIMIT - BASE:
        raise ValueError("Binary does not fit the original Pico's 2 MiB flash")
    n = (len(binary) + 255) // 256
    blocks = []
    for i in range(n):
        payload = binary[256*i:256*(i+1)].ljust(256, b"\0")
        blocks.append(struct.pack("<8I", *HEADER, 0x2000, BASE+256*i, 256, i, n, FAMILY)
                      + payload + bytes(220) + struct.pack("<I", 0x0AB16F30))
    return b"".join(blocks)

def unpack(uf2):
    if not uf2 or len(uf2) % 512:
        raise ValueError("UF2 must contain complete 512-byte blocks")
    blocks = {}
    n = len(uf2)//512
    for i in range(n):
        block = uf2[i*512:(i+1)*512]
        a,b,flags,address,size,number,total,family = struct.unpack_from("<8I", block)
        if ((a,b) != HEADER or flags != 0x2000 or family != FAMILY or size != 256
            or total != n or number != i or address != BASE+256*i
            or struct.unpack_from("<I",block,508)[0] != 0x0AB16F30):
            raise ValueError(f"Invalid/unsupported RP2040 UF2 block {i}")
        if address+size > LIMIT:
            raise ValueError("UF2 exceeds Pico flash")
        blocks[address] = block[32:32+size]
    return b"".join(blocks[k] for k in sorted(blocks))

def validate_tag(data):
    if len(data) not in (540,572):
        raise ValueError("Expected an original encrypted NTAG215 dump of 540 or 572 bytes")
    if data[3] != 0x88 ^ data[0] ^ data[1] ^ data[2] or data[8] != data[4] ^ data[5] ^ data[6] ^ data[7]:
        raise ValueError("Invalid UID/BCC; input is not a raw NTAG215 image")
    # BCC is only a structural check. No cryptographic authenticity is asserted.

def provision(template, data):
    validate_tag(data)
    image = unpack(template)
    if image.count(EMPTY_SLOT) != 1:
        raise ValueError("Expected one empty PicoAmiibo slot; use the original empty template")
    offset = image.index(EMPTY_SLOT)
    slot = MAGIC + struct.pack("<II",len(data),zlib.crc32(data)) + bytes(8) + data
    slot = slot.ljust(SLOT_SIZE,b"\0")
    patched = image[:offset] + slot + image[offset+SLOT_SIZE:]
    result = pack(patched)
    if unpack(result)[offset:offset+SLOT_SIZE] != slot:
        raise ValueError("UF2 personalization readback failed")
    return result

def inspect(uf2):
    image=unpack(uf2)
    positions=[i for i in range(len(image)) if image.startswith(MAGIC,i) and i+SLOT_SIZE <= len(image)]
    candidates=[]
    for offset in positions:
        n,crc=struct.unpack_from("<II",image,offset+16)
        if n in (0,540,572):
            candidates.append((offset,n,crc))
    # The comparison literal in the firmware may also contain the magic; the
    # actual slot is identified by its size/header and reserved zero bytes.
    candidates=[(o,n,c) for o,n,c in candidates if image[o+24:o+32] == bytes(8)]
    if len(candidates) != 1:
        raise ValueError("Cannot identify a unique preload slot")
    offset,n,crc=candidates[0]
    if n:
        data=image[offset+32:offset+32+n]
        validate_tag(data)
        if zlib.crc32(data) != crc:
            raise ValueError("Preload CRC mismatch")
    return {"family":"RP2040", "board":"pico", "uf2_blocks":len(uf2)//512,
            "image_bytes_padded":len(image), "loaded_bytes":n,
            "tag_check":"structural only; console authentication untested" if n else "empty",
            "sha256":hashlib.sha256(uf2).hexdigest()}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("pack"); p.add_argument("binary",type=Path); p.add_argument("output",type=Path); p.add_argument("--replace-build-output",action="store_true")
    p=sub.add_parser("preload"); p.add_argument("template",type=Path); p.add_argument("amiibo",type=Path); p.add_argument("output",type=Path)
    p=sub.add_parser("inspect"); p.add_argument("uf2",type=Path)
    args=parser.parse_args()
    try:
        if args.command == "inspect":
            print(json.dumps(inspect(args.uf2.read_bytes()),indent=2)); return
        if args.command == "pack":
            if args.output.suffix.lower() != ".uf2" or args.output.resolve() == args.binary.resolve():
                raise ValueError("Pack output must be a separate .uf2 file")
            result=pack(args.binary.read_bytes())
        else:
            if args.output.suffix.lower() != ".uf2":
                raise ValueError("Output must have a .uf2 extension")
            if args.output.resolve() in (args.template.resolve(),args.amiibo.resolve()):
                raise ValueError("Output must differ from both inputs")
            result=provision(args.template.read_bytes(),args.amiibo.read_bytes())
        args.output.parent.mkdir(parents=True,exist_ok=True)
        # Never overwrite an existing artifact, source dump or template.
        mode="wb" if args.command == "pack" and args.replace_build_output else "xb"
        with args.output.open(mode) as target:
            target.write(result)
        print(json.dumps(inspect(result),indent=2))
    except (ValueError,OSError) as error:
        parser.exit(2,f"Error: {error}\n")

if __name__ == "__main__":
    main()
