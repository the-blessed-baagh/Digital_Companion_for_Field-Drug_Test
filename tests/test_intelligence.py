from src.intelligence import analyze_test


def test_positive_result():
    result = analyze_test(
        measurement=24.0,
        threshold=20.0,
        quality_status="GOOD"
    )

    assert result["result"] == "POSITIVE"


def test_negative_result():
    result = analyze_test(
        measurement=15.0,
        threshold=20.0,
        quality_status="GOOD"
    )

    assert result["result"] == "NEGATIVE"


def test_bad_quality_is_inconclusive():
    result = analyze_test(
        measurement=24.0,
        threshold=20.0,
        quality_status="BAD"
    )

    assert result["result"] == "INCONCLUSIVE"


def test_missing_measurement_is_inconclusive():
    result = analyze_test(
        measurement=None,
        threshold=20.0,
        quality_status="GOOD"
    )

    assert result["result"] == "INCONCLUSIVE"


def test_missing_threshold_is_inconclusive():
    result = analyze_test(
        measurement=24.0,
        threshold=None,
        quality_status="GOOD"
    )

    assert result["result"] == "INCONCLUSIVE"