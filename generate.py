from support import ROOT,dump

def page(sid,seq,members,cursor='start',next_cursor=None):
    return {'snapshot_id':sid,'sequence':seq,'cursor':cursor,'next_cursor':next_cursor,'terminal':next_cursor is None,'members':members}

def generate():
    initial=[page('s1',1,['a','b','c','d'])]
    complete2=[page('s2',2,['a','b'],next_cursor='p2'),page('s2',2,['c','d','e'],cursor='p2')]
    cases=[
      {'id':'partial-page','pages':[complete2[0]],'expected':[]},
      {'id':'complete-retry-out-of-order','pages':[complete2[1],complete2[0],complete2[1]],'expected':[{'action':'gain','member':'e'}]},
      {'id':'mixed-snapshot','pages':[page('s3',3,['a','b'],next_cursor='p2'),page('different',3,['c','d'],cursor='p2')],'expected':[]},
      {'id':'complete-removals','pages':[page('s3',3,['a','c','d'])],'expected':[{'action':'loss','member':'b'},{'action':'loss','member':'e'}]},
      {'id':'duplicate-retry','pages':[page('s3',3,['a','c','d'])],'expected':[]},
      {'id':'stale-unseen-id','pages':[page('old-but-new-id',2,['a','b','c','d','e'])],'expected':[]},
      {'id':'empty-complete','pages':[page('s4',4,[])],'expected':[{'action':'loss','member':m} for m in ['a','c','d']]},
      {'id':'rejoin','pages':[page('s5',5,['a','x'])],'expected':[{'action':'gain','member':'a'},{'action':'gain','member':'x'}]},
      {'id':'cursor-cycle','pages':[page('s6',6,['a'],next_cursor='p2'),page('s6',6,[],cursor='p2',next_cursor='start')],'expected':[]}]
    value={'initial':initial,'cases':cases};dump(ROOT/'data/snapshots.json',value);return value
