# KAVACH Team A (CV / C++) Standalone Prototype & Test Harness

This package fulfills the Team A mandate:
> **Build and test the C++ OpenCV algorithm completely outside Flutter using a standalone C++ desktop test harness or Python.**
> **They don't need Flutter or mobile hardware. They feed sample camera `.jpg` files directly into their C++ function.**

---

## 🎯 Architecture & Pipeline Stages

```text
Input Camera JPG (Mobile Capture)
  │
  ▼
Stage 1: Image Quality Assurance
  ├── Blur Detection via Laplacian Variance (Threshold >= 45.0)
  └── Luminance Verification (35.0 <= Brightness <= 238.0)
  │
  ▼
Stage 2: ArUco Fiducial Marker Detection
  ├── Dictionary: DICT_4X4_50
  └── Card Corner Markers: TL (10), TR (20), BR (30), BL (40)
  │
  ▼
Stage 3: Homography Perspective Correction
  └── 4-point homography warp to canonical 1000x700 resolution
  │
  ▼
Stage 4: Glare-Resistant Robust ROI Extraction
  ├── Reference Color Swatches (4 patches across spectrum)
  └── Chemical Reagent Test Zone (Trimmed-mean 10%-90% channel filtering)
  │
  ▼
Stage 5: Least-Squares Color Correction Matrix (CCM)
  └── Solves M * Observed = Target via Moore-Penrose Pseudo-Inverse / SVD
  │
  ▼
Stage 6: CIELAB Color Transformation & CIEDE2000 Calculation
  └── Computes ISO/CIE 11664-6 perceptual color distance (ΔE00)
  │
  ▼
Stage 7: Tri-State Classification & Artifact Generation
  ├── POSITIVE (ΔE00 <= 8.0)
  ├── NEGATIVE (ΔE00 >= 15.0)
  └── INCONCLUSIVE (Borderline ΔE00 or Quality Reject)
```

---

## 🚀 Quick Start for Tomorrow's Prototype Demo

### Option 1: One-Click Execution (Fastest for presentation)
- **Live Demo**: Double-click `run_demo.bat`
- **Full Test Suite**: Double-click `run_tests.bat`

### Option 2: Running via Command Line (PowerShell)
```powershell
# 1. Run algorithm on any JPG image
python kavach_cv.py tests\sample_positive.jpg --output output\demo

# 2. Run the automated test matrix
python test_harness.py

# 3. Test your own custom photo
python kavach_cv.py "C:\path\to\your_photo.jpg" --output output\my_test
```

---

## 📊 Sample Test Matrix (Included)

| Test Sample | Image File | Description | Expected | Verified Result |
| :--- | :--- | :--- | :--- | :--- |
| **Positive Reagent** | `tests/sample_positive.jpg` | Drug reacted color (deep red/magenta) | `POSITIVE` | **PASS (ΔE00 = 3.53)** |
| **Negative Reagent** | `tests/sample_negative.jpg` | Unreacted reagent (pale yellow/clear) | `NEGATIVE` | **PASS (ΔE00 = 52.32)** |
| **Inconclusive** | `tests/sample_inconclusive.jpg` | Borderline / weak color shift | `INCONCLUSIVE` | **PASS (ΔE00 = 13.06)** |
| **Tilted Mobile Angle**| `tests/sample_tilted_camera.jpg` | 15° perspective tilt + lighting vignette | `POSITIVE` | **PASS (ΔE00 = 2.84)** |
| **Blurry Capture** | `tests/sample_blurry.jpg` | Out-of-focus capture | `INCONCLUSIVE` | **PASS (Quality Reject)** |

---

## 📁 Output Artifacts Generated for Every Image

Every test run generates visual and machine-readable artifacts in `output/<name>/`:
- `01_input.jpg` — Original camera capture
- `02_aruco_detected.jpg` — Card corner fiducial markers annotated
- `03_warped.jpg` — Rectified card view in canonical space
- `04_rois.jpg` — Color reference patches and chemical test zone overlaid
- `05_analysis_dashboard.jpg` — Executive presentation dashboard with swatches, ΔE00 metrics, and classification badge
- `result.json` — Machine-readable structured output

---

## 💻 C++ Engine (`cpp/`)

For native deployment and future Flutter C++ FFI integration:
- `cpp/include/ciede2000.hpp` — Pure C++ header implementation of CIEDE2000 ΔE00.
- `cpp/include/kavach_pipeline.hpp` — Pipeline class declaration and data models.
- `cpp/src/kavach_pipeline.cpp` — Complete OpenCV C++ implementation matching Python.
- `cpp/src/main.cpp` — Standalone C++ test harness executable.
- `cpp/CMakeLists.txt` — Standard CMake project linking against pre-built OpenCV.
