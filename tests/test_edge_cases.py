from src.intelligence import analyze_test


def test_zero_measurement():
    result = analyze_test(
        measurement=0,
        threshold=20.0,
        quality_status="GOOD"
    )

    assert result["result"] == "NEGATIVE"


def test_measurement_equal_to_threshold():
    result = analyze_test(
        measurement=20.0,
        threshold=20.0,
        quality_status="GOOD"
    )

    assert result["result"] == "POSITIVE"


def test_bad_quality_with_high_measurement():
    result = analyze_test(
        measurement=100.0,
        threshold=20.0,
        quality_status="BAD"
    )

    assert result["result"] == "INCONCLUSIVE"


def test_missing_measurement():
    result = analyze_test(
        measurement=None,
        threshold=20.0,
        quality_status="GOOD"
    )

    assert result["result"] == "INCONCLUSIVE"


def test_missing_threshold():
    result = analyze_test(
        measurement=25.0,
        threshold=None,
        quality_status="GOOD"
    )

    assert result["result"] == "INCONCLUSIVE"