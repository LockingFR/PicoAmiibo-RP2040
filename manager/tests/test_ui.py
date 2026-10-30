import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import time
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QMessageBox
from manager.app.window import MainWindow
from manager.transport.cdc import Transport
from manager.transport.discovery import Device
from conftest import make_tag
from test_transport import Model

@pytest.fixture
def window(qt,library):
    w=MainWindow(library,no_usb=True,test_mode=True);w.show();QTest.qWait(30)
    yield w
    deadline=time.monotonic()+5
    while w._tasks and time.monotonic()<deadline:QTest.qWait(10)
    w.close();QTest.qWait(10)

def wait(w):
    deadline=time.monotonic()+5
    while w._tasks and time.monotonic()<deadline:QTest.qWait(20)
    assert not w._tasks

def test_absent_never_enables_transfer(window):
    assert not window.load_button.isEnabled()
    assert 'not detected' in window.home_device.text()
    for i in range(5):window.page(i);assert window.pages.currentIndex()==i

def test_import_search_favorite_and_selection(window,tmp_path):
    a=tmp_path/'Synthetic test.bin';a.write_bytes(make_tag())
    window.import_paths([str(a)]);assert len(window._cards)==1 and window.selected
    window.search.setText('introuvable');assert not window._cards
    window.search.clear();window.favorite_tag(window.selected,True);window.favorites.setChecked(True)
    assert len(window._cards)==1 and window.library.get(window.selected)['favorite']

def test_controller_is_not_identified_as_pico(window):
    window.scanned([Device('controller_candidate')]);assert window.device is None
    assert 'unidentified' in window.home_device.text() and not window.load_button.isEnabled()

def test_multiple_cdc_requires_selection(window):
    window.scanned([Device('cdc','COM5'),Device('cdc','COM6')])
    assert window.device is None and not window.load_button.isEnabled()
    assert 'Multiple' in window.home_device.text()

def test_simulated_ui_transfer_and_game_feedback(window,tmp_path):
    model=Model();window.transport=Transport(model.open)
    p=tmp_path/'Synthetic test.bin';p.write_bytes(make_tag());window.import_paths([str(p)])
    window.scanned([Device('cdc','COM5','PicoAmiibo_0.1.2_hash','0.1.2')]);wait(window)
    assert window.probe and window.load_button.isEnabled()
    QTest.mouseClick(window.load_button,Qt.MouseButton.LeftButton);wait(window)
    assert 'Saved and verified' in window.phase_label.text()
    assert window.guide_button.isEnabled() and window.library.history()[0]['status']=='verified'
    window.page(3);QTest.mouseClick(window.game_ok,Qt.MouseButton.LeftButton)
    assert window.library.history()[0]['game_result']=='recognized'

def test_failed_transfer_blocks_guide(window,tmp_path):
    model=Model('corrupt_read');window.transport=Transport(model.open)
    p=tmp_path/'Synthetic test.bin';p.write_bytes(make_tag());window.import_paths([str(p)])
    window.devices=[Device('cdc','COM5','','0.1.2')];window.device=window.devices[0]
    window.start_upload();wait(window)
    assert not window.guide_button.isEnabled() and window._last_record is None
    assert window.library.history()[0]['status']=='failed'

def test_bootloader_requires_firmware_not_tag(window):
    window.scanned([Device('bootloader')]);assert 'BOOTSEL' in window.home_device.text()
    assert not window.load_button.isEnabled()

def test_library_search_by_reward(window):
    data=bytearray(make_tag());data[0x54:0x5c]=bytes.fromhex('01000000034d0902')
    window.library.import_data(bytes(data),'Artificial test Link');window.refresh_library()
    window.search.setText('epona');assert len(window._cards)==1
    window.search.setText('Loftwing');assert not window._cards
