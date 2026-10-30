import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from manager.core.library import Library,describe
from manager.core.guide import instructions
from manager.transport.discovery import discover,version_from_serial
from conftest import make_tag

def test_import_duplicate_and_reopen(library,tag):
    a,created=library.import_data(tag,"My tag");assert created
    b,created=library.import_data(tag,"Other name");assert not created and a==b
    assert len(library.all())==1 and library.data(a['sha256'])==tag
    assert Library(library.root).get(a['sha256'])['name']=="My tag"

@pytest.mark.parametrize("size",[0,1,532,539,541,571,573,2048])
def test_wrong_sizes(library,size):
    with pytest.raises(ValueError):library.import_data(bytes(size),"Invalid")
    assert not library.all()

def test_bad_bcc(library,tag):
    data=bytearray(tag);data[3]^=1
    with pytest.raises(ValueError):library.import_data(data,"Corrupted")

def test_extended(library):
    data=make_tag(572);a,_=library.import_data(data,"Signature")
    assert a['size']==572 and library.data(a['sha256'])==data

def test_favorites_and_settings_persist(library,tag):
    a,_=library.import_data(tag,"A");library.favorite(a['sha256'],True)
    library.set_setting("online_metadata",False)
    other=Library(library.root)
    assert other.get(a['sha256'])['favorite']==1 and other.setting("online_metadata") is False

def test_changed_library_file_rejected(library,tag):
    a,_=library.import_data(tag,"A");(library.files/(a['sha256']+'.bin')).write_bytes(make_tag(seed=9))
    with pytest.raises(ValueError,match="changed"):library.data(a['sha256'])

def test_history_feedback_and_private_export(library,tag,tmp_path):
    r=library.record("Private name","COM5","0.1.1",540,describe(tag)['crc'],"verified","Identical readback")
    library.game_result(r,"recognized");assert library.history()[0]['game_result']=="recognized"
    p=tmp_path/'log.json';library.export_log(p,{"mode":"absent"})
    raw=p.read_bytes();d=json.loads(raw)
    assert b'Private nam' not in raw and tag not in raw and 'name' not in d['history'][0]

def test_discovery_never_promotes_retail_controller():
    d=discover([],['USB\\VID_057E&PID_2069\\00'])
    assert len(d)==1 and d[0].kind=='controller_candidate' and not d[0].version

def test_bootloader_and_multiple_cdc():
    ports=[SimpleNamespace(vid=0xcafe,pid=0x4013,device='COM'+str(i),serial_number='PicoAmiibo_0.1.2_hash',description='Config') for i in (5,6)]
    d=discover(ports,['USB\\VID_2E8A&PID_0003\\ABC'])
    assert [x.kind for x in d]==['cdc','cdc','bootloader'] and d[0].version=='0.1.2'

def test_absent():assert discover([],[])==[]

def test_unknown_version_guide_does_not_guess_A():
    assert not version_from_serial('00')
    assert not any('quickly tap BOOTSEL twice' in s for s in instructions(''))
    assert 'do not assume' in ' '.join(instructions(''))

def test_version_guides_are_distinct():
    assert 'L+R' in ' '.join(instructions('0.1.0'))
    assert 'On 0.1.1 only' in ' '.join(instructions('0.1.1'))
    assert 'L+R' not in ' '.join(instructions('0.1.2'))
