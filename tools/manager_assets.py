"""Create an original Windows icon from the application's own vector drawing."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import struct
from PySide6.QtCore import QBuffer,QIODevice
from PySide6.QtWidgets import QApplication
from manager.app.widgets import artwork

app=QApplication([])
image=artwork('Zelda',256)
buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG');data=bytes(buffer.data())
target=Path(__file__).resolve().parents[1]/'manager/assets/icon.ico'
target.write_bytes(struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',0,0,0,0,1,32,len(data),22)+data)
