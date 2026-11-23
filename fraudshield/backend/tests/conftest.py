import os
import tempfile
from pathlib import Path

# Tests must never touch the network. Set before the app is imported.
os.environ["FRAUDSHIELD_NETWORK"] = "0"
# ...and never read a real discovery database (this file is never created unless a test writes to it).
os.environ["FRAUDSHIELD_DISCOVERY_DB"] = str(Path(tempfile.mkdtemp(prefix="fs-test-")) / "discovery.db")
# ...and never send a real alert.
os.environ.pop("TELEGRAM_BOT_TOKEN", None)
os.environ.pop("TELEGRAM_CHAT_ID", None)
os.environ["FRAUDSHIELD_THREAT_DB"] = str(Path(tempfile.mkdtemp(prefix="fs-test-")) / "threat.db")
os.environ["FRAUDSHIELD_DB"] = str(Path(tempfile.mkdtemp(prefix="fs-test-")) / "fraudshield.db")
# the ready model is optional; tests turn it on explicitly where they need it
os.environ["FRAUDSHIELD_ML"] = "0"
# login is switched off for the general suite; test_auth.py turns it on
os.environ["FRAUDSHIELD_AUTH"] = "0"
# the scan rate limit is off for the general suite; test_scan_limits.py turns it on
os.environ["FRAUDSHIELD_RATE_LIMIT"] = "0"
