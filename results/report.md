# Complete before different

Across 9 authored update attempts after initialization, the complete-snapshot monitor emits 8 correct change events, 0 false events and misses 0. Union-of-response differencing emits 10 false events, including 6 false losses, and misses 1. Ground truth contains 8 gain/loss events.

The usual failure is treating a partial response as the complete population. My admission contract verifies a terminal cursor chain, stable snapshot version, unique membership and advancing sequence, then commits the head and events together. An empty complete snapshot is valid; an incomplete nonempty one is withheld.

This is a deliberately adversarial fixture of pagination boundaries with orderly connection reopen, not a killed-process, remote-service or distributed consistency benchmark. A real integration needs provider snapshot/version semantics. The next step is contract-testing a chosen provider's actual pagination guarantees.
