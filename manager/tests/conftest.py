from pathlib import Path
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import pytest
from manager.core.library import Library

def make_tag(n=540,seed=7):
    data=bytearray((i*29+seed)&255 for i in range(n))
    data[3]=0x88^data[0]^data[1]^data[2];data[8]=data[4]^data[5]^data[6]^data[7]
    return bytes(data)

@pytest.fixture
def library(tmp_path):return Library(tmp_path/"profile")

@pytest.fixture
def tag():return make_tag()

@pytest.fixture(scope='session')
def qt():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])
