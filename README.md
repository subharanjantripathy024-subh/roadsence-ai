# RoadSense AI — Member 1: Vision & Data

Hackathon: PARAKRAM 1.0 | Problem Statement: PK01PS001
Module: Video Processing, GPS Detection & YOLOv8 Road-Damage Detection

This is the working repo for your part of the pipeline: **GPS detection →
frame extraction → YOLOv8 detection → `detections_raw.csv` → handoff to
Member 2.**

## Status

| Phase | Status |
|---|---|
| 0 — Environment setup | ✅ Done — see `logs/environment_report.json` |
| 1 — GPS availability detection | ✅ Done & tested (all 3 branches) |
| 2 — Frame extraction & preprocessing | ✅ Done & tested |
| 3 — YOLOv8 training & inference | ⬜ Not started — **you are here** |
| Validation | ⬜ Not started |
| Integration/handoff | ⬜ Not started |

## What's built so far

### Phase 0 — `backend/src/vision/check_environment.py`
Checks for ffmpeg/ffprobe/tesseract binaries, required Python packages, and
GPU availability. Logs a report to `logs/environment_report.json` so later
phases know whether to train on GPU or fall back to a lighter CPU config
(this machine currently has **no GPU** — plan for `yolov8n`, small image
size, or a free Colab/Kaggle GPU for the actual training run).

```bash
python3 backend/src/vision/check_environment.py
```

### Phase 1 — `backend/src/vision/gps_detector.py`
Implements the exact decision flow from the plan:

1. Check embedded GPS metadata via `ffprobe` (parses ISO 6709 location tags).
2. If absent, sample frames and run OCR (`pytesseract`) on the region
   where dashcam overlays usually sit, looking for `lat/long`-style text.
3. If neither exists → `location_status = "gps_unavailable"` — the video
   still proceeds, just without coordinates. **No coordinates are ever
   invented or borrowed from another video.**

```bash
python3 backend/src/vision/gps_detector.py path/to/video.mp4
```

Returns JSON like:
```json
{
  "video_filename": "video_with_overlay.mp4",
  "location_status": "overlay_ocr",
  "source": "ocr:frame_0:bottom_strip",
  "latitude": 19.076,
  "longitude": 72.8777,
  "raw_value": "LAT 19.076000 LON 72.877700",
  "confidence": "low",
  "notes": "Parsed from OCR on burned-in overlay text; verify against raw OCR output."
}
```

### Phase 2 — `backend/src/vision/extract_frames.py`
Pulls frames at a configurable interval (1s / 1 FPS default) using the
video's **actual timestamps** (not a naive `frame_count / fps` guess),
runs a Laplacian-variance blur check on every extracted frame, and writes:

- `frames/frame_00000.jpg`, `frame_00001.jpg`, ... — the extracted JPEGs
- `frame_manifest.csv` — frame_number, saved_index, timestamp_sec, filename, laplacian_variance, is_blurry
- `extraction_summary.json` — counts of total vs. flagged-blurry frames

```bash
python3 backend/src/vision/extract_frames.py path/to/video.mp4 --interval 1.0 --out data/processed/frames_output
```

Blurry frames are **flagged, not deleted** — per the plan, downstream
phases decide whether to use them.

### `backend/src/vision/make_test_videos.py`
You said you weren't sure what data you have yet — this generates 3 tiny
synthetic test videos so the GPS module (and later, frame extraction) can
be verified **right now** without waiting on the real demo footage:

- `video_with_overlay.mp4` — burned-in GPS text → tests OCR branch
- `video_no_gps.mp4` — nothing → tests `gps_unavailable` branch
- `video_with_metadata.mp4` — embedded location tag → tests metadata branch

All three currently pass. Swap in the real demo dashcam video once you have
it — the module doesn't change.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 backend/src/vision/check_environment.py
```

System binaries needed (already present in this environment; on your own
machine install via apt/brew): `ffmpeg`, `ffprobe`, `tesseract-ocr`.

## Datasets you'll need (Phase 3)

You said you're not sure what you have yet — here's where to get each one
from the plan:

- **RDD2022** (train/fine-tune, classes D00/D10/D20/D40):
  Official repo & download: https://github.com/sekilab/RoadDamageDetector
  Mirror on Figshare: https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547
  Kaggle mirror: https://www.kaggle.com/datasets/aliabdelmenam/rdd-2022

- **BharatPotHole** (Indian dashcam pothole examples, merge into pothole class):
  https://www.kaggle.com/datasets/surbhisaswatimohanty/bharatpothole

- **Pothole Detection — VOC** (OOD validation only, never train on this):
  https://public.roboflow.com/object-detection/pothole
  (Roboflow lets you export it directly in Pascal VOC or YOLO format.)

- **Demo dashcam video**: your own footage with a real burned-in GPS/speed
  overlay, per the plan (section 5.4). Drop it in `data/raw/demo_clip/`.

Put each dataset under its matching folder in `data/raw/` (see folder
structure below) once downloaded.

## Folder structure

```
roadsense-ai/
├── data/
│   ├── raw/
│   │   ├── rdd2022/
│   │   ├── bharatpothole/
│   │   ├── pothole_voc/
│   │   └── demo_clip/          (synthetic test videos live here for now)
│   └── processed/
│       └── detections_raw.csv  (Phase 3 output — not generated yet)
├── models/                     (trained weights go here — Phase 3)
├── backend/src/vision/
│   ├── check_environment.py    (Phase 0)
│   ├── gps_detector.py         (Phase 1)
│   └── make_test_videos.py     (test fixtures)
├── logs/
│   └── environment_report.json
├── requirements.txt
└── README.md
```

## Output contract with Member 2

`data/processed/detections_raw.csv` (Phase 3, not yet generated) will follow:

```
frame_number, timestamp, x1, y1, x2, y2, damage_class, confidence
```

Don't change this schema without telling the team — Member 2 builds their
severity/dedup/prioritization logic against it.

## Next steps (in order)

1. **Get real data**: download RDD2022 + BharatPotHole (Phase 3 training
   data) and your own demo dashcam clip. Grab the Pascal VOC pothole set
   separately for OOD validation only.
2. **Phase 3 — YOLOv8**: fine-tune on RDD2022 + BharatPotHole (once
   downloaded), run inference on demo-video frames, write
   `detections_raw.csv`. This is the heaviest phase — needs a GPU (Colab/
   Kaggle free tier is fine) since this machine has none.
3. **Validation**: evaluate RDD2022 holdout and Pascal VOC OOD set
   *separately* — don't average them, the plan is explicit about this.
4. **Handoff**: push to `member1-vision` branch, open a PR, notify Member 2.

## Continuing in Antigravity

Everything above is committed to disk and ready to open as a folder
project. Suggested first prompt once you open it there:

> "This is the RoadSense AI Member-1 vision module. Phases 0-2 (env check,
> GPS detection, frame extraction) are done and tested — see README.md for
> status. I need Phase 3: download RDD2022 and BharatPotHole into
> `data/raw/`, convert annotations to YOLO format, write a training script
> for `backend/src/vision/`, fine-tune YOLOv8 on the merged classes
> (D00/D10/D20/D40 + pothole), and run inference on the demo video's
> extracted frames to produce `data/processed/detections_raw.csv` matching
> the schema in the README."

A few things worth telling Antigravity up front, since it'll have its own
environment:
- No GPU was available in this environment — check for one there, or plan
  to train on Colab/Kaggle and pull the weights back in.
- `pymediainfo` and `gpxpy` are in `requirements.txt` but weren't exercised
  yet (ffprobe covered metadata for the test cases) — fine to keep or drop.
- Keep the `detections_raw.csv` schema exactly as documented — Member 2 is
  building against it.
