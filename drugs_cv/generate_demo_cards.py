"""
KAVACH Phase-1 CV Demo: Test Card Generator
Generates realistic test card images with ArUco markers, reference calibration patches,
and chemical reaction test zones for algorithm validation outside mobile hardware.
"""

import os
import json
import cv2
import numpy as np


def create_base_card(test_bgr: tuple, test_label: str, cfg: dict) -> np.ndarray:
    W = int(cfg["warp_width"])
    H = int(cfg["warp_height"])

    # High-quality card surface with neutral card stock texture
    card = np.full((H, W, 3), 246, dtype=np.uint8)

    # Card border and header branding
    cv2.rectangle(card, (30, 30), (W - 30, H - 30), (45, 45, 45), 3)
    cv2.rectangle(card, (34, 34), (W - 34, H - 34), (220, 220, 220), 2)
    cv2.putText(card, "KAVACH FORENSIC RAPID TEST CARD", (220, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.95, (30, 30, 30), 2, cv2.LINE_AA)
    cv2.putText(card, "STANDALONE DESKTOP TEST HARNESS [PHASE-1 PROTOTYPE]", (240, 105),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 100, 100), 1, cv2.LINE_AA)

    # Reference Color Patches
    ref_rois = cfg["reference_rois"]
    ref_bgrs = cfg["reference_target_bgr"]
    ref_names = ["CAL 1 (Dark)", "CAL 2 (Mid)", "CAL 3 (Warm)", "CAL 4 (Cool)"]

    for (rx, ry, rw, rh), bgr, name in zip(ref_rois, ref_bgrs, ref_names):
        bgr_color = [int(c) for c in bgr]
        cv2.rectangle(card, (rx, ry), (rx + rw, ry + rh), bgr_color, -1)
        cv2.rectangle(card, (rx, ry), (rx + rw, ry + rh), (30, 30, 30), 2)
        cv2.putText(card, name, (rx + 5, ry - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (60, 60, 60), 1, cv2.LINE_AA)

    # Test Reagent Reaction Zone
    tx, ty, tw, th = map(int, cfg["test_roi"])
    cv2.rectangle(card, (tx, ty), (tx + tw, ty + th), [int(c) for c in test_bgr], -1)
    cv2.rectangle(card, (tx, ty), (tx + tw, ty + th), (25, 25, 25), 3)
    cv2.putText(card, f"REAGENT: {test_label}", (tx + 15, ty + th // 2 + 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.70, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(card, "CHEMICAL REACTION ZONE", (tx + 20, ty - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (50, 50, 50), 1, cv2.LINE_AA)

    # Add ArUco Markers
    dict_name = getattr(cv2.aruco, cfg["dictionary"])
    dictionary = cv2.aruco.getPredefinedDictionary(dict_name)
    marker_size = 90

    marker_positions = {
        cfg["marker_ids"]["top_left"]: (70, 70),
        cfg["marker_ids"]["top_right"]: (850, 70),
        cfg["marker_ids"]["bottom_right"]: (850, 570),
        cfg["marker_ids"]["bottom_left"]: (70, 570)
    }

    for mid, (mx, my) in marker_positions.items():
        marker_img = cv2.aruco.generateImageMarker(dictionary, mid, marker_size)
        marker_bgr = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)
        card[my:my + marker_size, mx:mx + marker_size] = marker_bgr
        cv2.rectangle(card, (mx - 2, my - 2), (mx + marker_size + 2, my + marker_size + 2), (80, 80, 80), 1)

    return card


def generate_all_samples(config_path: str = "config.json", output_dir: str = "tests"):
    os.makedirs(output_dir, exist_ok=True)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # 1. Sample Positive: Drug reacted color (deep red/magenta: BGR [70, 75, 175])
    pos_card = create_base_card((70, 75, 175), "POSITIVE REACTION", cfg)
    cv2.imwrite(os.path.join(output_dir, "sample_positive.jpg"), pos_card)
    print(f"Generated: {os.path.join(output_dir, 'sample_positive.jpg')}")

    # 2. Sample Negative: Unreacted reagent (pale yellow/clear: BGR [180, 240, 245])
    neg_card = create_base_card((180, 240, 245), "NO REACTION", cfg)
    cv2.imwrite(os.path.join(output_dir, "sample_negative.jpg"), neg_card)
    print(f"Generated: {os.path.join(output_dir, 'sample_negative.jpg')}")

    # 3. Sample Inconclusive: Borderline / weak reagent (BGR [110, 115, 160])
    inc_card = create_base_card((110, 115, 160), "BORDERLINE", cfg)
    cv2.imwrite(os.path.join(output_dir, "sample_inconclusive.jpg"), inc_card)
    print(f"Generated: {os.path.join(output_dir, 'sample_inconclusive.jpg')}")

    # 4. Realistic Camera Capture with Tilt and Lighting Vignette
    W, H = int(cfg["warp_width"]), int(cfg["warp_height"])
    # Put card onto a textured desk background
    bg_w, bg_h = 1400, 1050
    desk = np.full((bg_h, bg_w, 3), (210, 205, 200), dtype=np.uint8)
    # Add mild wood texture / noise
    noise = np.random.normal(0, 4, (bg_h, bg_w, 3)).astype(np.int16)
    desk = np.clip(desk.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Perspective quad transformation simulating smartphone held at 15-degree tilt
    src_pts = np.array([[0, 0], [W, 0], [W, H], [0, H]], dtype=np.float32)
    dst_pts = np.array([[180, 120], [1220, 170], [1160, 940], [140, 910]], dtype=np.float32)
    M_homography = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_card = cv2.warpPerspective(pos_card, M_homography, (bg_w, bg_h))

    # Mask card into background
    mask = cv2.warpPerspective(np.full((H, W), 255, dtype=np.uint8), M_homography, (bg_w, bg_h))
    tilted_scene = desk.copy()
    tilted_scene[mask > 0] = warped_card[mask > 0]

    # Add realistic lighting gradient (sunlight from top-left)
    y_grad, x_grad = np.ogrid[:bg_h, :bg_w]
    gradient = 1.05 - 0.15 * ((x_grad / bg_w) + (y_grad / bg_h)) / 2.0
    gradient = np.repeat(gradient[:, :, np.newaxis], 3, axis=2)
    tilted_scene = np.clip(tilted_scene.astype(np.float64) * gradient, 0, 255).astype(np.uint8)

    cv2.imwrite(os.path.join(output_dir, "sample_tilted_camera.jpg"), tilted_scene)
    print(f"Generated: {os.path.join(output_dir, 'sample_tilted_camera.jpg')}")

    # 5. Out-of-Focus / Blurry Sample to test Image Quality rejection
    blurry = cv2.GaussianBlur(pos_card, (45, 45), 18.0)
    cv2.imwrite(os.path.join(output_dir, "sample_blurry.jpg"), blurry)
    print(f"Generated: {os.path.join(output_dir, 'sample_blurry.jpg')}")

    print("\nAll 5 demo test cards generated successfully.")


if __name__ == "__main__":
    generate_all_samples()
