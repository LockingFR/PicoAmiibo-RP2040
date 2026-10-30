"""Create a clearly artificial GUI profile below this project's build directory."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from manager.core.library import Library
from manager.core.metadata import Metadata

def main():
    parser=argparse.ArgumentParser();parser.add_argument('profile',type=Path);parser.add_argument('--public-metadata',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];profile=args.profile.resolve()
    if not profile.is_relative_to(root/'build'):raise SystemExit('Test profile must stay inside this project/build')
    library=Library(profile)
    for seed,identity in enumerate(('01000000034d0902','0100000004180902','01030000024f0902')):
        data=bytearray((i*29+seed)&255 for i in range(540))
        data[3]=0x88^data[0]^data[1]^data[2];data[8]=data[4]^data[5]^data[6]^data[7]
        data[0x54:0x5c]=bytes.fromhex(identity)
        tag,_=library.import_data(bytes(data),'ARTIFICIAL TEST '+str(seed+1))
        if seed==0:library.favorite(tag['sha256'],True);library.set_setting('selected',tag['sha256'])
    if args.public_metadata:
        metadata=Metadata(library.cache);print('Public entries:',metadata.refresh())
        for tag in library.all():print('Public image cached:',bool(metadata.fetch_image(tag)))
    print('Artificial test profile:',profile)

if __name__=='__main__':main()
