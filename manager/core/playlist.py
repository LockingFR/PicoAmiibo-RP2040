"""Bounded wire representation shared with the experimental playlist firmware."""
import struct
import zlib
from tools.uf2 import MAGIC,SLOT_SIZE,validate_tag

MAX_SLOTS=64
def encode_playlist(images):
    if not 1<=len(images)<=MAX_SLOTS:raise ValueError('Select between 1 and 64 amiibo.')
    slots=[]
    for image in images:
        data=bytes(image);validate_tag(data)
        slot=MAGIC+struct.pack('<II',len(data),zlib.crc32(data))+bytes(8)+data
        slots.append(slot.ljust(SLOT_SIZE,b'\0'))
    return b''.join(slots)
