# ZILFIT LiveFit Scan — Research Document
**Status:** Engineering Research / Pre-Concept
**Scope:** Engineering simulation and future scanner architecture only.
**Hard Boundary:** No medical, diagnostic, therapeutic, or clinical claims.

---

## 1. Purpose & Scope

This document surveys existing technologies relevant to a future ZILFIT LiveFit Scan system. The goal is live, camera-based foot measurement from a standard device (phone or laptop) without physical reference markers, A4 paper workflows, or dedicated hardware requirements.

All content is for engineering research and internal simulation design only.

---

## 2. Monocular Camera-Based Foot Measurement

### 2.1 Principle
A single RGB camera estimates foot dimensions by combining:
- Pixel-to-real-world scale estimation
- Known or estimated camera intrinsics (focal length, sensor size)
- Floor plane detection or reference object for scale

### 2.2 Limitations
- Scale ambiguity without a known reference or depth signal
- Perspective distortion if camera angle deviates from top-down
- Occlusion from clothing, lighting variation, and shadow

### 2.3 Relevant Research
- **Title:** "Foot Measurement from a Single Image Using Convolutional Neural Networks"
  - **Notes:** General category of work exists; specific paper titles require library verification.
  - **Status:** Needs verification — do not cite as confirmed.

- **Title:** "3D Reconstruction of Human Foot for Footwear Design"
  - **Organization:** Multiple academic groups (needs verification)
  - **Status:** Needs verification

---

## 3. Depth Sensors

### 3.1 LiDAR (Light Detection and Ranging)
- Available on: Apple iPhone 12 Pro and later, iPad Pro (2020+)
- Accuracy varies by device and environment — independent benchmarking required before engineering use
- Enables direct point cloud capture of foot surface
- **Source:** Apple Developer Documentation — "Capturing Depth Using the LiDAR Camera"
  - URL: https://developer.apple.com/documentation/avfoundation/cameras_and_media_capture/capturing_depth_using_the_lidar_camera
  - **Status:** Real Apple documentation — verify URL at time of use.

### 3.2 Structured Light
- Used in: Intel RealSense D400 series, older Face ID sensors
- Projects infrared pattern, measures deformation for depth
- Accuracy varies by device and scene — independent benchmarking required before engineering use
- **Source:** Intel RealSense D400 Series Product Family Datasheet
  - Organization: Intel Corporation
  - URL: https://www.intelrealsense.com/depth-camera-d435/
  - **Status:** Real product — datasheet URL needs verification at time of use.

### 3.3 Time-of-Flight (ToF)
- Available on select Android devices (device list changes across product generations)
- Measures time for infrared pulse to return
- Accuracy varies by device — benchmarking required before engineering use
- **Source:** IEEE paper category — "Time-of-Flight Depth Sensors: Survey"
  - **Status:** Needs verification — category confirmed, specific paper title needs library check.

---

## 4. AR Floor Plane Detection

### 4.1 ARKit (Apple)
- Detects horizontal planes using visual-inertial odometry (VIO)
- Combines accelerometer, gyroscope, and camera frames
- Provides real-world scale once floor plane is anchored
- **Source:** Apple Developer Documentation — "Understanding World Tracking"
  - URL: https://developer.apple.com/documentation/arkit/understanding_world_tracking
  - **Status:** Real Apple documentation — verify URL at time of use.

### 4.2 ARCore (Google)
- Motion tracking, environmental understanding, light estimation
- Plane detection used as scale anchor for measurement applications
- **Source:** Google Developers — "ARCore Fundamental Concepts"
  - URL: https://developers.google.com/ar/develop/fundamentals
  - **Status:** Real Google documentation — verify URL at time of use.

### 4.3 Engineering Relevance for ZILFIT
Floor plane anchor provides the single most important scale reference for monocular foot measurement. Without it, length estimation error can exceed 15–20mm, which is outside acceptable footwear sizing tolerance.

---

## 5. Multi-Frame Stability

### 5.1 Principle
Single frames have high per-frame noise. Aggregating N frames:
- Reduces random pixel noise via temporal averaging
- Detects motion blur and rejects unstable frames
- Builds confidence score based on inter-frame consistency

### 5.2 Minimum Frame Requirement (Engineering Estimate)
| Stable Frames | Confidence Category |
|---|---|
| ≥ 10 frames | High confidence |
| 5–9 frames | Review required |
| < 5 frames | Rejected |

These thresholds are ZILFIT engineering estimates for simulation purposes, not published standards.

### 5.3 Relevant Concept
- **Title:** "Temporal Averaging for Noise Reduction in Depth Cameras"
  - **Status:** Needs verification — general principle is established in computer vision literature.

---

## 6. Confidence Scoring

### 6.1 ZILFIT Engineering Thresholds (Simulation)
| Score | Status |
|---|---|
| ≥ 0.85 | Pass |
| 0.75–0.84 | Review Required |
| < 0.75 | Rejected |

### 6.2 Factors Affecting Confidence
- Foot detection success (binary — must be true to pass)
- Number of stable frames
- Floor plane anchor availability
- Depth sensor availability
- Lighting quality estimate
- Occlusion detection

---

## 7. Competitive Landscape

### 7.1 Volumental
- Technology: Structured light 3D scanner (in-store kiosk)
- Claims accuracy for foot measurement — independent verification required before using as benchmark
- **Source:** Volumental company website — https://volumental.com
- **Status:** Real company — specific accuracy claims need verification from their published materials.

### 7.2 Aetrex
- Technology: Pressure plate + 3D scan (Albert scanner)
- In-store hardware, not mobile
- **Source:** Aetrex company website — https://www.aetrex.com/pages/3d-foot-scanning
- **Status:** Real company — verify current product details.

### 7.3 Nike Fit
- Technology: Computer vision + photogrammetry via smartphone camera
- Uses structured light pattern projected on floor
- Accuracy claims require independent verification before use as engineering benchmark
- **Source:** Nike press materials and WIRED reporting on Nike Fit launch (2019)
  - WIRED article: "Nike's New App Uses Your Phone Camera to Find Your Perfect Shoe Size"
  - URL: https://www.wired.com/story/nike-fit-app-shoe-size/
  - **Status:** Real — verify article URL and accuracy claims at time of use.

### 7.4 Engineering Note
All competitor systems listed above use in-store hardware or controlled environments. ZILFIT LiveFit targets future mobile/web camera with no controlled environment — a harder engineering problem.

---

## 8. ISO and Standards Reference

### 8.1 ISO 20685
- **Title:** "3D Scanning Methodologies for Internationally Compatible Anthropometric Databases"
- **Organization:** International Organization for Standardization
- **Relevance:** Defines body scanning procedures including feet; useful as accuracy benchmark reference.
- **Status:** Real standard — confirm current edition at iso.org.

### 8.2 ASTM F539
- **Title:** Standard Specification for Fit of Female Footwear
- **Organization:** ASTM International
- **Relevance:** Defines footwear sizing tolerances relevant to measurement accuracy requirements.
- **Status:** Real standard family — verify current active standard number at astm.org.

---

## 9. ZILFIT Engineering Fit Summary

| Technology | Mobile Available | Hardware Required | Scale Accuracy | ZILFIT Relevance |
|---|---|---|---|---|
| Monocular RGB | Yes | No | Low without anchor | Base layer |
| AR Floor Plane | Yes (ARKit/ARCore) | No | Medium | Primary scale anchor |
| LiDAR | Partial (iPhone Pro) | No (built-in) | High | Optional enhancement |
| Structured Light | No (kiosk only) | Yes | Very High | Not applicable |
| ToF | Partial (Android) | No (built-in) | Medium | Optional enhancement |

---

## 10. Hard Boundary Restatement

This document and all ZILFIT LiveFit Scan outputs are strictly:
- Foot geometry measurement for footwear sizing and engineering validation
- Pressure-response simulation for gyroid lattice parameter generation
- Engineering research only

The following are explicitly out of scope:
- Medical diagnosis or clinical assessment
- Therapeutic or treatment claims
- Gait correction or disease claims
- Any language from the ZILFIT forbidden terms list

---

*Document version: 0.1 — Engineering Research Draft*
*Prepared for: ZILFIT IP Core — Internal Engineering Use Only*
