# Stand-alone safe browser for deep scans, if you want it separate from the API.
# Today the backend image already includes this capability (app/sandbox/fetcher.py), so this file is
# only for splitting it out later. It carries no secrets and runs without privileges.
FROM mcr.microsoft.com/playwright/python:v1.65.2-jammy
RUN pip install --no-cache-dir playwright==1.65.2
RUN useradd --system --uid 10002 sandbox
USER sandbox
WORKDIR /srv
# Egress control belongs to the network, not the app: run it on a network that blocks private ranges
# (see docs/sandbox.md). The app also refuses non-public addresses on every request.
CMD ["sleep", "infinity"]
