"""Private local library. No Qt, networking or device I/O."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import zlib
from manager import __version__
from tools.uf2 import validate_tag

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

def describe(data):
    validate_tag(data)
    return {"sha256":hashlib.sha256(data).hexdigest(),"size":len(data),
            "crc":f"{zlib.crc32(data):08x}","amiibo_id":data[0x54:0x5c].hex()}

class Library:
    def __init__(self, root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.files=self.root/"library";self.files.mkdir(exist_ok=True)
        self.cache=self.root/"cache";self.cache.mkdir(exist_ok=True)
        self.database=self.root/"manager.sqlite3"
        with self.db() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS tags(
              sha256 TEXT PRIMARY KEY, name TEXT NOT NULL, amiibo_id TEXT NOT NULL,
              size INTEGER NOT NULL, crc TEXT NOT NULL, favorite INTEGER NOT NULL DEFAULT 0,
              imported_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS history(
              id INTEGER PRIMARY KEY, date TEXT NOT NULL, name TEXT NOT NULL,
              port TEXT NOT NULL, firmware TEXT, size INTEGER, crc TEXT,
              status TEXT NOT NULL, message TEXT NOT NULL, game_result TEXT);
            ''')
    @contextmanager
    def db(self):
        c=sqlite3.connect(self.database,timeout=5);c.row_factory=sqlite3.Row
        try:
            yield c;c.commit()
        finally:c.close()
    def import_file(self,path):
        path=Path(path)
        if path.stat().st_size not in (540,572):raise ValueError("The file must contain 540 or 572 bytes.")
        return self.import_data(path.read_bytes(),path.stem)
    def import_data(self,data,name):
        meta=describe(data)
        with self.db() as c:
            existing=c.execute("SELECT * FROM tags WHERE sha256=?",(meta["sha256"],)).fetchone()
            if existing:return dict(existing),False
            target=self.files/(meta["sha256"]+".bin")
            temporary=target.with_suffix(".tmp")
            temporary.write_bytes(data);os.replace(temporary,target)
            c.execute("INSERT INTO tags(sha256,name,amiibo_id,size,crc,imported_at) VALUES(?,?,?,?,?,?)",
                (meta["sha256"],str(name)[:160] or "Unidentified amiibo",meta["amiibo_id"],meta["size"],meta["crc"],now()))
        return self.get(meta["sha256"]),True
    def get(self,sha):
        with self.db() as c:
            row=c.execute("SELECT * FROM tags WHERE sha256=?",(sha,)).fetchone()
            return dict(row) if row else None
    def all(self):
        with self.db() as c:return [dict(r) for r in c.execute("SELECT * FROM tags ORDER BY favorite DESC,name COLLATE NOCASE")]
    def data(self,sha):
        tag=self.get(sha)
        if not tag:raise ValueError("This amiibo is no longer in the library.")
        data=(self.files/(sha+".bin")).read_bytes()
        if describe(data)["sha256"]!=sha:raise ValueError("The local file has changed or is corrupted. Import the original again.")
        return data
    def favorite(self,sha,enabled):
        with self.db() as c:c.execute("UPDATE tags SET favorite=? WHERE sha256=?",(int(enabled),sha))
    def setting(self,key,default=None):
        with self.db() as c:row=c.execute("SELECT value FROM settings WHERE key=?",(key,)).fetchone()
        return json.loads(row[0]) if row else default
    def set_setting(self,key,value):
        with self.db() as c:c.execute("INSERT OR REPLACE INTO settings VALUES(?,?)",(key,json.dumps(value)))
    def record(self,name,port,firmware,size,crc,status,message):
        with self.db() as c:
            cursor=c.execute("INSERT INTO history(date,name,port,firmware,size,crc,status,message) VALUES(?,?,?,?,?,?,?,?)",
                (now(),name,port,firmware,size,crc,status,message))
            return cursor.lastrowid
    def history(self):
        with self.db() as c:return [dict(r) for r in c.execute("SELECT * FROM history ORDER BY id DESC LIMIT 200")]
    def game_result(self,record_id,result):
        if result not in ("recognized","failed"):raise ValueError("Unknown result")
        with self.db() as c:c.execute("UPDATE history SET game_result=? WHERE id=?",(result,record_id))
    def export_log(self,path,device):
        # No dumps, UID, paths to source files, SQL database or raw serial data.
        history=[{k:v for k,v in r.items() if k not in ("name",)} for r in self.history()]
        Path(path).write_text(json.dumps({"application":f"PicoAmiibo Manager {__version__}",
            "device":device,"history":history},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
