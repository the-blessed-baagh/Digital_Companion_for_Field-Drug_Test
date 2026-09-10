#!/usr/bin/env python3
"""
KAVACH Phase-1 Standalone Computer Vision Pipeline & Test Harness
Performs:
  1. Image Quality Validation (Blur via Laplacian variance & Brightness check)
  2. ArUco Marker Detection (4 fiducials defining card boundary & orientation)
  3. Homography Perspective Rectification (Warp to canonical 1000x700 space)
  4. Robust Trimmed-Mean ROI Extraction (Reference Patches & Reaction Zone)
  5. Least-Squares Color Correction Matrix (CCM) Calibration
  6. CIELAB Color Space Transformation
  7. ISO/CIE Standard CIEDE2000 (Delta E 00) Perceptual Color Difference Calculation
  8. Classification (POSITIVE / NEGATIVE / INCONCLUSIVE)
  9. Generation of visual debug artifacts and structured result.json
"""

import argparse
import json
import math
import os
import sys
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np


class KavachPipeline:
    def __init__(self, config_path: str = "config.json"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            self.cfg = json.load(f)

        self.warp_w = int(self.cfg["warp_width"])
        self.warp_h = int(self.cfg["warp_height"])
        self.marker_ids = self.cfg["marker_ids"]
        self.target_lab = np.array(self.cfg["target_lab"], dtype=np.float64)

        # Predefined ArUco dictionary
        dict_name = getattr(cv2.aruco, self.cfg["dictionary"])
        self.dictionary = cv2.aruco.getPredefinedDictionary(dict_name)
        self.detector_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.detector_params)

    def check_quality(self, image: np.ndarray) -> Tuple[bool, float, float, str]:
        """Validates blur and brightness to prevent false negatives from compromised imagery."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness = float(gray.mean())

        q = self.cfg["image_quality"]
        reasons = []
        if blur_score < q["min_blur_score"]:
            reasons.append(f"BLUR_DETECTED (score: {blur_score:.1f} < {q['min_blur_score']})")
        if brightness < q["min_brightness"]:
            reasons.append(f"IMAGE_TOO_DARK (lum: {brightness:.1f} < {q['min_brightness']})")
        elif brightness > q["max_brightness"]:
            reasons.append(f"IMAGE_OVEREXPOSED (lum: {brightness:.1f} > {q['max_brightness']})")

        is_ok = len(reasons) == 0
        status_msg = "PASSED" if is_ok else " | ".join(reasons)
        return is_ok, blur_score, brightness, status_msg

    def detect_markers(self, image: np.ndarray) -> Tuple[Dict[str, np.ndarray], tuple, Optional[np.ndarray]]:
        """Detects ArUco markers and locates the 4 card reference corners."""
        corners, ids, rejected = self.detector.detectMarkers(image)
        if ids is None or len(ids) == 0:
            return {}, corners, ids

        found = {}
        reverse_map = {v: k for k, v in self.marker_ids.items()}
        for c, marker_id in zip(corners, ids.flatten().tolist()):
            if marker_id in reverse_map:
                pts = c.reshape(4, 2).astype(np.float32)
                # Compute centroid of the marker
                found[reverse_map[marker_id]] = pts.mean(axis=0)
        return found, corners, ids

    def warp_card(self, image: np.ndarray, found_markers: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates homography and rectifies card perspective to standard dimensions."""
        order = ["top_left", "top_right", "bottom_right", "bottom_left"]
        missing = [k for k in order if k not in found_markers]
        if missing:
            raise ValueError(f"Missing required ArUco markers: {', '.join(missing)}")

        src_pts = np.array([found_markers[k] for k in order], dtype=np.float32)

        # Destination points mapped precisely to the marker design centers
        centers = self.cfg["marker_design_centers"]
        dst_pts = np.array([centers[k] for k in order], dtype=np.float32)

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(image, M, (self.warp_w, self.warp_h))
        return warped, M

    @staticmethod
    def extract_robust_bgr(region: np.ndarray) -> np.ndarray:
        """Extracts glare-resistant trimmed-mean BGR from a region."""
        if region.size == 0:
            raise ValueError("ROI extraction resulted in an empty image region.")
        flat = region.reshape(-1, 3).astype(np.float64)

        # Trim top and bottom 10% in each channel to eliminate specular reflection and noise
        channel_means = []
        for ch in range(3):
            sorted_vals = np.sort(flat[:, ch])
            n = len(sorted_vals)
            lo, hi = int(0.10 * n), int(0.90 * n)
            selected = sorted_vals[lo:hi] if hi > lo else sorted_vals
            channel_means.append(float(np.mean(selected)))
        return np.array(channel_means, dtype=np.float64)

    @staticmethod
    def solve_ccm(observed_bgrs: List[np.ndarray], target_bgrs: List[np.ndarray]) -> np.ndarray:
        """
        Fits 3x3 Color Correction Matrix M using Moore-Penrose pseudo-inverse:
        target ≈ M * observed => M = target * pinv(observed)
        """
        O = np.stack(observed_bgrs, axis=1)  # 3 x N
        T = np.stack(target_bgrs, axis=1)    # 3 x N
        M = T @ np.linalg.pinv(O)
        return M

    @staticmethod
    def apply_ccm(bgr: np.ndarray, M: np.ndarray) -> np.ndarray:
        """Applies 3x3 CCM calibration and clamps to 8-bit dynamic range."""
        corrected = M @ bgr
        return np.clip(corrected, 0.0, 255.0)

    @staticmethod
    def bgr_to_lab(bgr: np.ndarray) -> np.ndarray:
        """Converts BGR [0..255] float to conventional CIELAB [L:0..100, a:-128..127, b:-128..127]."""
        bgr_norm = np.clip(bgr / 255.0, 0.0, 1.0).astype(np.float32)
        px = np.array([[bgr_norm]], dtype=np.float32)
        lab = cv2.cvtColor(px, cv2.COLOR_BGR2Lab)[0, 0]
        return np.array([float(lab[0]), float(lab[1]), float(lab[2])], dtype=np.float64)

    @staticmethod
    def ciede2000(lab1: np.ndarray, lab2: np.ndarray) -> float:
        """Computes ISO/CIE 11664-6 standard CIEDE2000 total color difference."""
        L1, a1, b1 = map(float, lab1)
        L2, a2, b2 = map(float, lab2)

        C25_7 = 25.0 ** 7
        C1 = math.hypot(a1, b1)
        C2 = math.hypot(a2, b2)
        Cbar = (C1 + C2) / 2.0
        G = 0.5 * (1.0 - math.sqrt((Cbar ** 7) / (Cbar ** 7 + C25_7))) if Cbar else 0.5

        ap1 = (1.0 + G) * a1
        ap2 = (1.0 + G) * a2
        Cp1 = math.hypot(ap1, b1)
        Cp2 = math.hypot(ap2, b2)

        def get_hp(a, b):
            if a == 0 and b == 0:
                return 0.0
            h = math.degrees(math.atan2(b, a))
            return h + 360.0 if h < 0 else h

        hp1 = get_hp(ap1, b1)
        hp2 = get_hp(ap2, b2)

        dLp = L2 - L1
        dCp = Cp2 - Cp1
        dh = hp2 - hp1
        if Cp1 * Cp2 == 0:
            dh = 0.0
        elif dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        dHp = 2.0 * math.sqrt(Cp1 * Cp2) * math.sin(math.radians(dh / 2.0))

        Lbar = (L1 + L2) / 2.0
        Cpbar = (Cp1 + Cp2) / 2.0
        if Cp1 * Cp2 == 0:
            hpbar = hp1 + hp2
        elif abs(hp1 - hp2) <= 180:
            hpbar = (hp1 + hp2) / 2.0
        elif hp1 + hp2 < 360:
            hpbar = (hp1 + hp2 + 360.0) / 2.0
        else:
            hpbar = (hp1 + hp2 - 360.0) / 2.0

        T = (1.0
             - 0.17 * math.cos(math.radians(hpbar - 30.0))
             + 0.24 * math.cos(math.radians(2.0 * hpbar))
             + 0.32 * math.cos(math.radians(3.0 * hpbar + 6.0))
             - 0.20 * math.cos(math.radians(4.0 * hpbar - 63.0)))

        dtheta = 30.0 * math.exp(-((hpbar - 275.0) / 25.0) ** 2)
        Rc = 2.0 * math.sqrt((Cpbar ** 7) / (Cpbar ** 7 + C25_7)) if Cpbar else 0.0
        Sl = 1.0 + (0.015 * (Lbar - 50.0) ** 2) / math.sqrt(20.0 + (Lbar - 50.0) ** 2)
        Sc = 1.0 + 0.045 * Cpbar
        Sh = 1.0 + 0.015 * Cpbar * T
        Rt = -math.sin(math.radians(2.0 * dtheta)) * Rc

        delta_e = math.sqrt(
            (dLp / Sl) ** 2
            + (dCp / Sc) ** 2
            + (dHp / Sh) ** 2
            + Rt * (dCp / Sc) * (dHp / Sh)
        )
        return float(delta_e)

    def create_analysis_dashboard(self, warped: np.ndarray, test_roi: np.ndarray,
                                  obs_bgr: np.ndarray, corr_bgr: np.ndarray,
                                  target_bgr: np.ndarray, result: dict) -> np.ndarray:
        """Generates a comprehensive executive visual dashboard for the prototype presentation."""
        dash_w, dash_h = 1200, 750
        dashboard = np.full((dash_h, dash_w, 3), 245, dtype=np.uint8)

        # Header
        cv2.rectangle(dashboard, (0, 0), (dash_w, 80), (33, 37, 41), -1)
        cv2.putText(dashboard, "KAVACH CV ENGINE - REAGENT ANALYSIS DASHBOARD", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)

        # Left Column: Warped Card Preview
        thumb_h = 420
        thumb_w = int(thumb_h * (self.warp_w / self.warp_h))
        card_thumb = cv2.resize(warped, (thumb_w, thumb_h))
        dashboard[110:110 + thumb_h, 30:30 + thumb_w] = card_thumb
        cv2.rectangle(dashboard, (30, 110), (30 + thumb_w, 110 + thumb_h), (80, 80, 80), 2)
        cv2.putText(dashboard, "PERSPECTIVE-RECTIFIED CARD & ACTIVE ROIs", (30, 555),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (70, 70, 70), 1, cv2.LINE_AA)

        # Right Column: Color Swatches & Classification Panel
        panel_x = 30 + thumb_w + 40
        cv2.putText(dashboard, "COLOR CALIBRATION & REAGENT MATCHING", (panel_x, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.70, (40, 40, 40), 2, cv2.LINE_AA)

        # Swatch display
        swatches = [
            ("Raw Observed Color", obs_bgr),
            ("CCM-Corrected Color", corr_bgr),
            ("Target Reagent Profile", target_bgr)
        ]
        swatch_y = 150
        for title, bgr in swatches:
            cv2.putText(dashboard, title, (panel_x, swatch_y + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, (60, 60, 60), 1, cv2.LINE_AA)
            col = [int(np.clip(c, 0, 255)) for c in bgr]
            cv2.rectangle(dashboard, (panel_x + 230, swatch_y), (panel_x + 360, swatch_y + 40), col, -1)
            cv2.rectangle(dashboard, (panel_x + 230, swatch_y), (panel_x + 360, swatch_y + 40), (40, 40, 40), 2)
            bgr_txt = f"RGB: {col[2]},{col[1]},{col[0]}"
            cv2.putText(dashboard, bgr_txt, (panel_x + 375, swatch_y + 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 80, 80), 1, cv2.LINE_AA)
            swatch_y += 55

        # Quantitative Metrics Table
        cv2.line(dashboard, (panel_x, swatch_y + 10), (dash_w - 30, swatch_y + 10), (200, 200, 200), 2)
        metric_y = swatch_y + 40
        metrics = [
            ("Delta E00 (Perceptual Distance)", f"{result['deltaE00']:.3f}"),
            ("Observed Lab [L, a, b]", f"[{result['observedLab'][0]:.1f}, {result['observedLab'][1]:.1f}, {result['observedLab'][2]:.1f}]"),
            ("Target Lab [L, a, b]", f"[{result['targetLab'][0]:.1f}, {result['targetLab'][1]:.1f}, {result['targetLab'][2]:.1f}]"),
            ("Blur Score (Laplacian Var)", f"{result['blurScore']:.1f}"),
            ("Mean Luminance (0-255)", f"{result['brightness']:.1f}")
        ]
        for label, val in metrics:
            cv2.putText(dashboard, label, (panel_x, metric_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, (60, 60, 60), 1, cv2.LINE_AA)
            cv2.putText(dashboard, val, (panel_x + 310, metric_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (20, 20, 20), 2, cv2.LINE_AA)
            metric_y += 32

        # Status Banner Badge
        status = result["status"]
        if status == "POSITIVE":
            badge_color = (40, 167, 69)      # Green
            badge_text = "STATUS: POSITIVE (TARGET DRUG DETECTED)"
        elif status == "NEGATIVE":
            badge_color = (220, 53, 69)      # Red
            badge_text = "STATUS: NEGATIVE (NO REACTION)"
        else:
            badge_color = (255, 193, 7)      # Amber
            badge_text = f"STATUS: INCONCLUSIVE ({result.get('reason', 'BORDERLINE')})"

        cv2.rectangle(dashboard, (panel_x, 620), (dash_w - 30, 695), badge_color, -1)
        text_color = (0, 0, 0) if status == "INCONCLUSIVE" else (255, 255, 255)
        cv2.putText(dashboard, badge_text, (panel_x + 20, 665),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.72, text_color, 2, cv2.LINE_AA)

        return dashboard

    def process(self, image_path: str, output_dir: str = "output") -> dict:
        """Executes the complete end-to-end CV algorithm."""
        os.makedirs(output_dir, exist_ok=True)
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Cannot read image file at: {image_path}")

        cv2.imwrite(os.path.join(output_dir, "01_input.jpg"), image)

        # 1. Quality Control
        q_ok, blur, bright, q_msg = self.check_quality(image)
        if not q_ok:
            result = {
                "status": "INCONCLUSIVE",
                "reason": f"IMAGE_QUALITY_FAIL ({q_msg})",
                "deltaE00": 999.0,
                "blurScore": round(blur, 2),
                "brightness": round(bright, 2),
                "markersFound": 0
            }
            with open(os.path.join(output_dir, "result.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            return result

        # 2. ArUco Marker Detection
        found_markers, corners, ids = self.detect_markers(image)
        if corners and ids is not None:
            debug_aruco = image.copy()
            cv2.aruco.drawDetectedMarkers(debug_aruco, corners, ids)
            cv2.imwrite(os.path.join(output_dir, "02_aruco_detected.jpg"), debug_aruco)

        if len(found_markers) < 4:
            result = {
                "status": "INCONCLUSIVE",
                "reason": f"CARD_NOT_FOUND (Found {len(found_markers)} of 4 markers)",
                "deltaE00": 999.0,
                "blurScore": round(blur, 2),
                "brightness": round(bright, 2),
                "markersFound": len(found_markers)
            }
            with open(os.path.join(output_dir, "result.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            return result

        # 3. Perspective Rectification
        warped, M_homography = self.warp_card(image, found_markers)
        cv2.imwrite(os.path.join(output_dir, "03_warped.jpg"), warped)

        # 4. Patch & Reaction Zone Extraction
        ref_bgrs = []
        for r in self.cfg["reference_rois"]:
            rx, ry, rw, rh = map(int, r)
            patch = warped[ry:ry + rh, rx:rx + rw]
            ref_bgrs.append(self.extract_robust_bgr(patch))

        target_bgrs = [np.array(b, dtype=np.float64) for b in self.cfg["reference_target_bgr"]]

        tx, ty, tw, th = map(int, self.cfg["test_roi"])
        test_patch = warped[ty:ty + th, tx:tx + tw]
        raw_test_bgr = self.extract_robust_bgr(test_patch)

        # 5. Color Correction Matrix (CCM) Calibration
        M_ccm = self.solve_ccm(ref_bgrs, target_bgrs)
        calibrated_test_bgr = self.apply_ccm(raw_test_bgr, M_ccm)

        # 6. CIELAB Transformation & CIEDE2000 Distance
        observed_lab = self.bgr_to_lab(calibrated_test_bgr)
        delta_e = self.ciede2000(observed_lab, self.target_lab)

        # 7. Tri-State Classification
        cls_cfg = self.cfg["classification"]
        if delta_e <= cls_cfg["positive_max_de00"]:
            status = "POSITIVE"
            reason = "DELTA_E_WITHIN_POSITIVE_THRESHOLD"
        elif delta_e >= cls_cfg["negative_min_de00"]:
            status = "NEGATIVE"
            reason = "DELTA_E_EXCEEDS_NEGATIVE_THRESHOLD"
        else:
            status = "INCONCLUSIVE"
            reason = "BORDERLINE_DELTA_E_RANGE"

        # 8. Visual ROI Artifact
        roi_vis = warped.copy()
        for idx, r in enumerate(self.cfg["reference_rois"]):
            rx, ry, rw, rh = map(int, r)
            cv2.rectangle(roi_vis, (rx, ry), (rx + rw, ry + rh), (0, 255, 0), 2)
            cv2.putText(roi_vis, f"CAL {idx+1}", (rx + 5, ry + 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.rectangle(roi_vis, (tx, ty), (tx + tw, ty + th), (0, 0, 255), 3)
        cv2.putText(roi_vis, "TEST ZONE", (tx + 10, ty + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imwrite(os.path.join(output_dir, "04_rois.jpg"), roi_vis)

        # Compute nominal target BGR for the dashboard swatch
        px_target_lab = np.array([[[self.target_lab[0], self.target_lab[1], self.target_lab[2]]]], dtype=np.float32)
        nominal_target_bgr = cv2.cvtColor(px_target_lab, cv2.COLOR_Lab2BGR)[0, 0] * 255.0

        result = {
            "status": status,
            "reason": reason,
            "deltaE00": round(float(delta_e), 3),
            "observedLab": [round(float(v), 3) for v in observed_lab],
            "targetLab": [round(float(v), 3) for v in self.target_lab],
            "observedBgrRaw": [round(float(v), 1) for v in raw_test_bgr],
            "observedBgrCalibrated": [round(float(v), 1) for v in calibrated_test_bgr],
            "blurScore": round(blur, 2),
            "brightness": round(bright, 2),
            "markersFound": len(found_markers),
            "artifacts": {
                "input": os.path.join(output_dir, "01_input.jpg"),
                "aruco": os.path.join(output_dir, "02_aruco_detected.jpg"),
                "warped": os.path.join(output_dir, "03_warped.jpg"),
                "rois": os.path.join(output_dir, "04_rois.jpg"),
                "dashboard": os.path.join(output_dir, "05_analysis_dashboard.jpg")
            }
        }

        # 9. Generate Executive Analysis Dashboard
        dashboard = self.create_analysis_dashboard(roi_vis, test_patch, raw_test_bgr,
                                                   calibrated_test_bgr, nominal_target_bgr, result)
        cv2.imwrite(os.path.join(output_dir, "05_analysis_dashboard.jpg"), dashboard)

        with open(os.path.join(output_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        return result


def print_banner(res: dict, img_path: str):
    print("\n" + "=" * 65)
    print("           KAVACH CV PROTOCOL - TEST EXECUTION REPORT")
    print("=" * 65)
    print(f" Input Image       : {img_path}")
    print(f" Classification    : {res['status']}")
    print(f" Diagnostic Reason : {res.get('reason', 'N/A')}")
    print(f" Delta E00 (dE00)  : {res.get('deltaE00', 'N/A')}")
    if 'observedLab' in res:
        print(f" Observed Lab      : {res['observedLab']}")
        print(f" Target Lab        : {res['targetLab']}")
        print(f" Calibrated BGR    : {res['observedBgrCalibrated']}")
    print(f" Image Quality     : Blur={res['blurScore']} | Brightness={res['brightness']}")
    print(f" Markers Detected  : {res['markersFound']} / 4")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="KAVACH Phase-1 Standalone CV Pipeline")
    parser.add_argument("image", nargs="?", default=None, help="Path to input camera JPG/PNG")
    parser.add_argument("--config", default="config.json", help="Path to configuration JSON")
    parser.add_argument("--output", default="output", help="Directory for visual debug outputs")
    parser.add_argument("--demo", action="store_true", help="Run quick prototype demo on tests/sample_positive.jpg")
    args = parser.parse_args()

    pipeline = KavachPipeline(args.config)

    if args.demo or args.image is None:
        sample_img = os.path.join("tests", "sample_positive.jpg")
        if not os.path.exists(sample_img):
            print("Generating sample cards first...")
            from generate_demo_cards import generate_all_samples
            generate_all_samples(args.config, "tests")
        image_to_run = sample_img
    else:
        image_to_run = args.image

    result = pipeline.process(image_to_run, args.output)
    print_banner(result, image_to_run)
    print(f"Detailed artifacts written to directory: {os.path.abspath(args.output)}\n")


if __name__ == "__main__":
    main()
