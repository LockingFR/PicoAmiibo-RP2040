from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from manager.app.window import MainWindow
from manager.transport.cdc import Transport
from manager.transport.discovery import Device
from manager.i18n import set_language,t
from conftest import make_tag
from test_ui import wait
from test_playlist import PlaylistModel

def populate(library):
    for seed in (1,2,3):library.import_data(make_tag(seed=seed),'Artificial '+str(seed))

def test_checkbox_does_not_navigate_but_card_does(qt,library):
    populate(library);w=MainWindow(library,no_usb=True,test_mode=True);w.show();w.page(1)
    card=w._cards[0]
    QTest.mouseClick(card.check,Qt.MouseButton.LeftButton)
    assert w.pages.currentIndex()==1 and len(w.checked)==1
    QTest.mouseClick(card,Qt.MouseButton.LeftButton,pos=card.rect().center())
    assert w.pages.currentIndex()==2 and w.selected==card.tag['sha256'] and not w.is_playlist()
    w.close()

def test_language_hot_switch_persists_checked_and_selected(qt,library):
    populate(library);w=MainWindow(library,no_usb=True,test_mode=True);w.show();w.page(1)
    w.check_shown();before=w.checked[:];selected=w.selected
    w.language_combo.setCurrentIndex(w.language_combo.findData('fr'))
    assert w.checked==before and w.selected==selected
    assert w.heading.text()=='Bibliothèque' and 'Charger' in w.batch_button.text()
    assert library.setting('language')=='fr'
    w.close();w=MainWindow(library,no_usb=True,test_mode=True)
    assert w.language_combo.currentData()=='fr' and w.checked==before
    w.language_combo.setCurrentIndex(w.language_combo.findData('en'))
    assert w.heading.text()=='Home';w.close();set_language('en')

def test_legacy_multiselection_blocked_single_still_works(qt,library):
    populate(library);w=MainWindow(library,no_usb=True,test_mode=True);w.show();w.check_shown();w.open_playlist()
    w.device=Device('cdc','COM5','','0.1.1');w.probe={'loaded':1,'size':540,'crc':'00000000','generation':1,'presented':0}
    w._update_device_ui();assert not w.load_button.isEnabled() and '0.2.0' in w.transfer_hint.text()
    w.open_tag(w.tags[0]['sha256']);assert w.load_button.isEnabled() and not w.is_playlist()
    w.close()

def test_checked_playlist_upload_then_replace_with_one(qt,library):
    populate(library);model=PlaylistModel();w=MainWindow(library,Transport(model.open),no_usb=True,test_mode=True)
    w.show();w.check_shown();w.open_playlist()
    w.scanned([Device('cdc','COM5','PicoAmiibo_0.2.0_hash','0.2.0')]);wait(w)
    assert w.load_button.isEnabled(), (w.probe,w._error_message,model.commands)
    QTest.mouseClick(w.load_button,Qt.MouseButton.LeftButton);wait(w)
    assert len(model.images)==3 and library.history()[0]['status']=='verified'
    assert 'Playlist saved' in w.phase_label.text()
    w.open_tag(w.tags[1]['sha256']);assert not w.is_playlist()
    assert w.load_button.isEnabled()
    QTest.mouseClick(w.load_button,Qt.MouseButton.LeftButton);wait(w)
    assert len(model.images)==1 and model.images[0]==library.data(w.tags[1]['sha256'])
    assert library.history()[0]['status']=='verified';w.close()
