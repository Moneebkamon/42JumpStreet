"""Regression guard on the hand-labelled golden set (tests/fixtures/golden_urls.json).

The pass criteria are floors that stop the scorer from quietly getting worse. They are NOT an accuracy claim: the rules were
tuned by the same person who wrote the set. Known gaps are listed here on purpose, so a fix shows up as a test to tighten.
"""
import json
from pathlib import Path

import pytest

from app.engine.pipeline import run_pipeline

CASES = json.loads((Path(__file__).parents[1] / "fixtures" / "golden_urls.json").read_text(encoding="utf-8"))["cases"]
FLAG = 30
KNOWN_FALSE_ALARMS = {"https://www.emirates-estate-agents.ae/properties"}  # a brand word inside an unrelated .ae business
KNOWN_MISSES = {"http://bit.ly/3xYzAbC"}  # a shortener hides the target; the text alone says little


@pytest.fixture(scope="module")
def scored(tmp_path_factory):
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("FRAUDSHIELD_DB", str(tmp_path_factory.mktemp("g") / "f.db"))  # no admin overrides leak in
        yield [{**c, "score": run_pipeline(c["url"])["score"]} for c in CASES]


def test_set_is_a_sensible_mix():
    kinds = [c["truth"] for c in CASES]
    assert len(CASES) >= 30 and kinds.count("phish") >= 12 and kinds.count("benign") >= 8 and kinds.count("hard_negative") >= 6


def test_no_new_false_alarms(scored):
    alarms = {r["url"] for r in scored if r["truth"] != "phish" and r["score"] >= FLAG}
    assert alarms <= KNOWN_FALSE_ALARMS, f"new false alarms: {alarms - KNOWN_FALSE_ALARMS}"


def test_phishing_style_links_are_still_caught(scored):
    missed = {r["url"] for r in scored if r["truth"] == "phish" and r["score"] < FLAG}
    assert missed <= KNOWN_MISSES, f"newly missed: {missed - KNOWN_MISSES}"
    caught = sum(1 for r in scored if r["truth"] == "phish" and r["score"] >= FLAG)
    assert caught >= 13


def test_official_domains_stay_low(scored):
    for r in scored:
        if r["note"].startswith("official brand domain"):
            assert r["score"] <= 10, r["url"]
