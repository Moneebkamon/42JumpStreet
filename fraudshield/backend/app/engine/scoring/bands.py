"""Map a 0-100 score to a band name and action, using config/risk_bands.yaml."""
from app.engine.scoring.tuning import bands


def band_for(score: int) -> dict:
    for band in bands():
        if band["min"] <= score <= band["max"]:
            return {"name": band["name"], "action": band["action"]}
    raise ValueError(f"score {score} is outside every configured band")
