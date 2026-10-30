from manager.core.rewards import Rewards,searchable
from manager.core.metadata import Metadata
from manager.app.rewards import RewardsDialog

def test_epona_is_attributed_only_to_two_link_figures():
    r=Rewards()
    assert {p['key'] for p in r.profiles if p['special']}=={'4','845'}
    assert {p['key'] for p in r.profiles if 'epona' in searchable(r.text(p))}=={'4','845'}
    assert r.for_id('01000000034d0902')['key']=='845'
    assert not r.for_id('0100000003540902')['special']

def test_wolf_link_has_fabric_but_no_companion_promise():
    p=Rewards().for_id('01030000024f0902')
    assert any(i['name']=='Mirror of Twilight Fabric' for t in p['tables'] for i in t['items'])
    assert 'does not summon' in p['notes'][0]

def test_catalog_coverage_and_unknown_identity():
    r=Rewards();ids=[i for p in r.profiles for i in p['amiibo_ids']]
    assert len(r.profiles)==36 and len(ids)==33 and len(set(ids))==33
    assert r.for_id('0000000000000000')['key']=='default'
    assert r.for_id('010d000004a70902')['key']=='mineru'
    assert r.by_key['1189']['amiibo_ids']==['010b000004a50902']
    for p in r.profiles:
        assert p['tables'] and all(t['items'] for t in p['tables'])
        assert all(s in r.document['sources'] for s in p['sources'])
        html=r.html(p)
        assert 'not per-scan' in html and 'The PC cannot' in html
    assert 'Complete Great Sky Island' in r.html(r.by_key['845'])

def test_metadata_offline_and_invalid_cache(library):
    (library.cache/'catalog.json').write_text('["corrupted"]',encoding='utf-8')
    m=Metadata(library.cache)
    assert 'Tulin' in m.get({'amiibo_id':'010b000004a50902','name':'unnamed'})['name']

def test_rewards_dialog_search_and_empty_results(qt):
    dialog=RewardsDialog(Rewards(),'01000000034d0902');dialog.show()
    assert dialog.combo.currentData()=='845'
    dialog.search.setText('epona');assert dialog.combo.count()==2
    assert 'Epona' in dialog.browser.toPlainText()
    dialog.search.setText('no-such-reward');assert dialog.combo.count()==0
    assert 'No entries' in dialog.browser.toPlainText();dialog.close()
