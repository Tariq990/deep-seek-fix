from pathlib import Path

from deep_seek_fix.benchmarks import smoke_report


def test_smoke_benchmark_has_zero_false_passes() -> None:
    report = smoke_report(Path("benchmarks/harbor/deep-seek-fix/dataset/smoke.json"))
    assert report.cases == 12
    assert report.false_pass_count == 0
    assert report.false_pass_rate == 0.0
