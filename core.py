"""Qualified snapshot differences; a partial read is not a membership loss."""
import hashlib
import json
import sqlite3

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)

def assemble(pages):
    if not isinstance(pages,list) or not pages:raise ValueError('missing snapshot pages')
    by_cursor={};sid=None;sequence=None
    for p in pages:
        if not isinstance(p,dict):raise ValueError('page must be an object')
        if not isinstance(p.get('snapshot_id'),str) or not p['snapshot_id']:raise ValueError('snapshot identity required')
        seq=p.get('sequence')
        if isinstance(seq,bool) or not isinstance(seq,int) or seq<1:raise ValueError('positive integer sequence required')
        if sid is None:sid,sequence=p['snapshot_id'],seq
        if (p['snapshot_id'],seq)!=(sid,sequence):raise ValueError('mixed snapshot versions')
        cursor=p.get('cursor');nxt=p.get('next_cursor')
        if not isinstance(cursor,str) or not cursor or (nxt is not None and (not isinstance(nxt,str) or not nxt)):raise ValueError('invalid cursor')
        if not isinstance(p.get('terminal'),bool):raise ValueError('terminal evidence required')
        if p['terminal']!=(nxt is None):raise ValueError('terminal flag and next cursor disagree')
        if not isinstance(p.get('members'),list) or not all(isinstance(m,str) and m for m in p['members']):raise ValueError('invalid member keys')
        if cursor in by_cursor and canonical(by_cursor[cursor])!=canonical(p):raise ValueError('conflicting duplicate page')
        by_cursor[cursor]=p
    cursor='start';visited=set();members=set()
    while cursor is not None:
        if cursor in visited:raise ValueError('cursor cycle')
        if cursor not in by_cursor:raise ValueError('incomplete page chain')
        visited.add(cursor);p=by_cursor[cursor]
        if len(set(p['members']))!=len(p['members']) or members.intersection(p['members']):raise ValueError('duplicate members across pages')
        members.update(p['members']);cursor=p['next_cursor']
    if visited!=set(by_cursor):raise ValueError('unreachable extra page')
    digest=hashlib.sha256(canonical({'sequence':sequence,'members':sorted(members)}).encode()).hexdigest()
    return sid,sequence,members,digest

class Monitor:
    def __init__(self,path):
        self.db=sqlite3.connect(str(path),timeout=10,isolation_level=None)
        self.db.executescript('CREATE TABLE IF NOT EXISTS heads(stream TEXT PRIMARY KEY,sid TEXT,seq INTEGER,members TEXT);'
                              'CREATE TABLE IF NOT EXISTS snapshots(stream TEXT,sid TEXT,seq INTEGER,digest TEXT,PRIMARY KEY(stream,sid));'
                              'CREATE TABLE IF NOT EXISTS events(stream TEXT,sid TEXT,action TEXT,member TEXT,PRIMARY KEY(stream,sid,action,member));')
    def close(self):self.db.close()
    def state(self,stream):
        row=self.db.execute('SELECT members FROM heads WHERE stream=?',(stream,)).fetchone()
        return set(json.loads(row[0])) if row else None
    def admit(self,stream,pages,fail_before_commit=False):
        if not isinstance(stream,str) or not stream:raise ValueError('stream required')
        sid,seq,members,digest=assemble(pages)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            prior=self.db.execute('SELECT digest FROM snapshots WHERE stream=? AND sid=?',(stream,sid)).fetchone()
            if prior:
                if prior[0]!=digest:raise ValueError('snapshot id reused with different content')
                self.db.execute('COMMIT');return {'status':'duplicate','events':[]}
            head=self.db.execute('SELECT seq,members FROM heads WHERE stream=?',(stream,)).fetchone()
            if head and seq<=head[0]:raise ValueError('snapshot sequence did not advance')
            previous=set(json.loads(head[1])) if head else members
            events=[{'action':'gain','member':m} for m in sorted(members-previous)]
            events += [{'action':'loss','member':m} for m in sorted(previous-members)]
            self.db.execute('INSERT INTO snapshots VALUES(?,?,?,?)',(stream,sid,seq,digest))
            self.db.execute('INSERT OR REPLACE INTO heads VALUES(?,?,?,?)',(stream,sid,seq,canonical(sorted(members))))
            self.db.executemany('INSERT INTO events VALUES(?,?,?,?)',[(stream,sid,e['action'],e['member']) for e in events])
            if fail_before_commit:raise RuntimeError('injected precommit fault')
            self.db.execute('COMMIT');return {'status':'accepted','events':events}
        except BaseException:
            self.db.execute('ROLLBACK');raise
    def ledger(self):
        return [{'stream':r[0],'snapshot_id':r[1],'action':r[2],'member':r[3]} for r in self.db.execute('SELECT * FROM events ORDER BY rowid')]
