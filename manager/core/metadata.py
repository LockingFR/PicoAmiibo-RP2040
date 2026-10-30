"""Optional public metadata; private binary files never leave the computer."""
import json
from pathlib import Path
import urllib.request

BUILTIN={
    "01000000034d0902":{"name":"Link · Twilight Princess","character":"Link","series":"Zelda","image":""},
    "0100000000040002":{"name":"Link · Super Smash Bros.","character":"Link","series":"Zelda","image":""},
}
CATALOG_URL="https://raw.githubusercontent.com/N3evin/AmiiboAPI/master/database/amiibo.json"

class Metadata:
    def __init__(self,cache):
        self.cache=Path(cache);self.path=self.cache/"catalog.json";self.entries=dict(BUILTIN)
        from .rewards import Rewards
        for p in Rewards().profiles:
            for identity in p['amiibo_ids']:
                self.entries.setdefault(identity,{'name':p['name'],'character':p['name'].split(' · ')[0],'series':'Zelda','image':''})
        try:
            cached=json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(cached,dict):
                self.entries.update({k:v for k,v in cached.items() if isinstance(v,dict) and all(isinstance(v.get(f,''),str) for f in ('name','character','series','image'))})
        except (OSError,ValueError):pass
    def get(self,tag):
        item=self.entries.get(tag["amiibo_id"],{})
        return {"name":item.get("name",tag["name"]),"character":item.get("character","Unidentified"),
            "series":item.get("series","Unidentified"),"image":item.get("image","")}
    def image_path(self,tag):
        p=self.cache/(tag["amiibo_id"]+".png")
        return p if p.is_file() else None
    def refresh(self):
        request=urllib.request.Request(CATALOG_URL,headers={"User-Agent":"PicoAmiiboManager/1.0"})
        with urllib.request.urlopen(request,timeout=15) as r:
            raw=r.read(6*1024*1024+1)
        if len(raw)>6*1024*1024:raise ValueError("Catalog too large")
        document=json.loads(raw);entries={}
        # AmiiboAPI's source database maps 0x + 16 hex ID to public metadata.
        for key,value in document.get("amiibos",{}).items():
            identity=key.removeprefix("0x").lower()
            if len(identity)!=16:continue
            head,tail=identity[:8],identity[8:]
            series_key="0x"+identity[:3]
            series=document.get("game_series",{}).get(series_key,"Unidentified")
            entries[identity]={"name":value.get("name","Amiibo"),"character":value.get("name","Amiibo"),
                "series":series,"image":f"https://raw.githubusercontent.com/N3evin/AmiiboAPI/master/images/icon_{head}-{tail}.png"}
        if not entries:raise ValueError("Unrecognized public catalog format")
        temporary=self.path.with_suffix(".tmp");temporary.write_text(json.dumps(entries),encoding="utf-8");temporary.replace(self.path)
        self.entries.update(entries)
        return len(entries)
    def fetch_image(self,tag):
        entry=self.get(tag);url=entry["image"]
        if not url.startswith("https://raw.githubusercontent.com/N3evin/AmiiboAPI/"):return None
        target=self.cache/(tag["amiibo_id"]+".png")
        if target.is_file():return target
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"PicoAmiiboManager/1.0"}),timeout=10) as r:data=r.read(2*1024*1024+1)
        if len(data)>2*1024*1024 or not data.startswith(b"\x89PNG\r\n\x1a\n"):raise ValueError("Invalid public image")
        target.write_bytes(data);return target
