# Safe browser (deep scan) and container hardening

**Status: the browser code passed its 7 live tests against the local staged pages (run with `FRAUDSHIELD_LIVE=1 FRAUDSHIELD_SANDBOX_ALLOW_HOSTS=127.0.0.1`). The Docker stack was built and run: the full browser flow passes against it, and Chromium runs inside the hardened container (non-root uid 10001, read-only filesystem, no Linux capabilities) with the private-address guard still blocking 169.254.169.254.**

## What the code enforces (`backend/app/sandbox/`)
- Every request, including redirects and sub-resources, must go to a public address (`is_public_url`); private, loopback and link-local targets are blocked and recorded.
- No downloads, dialogs dismissed, service workers blocked, hard time and size limits, heavy resource types aborted.
- Forms are never filled or submitted.

## What the containers add (`docker-compose.yml`)
- Backend and frontend run as non-root, `cap_drop: ALL`, `no-new-privileges`, read-only root filesystem, tmpfs for `/tmp`, memory and process limits.
- The `internal` network has no internet: frontend and backend talk only to each other. Only the backend joins `egress`.
- Data lives in one volume, `fraud_data`.

## What is NOT done
- The browser still runs in the same container as the API. A separate sandbox service (or gVisor / a throwaway container per scan) would limit the damage of a browser exploit further. `infra/docker/sandbox.Dockerfile` is a placeholder for that split.
- Network egress filtering by destination is not configured; on a real host add firewall rules that block private ranges (169.254.169.254 especially) from the egress network.
- Never point deep scan at a real scam URL during development without the owner's say-so; the staged local pages in `data/samples/staged` are the safe targets.

## Decision (2026-11-23): this is a demo build
Deep scan (safe browser) is **staff only** (analyst/admin login; visitors get 401), limited to 5 per minute per user, and is meant for the staged test pages only. Real scam pages are not opened: the sandbox is not ready for that (see the gaps below). `/scan` is limited to 60 per minute per client. Both limits can be switched off with `FRAUDSHIELD_RATE_LIMIT=0`.

## Honest security assessment before opening any real scam page (2026-11-23)
What protects the machine today, in layers:
1. **Address guard (app level):** every request must resolve only to public addresses; downloads, dialogs, forms, service workers blocked.
2. **Container:** non-root, no Linux capabilities, read-only root filesystem, memory and process limits, no folders from the host mounted (only a named volume), frontend cannot reach the internet.
3. **Docker Desktop on Windows runs containers inside a WSL2 virtual machine,** so a container escape would first land in that VM, not directly on Windows.

What it does NOT protect against (known gaps):
- **Chromium's own process sandbox is off.** Playwright starts Chromium without it by default, and the container has no capabilities to enable it. The container is the only wall around a browser exploit.
- **The browser shares a container with the API.** A browser exploit would sit next to the scan database, the password hashes and the session-signing key, and could mint an admin session. This is the biggest gap.
- **DNS rebinding:** the guard resolves the name before the request, then the browser resolves it again. A hostile DNS server could answer differently the second time and reach a private address (LAN, router, `host.docker.internal`). No network rule blocks private ranges yet.
- No CPU limit; the shared kernel/VM is only as safe as Docker Desktop and WSL2 are up to date.
- Real scam pages are the most likely place to meet browser exploit kits. Rare, but this is the case the sandbox exists for.

Fixes, in order of value: (1) run the browser in its own throwaway container with no secrets and no volume; (2) block private ranges and `host.docker.internal` on its network (firewall rule); (3) pin the resolved IP so the browser cannot be re-pointed; (4) enable Chromium's sandbox with a proper seccomp profile; (5) add CPU/disk limits and keep Docker Desktop updated.
Until (1) and (2) exist, deep scan should stay on staged pages. A text-only score of a real link (network lookups off) has no contact with the scam site at all.
