#!/usr/bin/env python3
"""
Automated Desktop Test Harness for Team A CV Algorithm.
Runs full test matrix against sample camera JPGs without Flutter or mobile hardware.
"""

import os
import sys
import glob
from kavach_cv import KavachPipeline


def run_harness():
    print("=" * 80)
    print("        KAVACH TEAM A (CV / C++) - STANDALONE ALGORITHM TEST HARNESS")
    print("=" * 80)

    test_cases = [
        {
            "name": "Target Drug Present (Positive Sample)",
            "file": "tests/sample_positive.jpg",
            "expected_status": "POSITIVE"
        },
        {
            "name": "No Drug / Control (Negative Sample)",
            "file": "tests/sample_negative.jpg",
            "expected_status": "NEGATIVE"
        },
        {
            "name": "Weak / Borderline Reaction (Inconclusive)",
            "file": "tests/sample_inconclusive.jpg",
            "expected_status": "INCONCLUSIVE"
        },
        {
            "name": "Real-World Camera Angle (15 deg Perspective Tilt)",
            "file": "tests/sample_tilted_camera.jpg",
            "expected_status": "POSITIVE"
        },
        {
            "name": "Degraded Capture / Out-of-Focus (Quality Reject)",
            "file": "tests/sample_blurry.jpg",
            "expected_status": "INCONCLUSIVE"
        }
    ]

    pipeline = KavachPipeline("config.json")
    all_passed = True

    print(f"{'Test Case':<36} | {'dE00':<7} | {'Expected':<12} | {'Actual':<12} | {'Pass/Fail'}")
    print("-" * 80)

    for tc in test_cases:
        img_path = tc["file"]
        if not os.path.exists(img_path):
            print(f"Error: missing test file {img_path}")
            continue

        case_id = os.path.splitext(os.path.basename(img_path))[0]
        out_dir = os.path.join("output", case_id)
        res = pipeline.process(img_path, output_dir=out_dir)

        actual_status = res["status"]
        expected_status = tc["expected_status"]
        de00_str = f"{res['deltaE00']:.2f}" if res['deltaE00'] < 900 else "N/A"

        is_match = (actual_status == expected_status)
        pf_str = "PASS [OK]" if is_match else "FAIL [X]"
        if not is_match:
            all_passed = False

        print(f"{tc['name']:<36} | {de00_str:<7} | {expected_status:<12} | {actual_status:<12} | {pf_str}")

    print("=" * 80)
    if all_passed:
        print("ALL PROTOTYPE CV ALGORITHM TESTS PASSED SUCCESSFULLY! Ready for demo.")
    else:
        print("SOME TESTS FAILED - Check individual case logs.")
    print("=" * 80 + "\n")
    return all_passed


if __name__ == "__main__":
    success = run_harness()
    sys.exit(0 if success else 1)
