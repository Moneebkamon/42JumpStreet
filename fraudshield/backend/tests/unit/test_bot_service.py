from app.alerts import whatsapp
from app.guard import bot_service


def _links(band, score=70):
    return [{"url": "http://x.example", "band": band, "score": score, "reasons": ["why"]}]


def test_no_link_asks_for_one():
    assert "link" in bot_service.build_reply("hello", [])


def test_arabic_message_gets_arabic_reply():
    assert "رابط" in bot_service.build_reply("مرحبا", [])


def test_bad_link_warns_not_to_open():
    out = bot_service.build_reply("see http://x.example", _links("likely_fraud", 90))
    assert "Do NOT open" in out and "http://x.example" in out


def test_handle_replies_to_sender_and_rate_limits(monkeypatch):
    sent = []
    monkeypatch.setattr(whatsapp, "send_text", lambda n, t, instance=None: sent.append((n, instance)) or True)
    bot_service.limiter.reset()
    bot_service.notice_limiter.reset()
    assert bot_service.handle("9715@s.whatsapp.net", "hello") is True
    assert sent == [("9715@s.whatsapp.net", bot_service.bot_instance())]
    for _ in range(12):
        bot_service.handle("9715@s.whatsapp.net", "hello")
    assert len(sent) == 11  # ten answers, plus exactly one "slow down" notice
