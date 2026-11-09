import argparse
from pathlib import Path
import tempfile
from core import Monitor
from generate import generate
from support import ROOT,dump,manifest

def diff(old,new):return [{'action':'gain','member':m} for m in sorted(new-old)]+[{'action':'loss','member':m} for m in sorted(old-new)]
def keys(events):return {(e['action'],e['member']) for e in events}
def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);data=generate();rows=[]
    totals={m:{'true_positive':0,'false_positive':0,'false_loss':0,'missed':0} for m in ['complete_snapshot','response_union']}
    naive=set(data['initial'][0]['members'])
    with tempfile.TemporaryDirectory() as t:
        path=Path(t)/'snapshots.db';mon=Monitor(path);mon.admit('fixture',data['initial'])
        for case in data['cases']:
            observed={m for p in case['pages'] for m in p['members']};baseline=diff(naive,observed);naive=observed
            try:result=mon.admit('fixture',case['pages'])
            except ValueError as e:result={'status':'refused','reason':str(e),'events':[]}
            expected=keys(case['expected']);row={'case':case['id'],'expected':case['expected'],'guarded':result,'baseline_events':baseline}
            for name,events in [('complete_snapshot',result['events']),('response_union',baseline)]:
                actual=keys(events);totals[name]['true_positive']+=len(actual&expected);totals[name]['false_positive']+=len(actual-expected)
                totals[name]['false_loss']+=sum(a=='loss' for a,m in actual-expected);totals[name]['missed']+=len(expected-actual)
            rows.append(row)
            # Explicit orderly reopen tests durable admission and retry state.
            mon.close();mon=Monitor(path)
        ledger=mon.ledger();final=sorted(mon.state('fixture'));mon.close()
    metrics={'snapshots_attempted':len(rows),'comparison':totals,'expected_change_events':8,'final_members':final,
             'scope':'Local authored pagination/restart contracts; no external API reliability estimate.'}
    dump(output/'decisions.json',rows);dump(output/'event-ledger.json',ledger);dump(output/'metrics.json',metrics)
    g,b=totals['complete_snapshot'],totals['response_union']
    report=f"# Complete before different\n\nAcross {len(rows)} authored update attempts after initialization, the complete-snapshot monitor emits {g['true_positive']} correct change events, {g['false_positive']} false events and misses {g['missed']}. Union-of-response differencing emits {b['false_positive']} false events, including {b['false_loss']} false losses, and misses {b['missed']}. Ground truth contains 8 gain/loss events.\n\nThe usual failure is treating a partial response as the complete population. My admission contract verifies a terminal cursor chain, stable snapshot version, unique membership and advancing sequence, then commits the head and events together. An empty complete snapshot is valid; an incomplete nonempty one is withheld.\n\nThis is a deliberately adversarial fixture of pagination boundaries with orderly connection reopen, not a killed-process, remote-service or distributed consistency benchmark. A real integration needs provider snapshot/version semantics. The next step is contract-testing a chosen provider's actual pagination guarantees.\n"
    (output/'report.md').write_bytes(report.encode());manifest(output);return metrics

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='results');a=p.parse_args();print(run(ROOT/a.output))
