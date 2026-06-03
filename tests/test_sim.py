import time

from sim import ScriptedEMGSource


def test_scripted_emg_cycles_segments(monkeypatch):
    segments = [((1.0, 0.0), 0.1), ((0.0, 1.0), 0.1)]
    source = ScriptedEMGSource(segments, repeat=False)

    base = time.time()
    monkeypatch.setattr("sim.emg_profiles.time", lambda: base)
    assert source.read() == (1.0, 0.0)

    monkeypatch.setattr("sim.emg_profiles.time", lambda: base + 0.11)
    assert source.read() == (0.0, 1.0)

    monkeypatch.setattr("sim.emg_profiles.time", lambda: base + 0.25)
    assert source.read() == (0.0, 1.0)

