# FraudShield backend (API + optional safe-browser deep scan).
# Build from the fraudshield/ folder:  docker build -f infra/docker/backend.Dockerfile -t fraudshield-backend .
# The Playwright base image must match the pinned playwright version in requirements.txt (browsers are baked in).
# It already contains Chromium and its system libraries (large: ~2 GB).
FROM mcr.microsoft.com/playwright/python:v1.65.2-jammy

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/srv \
    FRAUDSHIELD_DB=/data/fraudshield.db \
    FRAUDSHIELD_DISCOVERY_DB=/data/discovery.db \
    FRAUDSHIELD_THREAT_DB=/data/threat_feeds.db \
    FRAUDSHIELD_CONFIG_DIR=/srv/config \
    FRAUDSHIELD_MODEL_DIR=/srv/ml/artifacts/urlbert-tiny-v2

WORKDIR /srv
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY config /srv/config
# The ready-made URL model (MIT licence) is copied in only if you downloaded it: see ml/README.md.
COPY ml/artifacts /srv/ml/artifacts
# The SIMULATED certificate sample and its runner, so the early-detection feed can be filled (see README).
COPY data/samples/ct_stream.jsonl /srv/samples/ct_stream.jsonl
COPY scripts/run_discovery.py /srv/scripts/run_discovery.py
COPY scripts/run_ct_listener.py /srv/scripts/run_ct_listener.py

# Run as an unprivileged user; /data is the only writable place (mount a volume there).
RUN useradd --system --uid 10001 fraud && mkdir /data && chown fraud /data
USER fraud
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/v1/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
