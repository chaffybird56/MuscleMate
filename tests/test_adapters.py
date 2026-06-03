from hardware.adapters import BenchRigAdapter, IntegrationRigAdapter


def test_bench_adapter_commissioning():
    adapter = BenchRigAdapter()
    adapter.connect()
    report = adapter.commissioning_report()
    assert report["phase"] == "bench"
    assert "home_reached" in report["checks"]


def test_integration_requires_signoff():
    adapter = IntegrationRigAdapter()
    adapter.set_bench_signoff("TEST-001")
    adapter.connect()
    assert adapter.commissioning_report()["bench_signoff_id"] == "TEST-001"
