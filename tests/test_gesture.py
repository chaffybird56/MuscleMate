import time

from control.config import Thresholds
from control.gesture import GestureDecoder, Intent


def test_grip_intent_trigger_after_debounce(monkeypatch):
    thresholds = Thresholds(debounce_s=0.0, cooldown_s=0.0)
    decoder = GestureDecoder(thresholds)

    now = time.time()
    monkeypatch.setattr("control.gesture.time", lambda: now)
    decoder.update(0.0, 1.0)
    monkeypatch.setattr("control.gesture.time", lambda: now + 0.1)

    assert decoder.intent() == Intent.GRIP


def test_cooldown_blocks_retrigger(monkeypatch):
    thresholds = Thresholds(cooldown_s=0.2, debounce_s=0.0)
    decoder = GestureDecoder(thresholds)

    base = time.time()
    monkeypatch.setattr("control.gesture.time", lambda: base)
    decoder.update(1.0, 0.0)
    monkeypatch.setattr("control.gesture.time", lambda: base + 0.1)
    assert decoder.intent() == Intent.START

    monkeypatch.setattr("control.gesture.time", lambda: base + 0.15)
    assert decoder.intent() == Intent.NONE


def test_long_press_triggers_abort(monkeypatch):
    thresholds = Thresholds(longpress_s=0.3, debounce_s=0.0, cooldown_s=0.0)
    decoder = GestureDecoder(thresholds)

    base = time.time()
    monkeypatch.setattr("control.gesture.time", lambda: base)
    decoder.update(0.0, 1.0)
    monkeypatch.setattr("control.gesture.time", lambda: base + 0.31)
    assert decoder.intent() == Intent.ABORT

