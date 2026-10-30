"""Rebuild the offline factual catalogue from pinned public tables (no tag data).

Usage: python tools/build_totk_catalog.py path/to/amiibo-drop-tables.txt path/to/amiibo.json
The two inputs are public text/metadata, never amiibo .bin files.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
GIST='https://gist.github.com/jordanbtucker/a950e3a041b95867bc123b71c4cf7f28'
REVISION='4dd8cd25ce09ed1fdf9403614ea7c68ab812e81e'
WIKI='https://zeldawiki.wiki/w/index.php?title=Amiibo_in_Tears_of_the_Kingdom&oldid=1386889'
TAGMO='https://github.com/HiddenRamblings/TagMo/blob/d4e8246c9f087db70f2ad159a831f851127f033c/app/src/main/res/raw/amiibo.json'
ALIASES={'ToonLink':22,'Sheik':23,'Link':'generic-link','Zelda':'generic-zelda',
    'Ganon':27,'WolfLink':591,'Darukel':856,'Reval':859,'Mifar':858,'Uruboza':857,
    'Guardian':853,'Bokoblin':860}
NAMES={4:'Link · Super Smash Bros.',14:'Zelda · Super Smash Bros.',22:'Toon Link · Super Smash Bros.',
    23:'Sheik',27:'Ganondorf · Super Smash Bros.',591:'Wolf Link',843:'Link · Ocarina of Time',
    844:"Link · Majora’s Mask",845:'Link · Twilight Princess',846:'Link · Skyward Sword',847:'8-Bit Link',
    848:'Toon Link · The Wind Waker',850:'Toon Zelda · The Wind Waker',851:'Link Archer · BOTW',
    852:'Link Rider · BOTW',853:'Guardian · BOTW',854:'Zelda · BOTW',856:'Daruk',857:'Urbosa',
    858:'Mipha',859:'Revali',860:'Bokoblin',892:'Young Link · Super Smash Bros.',921:"Link · Link’s Awakening",
    1044:'Zelda and Loftwing',1048:'Link · TOTK',1049:'Zelda · TOTK',1050:'Ganondorf · TOTK',
    1187:'Riju · TOTK',1188:'Sidon · TOTK',1189:'Tulin · TOTK',1190:'Yunobo · TOTK',
    'mineru':'Mineru Construct · TOTK','generic-link':'Generic Link · internal table',
    'generic-zelda':'Generic Zelda · internal table','default':'Other amiibo · generic rewards'}
HIGHLIGHTS={4:'Epona · Twilight armor · Mirror of Twilight Fabric',845:'Epona · Twilight armor · Mirror of Twilight Fabric',
    591:'Meat · Mirror of Twilight Fabric (no wolf companion)',843:'Time armor · Biggoron Sword · Lon Lon Ranch Fabric',
    892:'Time armor · Biggoron Sword · Lon Lon Ranch Fabric',844:'Fierce Deity armor and sword · Majora Mask Fabric',
    846:'Sky armor · White Sword of the Sky · Sword-Spirit Fabric',847:'Hero armor and sword · Pixel Fabric',
    848:'Wind armor · Sea-Breeze Boomerang · King of Red Lions Fabric',22:'Wind armor · Sea-Breeze Boomerang · King of Red Lions Fabric',
    921:'Awakening armor · Egg Fabric',851:'Bows · Ancient Blade · Tunic of Memories Fabric',
    852:'Mushrooms · swords · Hylian-Hood Fabric',853:'Ancient Blade · Ancient Sheikah Fabric',
    854:'Gems · Hyrule-Princess Fabric',14:'Dusk Bow · Princess of Twilight Fabric',
    23:'Sheik Mask · Sheik Fabric',27:'Dusk Claymore · Demon King Fabric',
    850:'Hero Shield · Bygone-Royal Fabric',1044:'Goddess Fabric · gems',
    1048:'Champion Leathers Fabric · mushrooms',1049:'Princess Zelda Fabric · plants and gems',
    1050:'Gerudo-King Fabric · Gloom Sword',856:'Vah Rudania Divine Helm · Goron-Champion Fabric',
    857:'Vah Naboris Divine Helm · Gerudo-Champion Fabric',858:'Vah Ruta Divine Helm · Zora-Champion Fabric',859:'Vah Medoh Divine Helm · Rito-Champion Fabric',
    860:'Bokoblin Fabric · Boko equipment',1187:'Sage of Lightning Fabric · Gerudo equipment',
    1188:'Sage of Water Fabric · Zora spears',1189:'Sage of Wind Fabric · bows and arrows',
    1190:'Sage of Fire Fabric · Goron weapons','mineru':'Sage of Spirit Fabric · Zonaite and Construct bows',
    'generic-link':'Fish · Soldier and Knight weapons','generic-zelda':'Plants · gems',
    'default':'Materials and food · no exclusive Zelda rewards'}

def main():
    raw=Path(sys.argv[1]).read_bytes();text=raw.decode('utf-8')
    source=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    products={int(k.removeprefix('0x')[8:12],16):k.removeprefix('0x') for k in source['amiibos']}
    profiles=[]
    sections=re.split(r'^----- (.*?) -----\s*$',text,flags=re.M)
    for title,body in zip(sections[1::2],sections[2::2]):
        number=re.search(r'NumberingID_(\d+)',title)
        key=int(number[1]) if number else ALIASES[re.search(r'\((.*?)\)',title)[1] if '(' in title else title]
        tables=[];table=None
        for line in body.splitlines():
            heading=re.fullmatch(r'(Normal|SmallHit|BigHit|GreatHit) - x([\d-]+)',line.strip())
            item=re.fullmatch(r'\s*(\d+)% - (.*?)(?: - Requirement: (.*))?',line)
            if heading:
                table={'kind':heading[1],'count':heading[2],'items':[]};tables.append(table)
            elif item:
                if table is None:raise ValueError('Item outside a table')
                table['items'].append({'name':item[2],'weight':int(item[1]),'requires':item[3] or ''})
            elif line.strip():raise ValueError('Unparsed table line: '+line)
        profiles.append({'key':str(key),'name':NAMES[key],'amiibo_ids':[products[key]] if isinstance(key,int) else [],
            'highlight':HIGHLIGHTS[key],'tables':tables,'sources':['datamine'],'notes':[],'special':[]})
    bykey={p['key']:p for p in profiles}
    for key in ('4','845'):
        bykey[key]['special']=['Epona: a special first-scan case in a location where horses can appear. Later scans do not guarantee another horse. The Manager cannot read game progress or scan history.']
        bykey[key]['sources'].append('wiki')
    bykey['591']['notes']=['In TOTK, Wolf Link provides meat and a fabric; it does not summon the wolf companion from BOTW.']
    for key in ('generic-link','generic-zelda'):
        bykey[key]['notes']=['Documented internal table; no released figure is automatically assigned to this profile.']
    # New sages share their predecessor's ordinary pools, with their own fabric.
    for key,base,fabric in ((1189,859,'Sage of Wind Fabric'),(1187,857,'Sage of Lightning Fabric'),
                            (1188,858,'Sage of Water Fabric'),(1190,856,'Sage of Fire Fabric')):
        tables=copy.deepcopy(bykey[str(base)]['tables'])
        tables[-1]['items']=[{'name':fabric,'weight':100,'requires':''}]
        profiles.append({'key':str(key),'name':NAMES[key],'amiibo_ids':[products[key]],'highlight':HIGHLIGHTS[key],
            'tables':tables,'sources':['wiki'],'special':[],'notes':['Requires a game version supporting the new sages (1.4.0 or later).']})
    def table(kind,count,items):
        return {'kind':kind,'count':count,'items':[{'name':name,'weight':weight,'requires':condition} for name,weight,condition in items]}
    profiles.append({'key':'mineru','name':NAMES['mineru'],'amiibo_ids':['010d000004a70902'],'highlight':HIGHLIGHTS['mineru'],
        'sources':['wiki','tagmo'],'special':[],'notes':['A compatible game version is required. The public figure ID is cross-checked against the pinned TagMo catalog.'],
        'tables':[table('Normal','4',[('Iron Box',100,'')]),table('SmallHit','3-5',[('Zonaite',100,'')]),
            table('BigHit','1',[('Construct Bow',40,''),('Strong Construct Bow',40,'Complete Great Sky Island'),('Zonaite Bow',20,'Visit Depths')]),
            table('GreatHit','1',[('Sage of Spirit Fabric',100,'')])]})
    normal=[('Raw Meat',5),('Hyrule Herb',10),('Cool Safflina',5),('Warm Safflina',5),('Electric Safflina',5),('Mighty Thistle',5),('Armoranth',5),('Blue Nightshade',5),('Apple',10),('Acorn',10),('Hylian Shroom',5),('Chillshroom',5),('Sunshroom',5),('Zapshroom',5),('Silent Shroom',5),('Endura Shroom',5),('Razorshroom',5),('Ironshroom',5)]
    profiles.append({'key':'default','name':NAMES['default'],'amiibo_ids':[],'highlight':HIGHLIGHTS['default'],
        'sources':['wiki'],'special':[],'notes':['Documented fallback for other amiibo; an unlisted identifier does not confirm authenticity or an exclusive reward.'],
        'tables':[table('Normal','3-5',[(name,w,'') for name,w in normal]),table('SmallHit','1',[('Raw Prime Meat',5,''),('Hearty Truffle',5,''),('Raw Meat',90,'')]),table('BigHit','1',[('Raw Prime Meat (no chest)',100,'')])]})
    document={'schema':1,'game':'Tears of the Kingdom','reviewed':'2026-10-30',
        'sources':{'datamine':{'title':'JordanBTucker · datamined drop tables','url':GIST+'/'+REVISION,'revision':REVISION,'input_sha256':hashlib.sha256(raw).hexdigest()},
        'wiki':{'title':'Zelda Wiki · TOTK amiibo drop tables','url':WIKI},
        'tagmo':{'title':'TagMo · public figure identifiers','url':TAGMO},
        'nintendo':{'title':'Nintendo · using amiibo in TOTK','url':'https://en-americas-support.nintendo.com/app/answers/detail/a_id/61937/p/988/c/950'}},
        'profiles':sorted(profiles,key=lambda p:p['name'].casefold())}
    target=ROOT/'manager/assets/rewards_totk.json';target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(profiles)} profiles, {sum(len(p["amiibo_ids"]) for p in profiles)} automatic identities')

if __name__=='__main__':main()
