# Snapshot Completeness Monitor

A missing response page can make active members appear to have left. The experiment feeds two change detectors the same nine update attempts, including a partial snapshot, mixed versions, a stale sequence and a complete empty snapshot.

One detector takes the union of whatever responses arrive. The other requires a consistent snapshot identity and a complete cursor chain, then commits the new population and its events together. An identical retry is safe. If the provider cannot establish that the final page belongs to the same snapshot, the previous population stays in effect. [Admission and commit logic](core.py)

The fixture contains eight real changes by construction. The complete-snapshot detector found all eight with zero false events. Response-union differencing missed one and emitted ten false events, six of them losses. [Event ledger](results/event-ledger.json) · [Comparison](results/metrics.json)

The [precommit-fault test](tests/test_snapshot.py#L34) checks that the previous head and events survive an interrupted write and that retrying yields one change. The fixture exercises a local pagination contract with trusted sequence and identity fields.

## Replay the snapshots

The [update attempts](data/snapshots.json) are local fixtures. Replay them with Python 3.11.

```bash
python -m unittest discover -s tests -v
python run.py --output runs/local
```

[Data card](docs/data-card.md) · [Run manifest](results/manifest.json) · [Source and contribution notes](docs/provenance.md)
