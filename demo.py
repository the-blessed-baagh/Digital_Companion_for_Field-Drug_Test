from src.intelligence import analyze_and_save
from src.signature import generate_key_pair, verify_record


def run_case(case_name, test_id, measurement, quality_status):
    print("=" * 60)
    print(case_name)
    print("=" * 60)

    result = analyze_and_save(
        test_id=test_id,
        measurement=measurement,
        quality_status=quality_status,
        test_type="prototype_test"
    )

    print(f"Measurement       : {measurement}")
    print(f"Quality Status    : {quality_status}")
    print(f"Result            : {result['result']}")
    print(f"Confidence        : {result['confidence']}")
    print(f"Threshold         : {result['threshold']}")
    print(f"Decision Reason   : {result['decision_reason']}")
    print(f"Record Hash       : {result['record_hash']}")
    print(f"Signature Length  : {len(result['signature'])} characters")

    return result


def main():
    print("\nKAVACH - DATA + INTELLIGENCE + SECURITY DEMO\n")

    positive = run_case(
        "CASE 1 - POSITIVE TEST",
        "KAVACH-DEMO-POSITIVE",
        24.0,
        "GOOD"
    )

    negative = run_case(
        "CASE 2 - NEGATIVE TEST",
        "KAVACH-DEMO-NEGATIVE",
        15.0,
        "GOOD"
    )

    inconclusive = run_case(
        "CASE 3 - INCONCLUSIVE TEST",
        "KAVACH-DEMO-INCONCLUSIVE",
        24.0,
        "BAD"
    )

    print("=" * 60)
    print("SECURITY VERIFICATION")
    print("=" * 60)

    _, verify_key = generate_key_pair()

    valid = verify_record(
        positive["record_hash"],
        positive["signature"],
        verify_key
    )

    print(f"Original record signature valid : {valid}")

    tampered_hash = positive["record_hash"][:-1] + (
        "0" if positive["record_hash"][-1] != "0" else "1"
    )

    tampered_valid = verify_record(
        tampered_hash,
        positive["signature"],
        verify_key
    )

    print(f"Tampered record signature valid : {tampered_valid}")

    print("\n" + "=" * 60)
    print("KAVACH DEMO COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()