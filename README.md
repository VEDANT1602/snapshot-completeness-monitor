# Snapshot Completeness Monitor

A missing page should not become a lost member.

This independent portfolio experiment by Vedant Thaker runs locally on Python 3.11. All inputs are original fictional or synthetic fixtures. It requires no cloud account, paid API, credentials, external weights or employer data.

## The decision

I narrowed change-data capture to a complete-snapshot admission rule. A response union is tempting because set difference is simple; missing pages can turn it into false loss events. My implementation assembles a coherent cursor chain, checks identity and sequence, and atomically commits a new head with gain/loss events. Retried pages are deduplicated only when their content agrees.

## Reproduce and inspect

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run.py --output runs/ci
```

The default `python run.py` refreshes committed `results/`; `--output` writes a fresh run to an ignored directory. The seeded generator in `generate.py` writes the original input fixtures to `data/`. [Measured results](results/report.md), [raw metrics](results/metrics.json), and [source/data/result digests](results/manifest.json) make the experiment inspectable. Tests verify known answers and failure boundaries, not just successful execution.

## Measured comparison and next decision

Across **9 update attempts**, the admitted snapshots produce **8 correct change events, 0 false events and 0 missed events**. Response-union differencing produces **10 false events**, including **6 false losses**, and misses 1 change. The fixture includes missing pages, mixed versions, retries, a stale sequence, a complete empty population and a rejoining member.

The next integration decision is whether a real provider supplies a stable snapshot identity and terminal-page guarantee. Without that contract, this monitor should withhold change events rather than pretend the population is complete.

## What the result can support

The experiment uses fictional member keys and local pagination responses. Snapshot identity and sequence are trusted provider assertions, not inferred from wall-clock order. There are no live API calls, real audience records, polling service, multi-host replication or provider reliability claims. Initial population is seeded without emitting acquisition events.

The next decision follows from the recorded comparison, including weak or negative outcomes. No synthetic result is presented as an employer deployment or a real-world business improvement.

See [data card](docs/data-card.md) and [reference credits](docs/provenance.md). Original code and fixtures are MIT licensed.
