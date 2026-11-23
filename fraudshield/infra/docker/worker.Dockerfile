# Background worker for discovery ingestion (scripts/run_discovery.py). Same image as the backend.
# Usage: docker run --rm -v fraud_data:/data fraudshield-backend python -m scripts.run_discovery
FROM fraudshield-backend
COPY scripts /srv/scripts
CMD ["python", "scripts/run_discovery.py"]
