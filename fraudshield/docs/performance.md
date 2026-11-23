# Performance (measured 2026-11-23)

Measured on the developer's Windows laptop, against the Docker stack (backend container with the URL model on), calling `POST /api/v1/scan` over `127.0.0.1`. Small samples (n = 20 per row), one machine, one afternoon. Treat as indicative, not as a benchmark.

| What | Result |
|---|---|
| Link scan, link never seen before, network lookups on | median **103 ms**, p95 230 ms, max 281 ms |
| Same link scanned again | median **43 ms**, p95 79 ms, max 108 ms |
| Domain lookups (registration, DNS, certificate) for a **new** registered domain, first time | about **1 s** (983 ms measured inside the container); cached afterwards (1 ms) |
| URL model (neural network, runs in plain numpy) | about 100-175 ms per link |
| Deep scan (safe browser) of a page served inside the container | median **0.94 s** (0.84-1.6 s over 6 runs) |
| Deep scan of a real page on the internet | **not measured**: depends on the page and the network, and we do not open real scam pages without permission. Earlier notes put it at roughly 4-5 s with a fresh browser each time |

Caveats worth knowing before quoting any of this:
- The "fresh link" rows reuse one registered domain (`example.com`), so the registration lookup was cached after the first link. A genuinely new domain costs about a second more, the first time only.
- Measuring through `localhost` on Windows added about 2 s of connection delay (IPv6 tried first). The figures above use `127.0.0.1`. Use that address when testing yourself.
- No load test was run: nothing here says how many scans per second one server handles.
- The browser starts fresh for every deep scan (no pool), so deep scans are slower than they could be.

Reproduce: start the stack (`docker compose up -d`), then run a loop of `POST /api/v1/scan` calls with `time`.
