"""Offline reference information only. Never reads game state or controls loot."""
from html import escape
import json
from pathlib import Path
import unicodedata

def searchable(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if not unicodedata.combining(c))

class Rewards:
    def __init__(self):
        self.document=json.loads((Path(__file__).resolve().parents[1]/'assets/rewards_totk.json').read_text(encoding='utf-8'))
        self.profiles=self.document['profiles']
        self.by_key={p['key']:p for p in self.profiles}
        self.by_id={identity:p for p in self.profiles for identity in p['amiibo_ids']}
    def for_id(self,identity):return self.by_id.get(identity.lower(),self.by_key['default'])
    def text(self,profile):
        return ' '.join([profile['name'],profile['highlight'],*profile['special'],
            *(i['name'] for t in profile['tables'] for i in t['items'])])
    def html(self,profile):
        e=escape
        lines=[f'<h1>{e(profile["name"])}</h1>',f'<p style="color:#77ead4">{e(profile["highlight"])}</p>',
            '<p>Possible rewards, not guaranteed drops. Results depend on game progress, previously obtained items, and game version. Normally, each amiibo can be used once per day. The PC cannot see the loot received on the console.</p>']
        for note in profile['special']+profile['notes']:lines.append('<p><b>'+e(note)+'</b></p>')
        lines.append('<p>Detailed item pools. ✨ = pristine weapon. Numbers are <b>relative weights within a table</b>, not per-scan drop chances.</p>')
        titles={'Normal':'Common materials','SmallHit':'Bonus materials','BigHit':'Common drop pool','GreatHit':'Rare drop pool'}
        conditions={'Complete Great Sky Island':'Complete Great Sky Island', 'Visit Depths':'Visit the Depths'}
        for table in profile['tables']:
            lines.append(f'<h2>{titles[table["kind"]]} · quantity {e(table["count"])}</h2><ul>')
            for item in table['items']:
                condition=item['requires'];suffix=' · '+conditions.get(condition,condition) if condition else ''
                lines.append(f'<li>{e(item["name"])} <span style="color:#a1b2be">· weight {item["weight"]}{e(suffix)}</span></li>')
            lines.append('</ul>')
        lines.append('<h2>Sources and limitations</h2><p>Offline reference · reviewed on '+self.document['reviewed']+'. Sources are available online. These entries do not represent hardware tests of every figure.</p>')
        for key in dict.fromkeys(profile['sources']+['nintendo']):
            source=self.document['sources'][key];lines.append(f'<p><a style="color:#77ead4" href="{e(source["url"],quote=True)}">{e(source["title"])}</a></p>')
        return ''.join(lines)
