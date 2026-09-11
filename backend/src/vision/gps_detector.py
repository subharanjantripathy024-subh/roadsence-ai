"""
Phase 1 - GPS Availability Detection
RoadSense AI - Member 1 (Vision & Data)

Decision flow (per project plan, section 6):

    Uploaded Video
        -> 1. Check embedded GPS metadata (ffprobe)
        -> 2. If absent, inspect burned-in GPS/speed overlay via OCR
        -> 3. If neither exists -> location_status = "gps_unavailable"
        -> Continue processing regardless

Hard rule: NEVER fabricate coordinates and NEVER borrow a GPS trace
from a different recording. If GPS can't be tied back to *this* video,
report gps_unavailable instead of guessing.

Run directly for a quick manual check:
    python3 gps_detector.py /path/to/video.mp4
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pytesseract

# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class GPSResult:
    video_filename: str
    location_status: str          # "embedded" | "overlay_ocr" | "gps_unavailable"
    source: Optional[str]         # e.g. "ffprobe:location" or "ocr:frame_12"
    latitude: Optional[float]
    longitude: Optional[float]
    raw_value: Optional[str]      # original string the value was parsed from
    confidence: Optional[str]     # "high" | "low" (OCR is inherently lower confidence)
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Step 1: Embedded metadata (ffprobe)
# --------------------------------------------------------------------------

# Common tag names containers use for GPS location.
_METADATA_GPS_TAGS = [
    "location", "location-eng", "com.apple.quicktime.location.iso6709",
    "GPSLatitude", "GPSLongitude", "gps", "xyz",
]

# ISO 6709 format, e.g. "+19.0760+072.8777/" (used by QuickTime/Apple "location" tag)
_ISO6709_RE = re.compile(r"([+\-]\d+\.\d+)([+\-]\d+\.\d+)")


def _parse_iso6709(value: str) -> Optional[tuple[float, float]]:
    match = _ISO6709_RE.search(value)
    if not match:
        return None
    lat, lon = float(match.group(1)), float(match.group(2))
    return lat, lon


def check_embedded_metadata(video_path: Path) -> Optional[GPSResult]:
    """Use ffprobe to inspect container/stream tags for GPS info."""
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        return None  # ffprobe not installed - caller falls through to OCR

    if proc.returncode != 0 or not proc.stdout:
        return None

    try:
        info = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None

    tag_sources = []
    fmt_tags = info.get("format", {}).get("tags", {})
    tag_sources.append(("format", fmt_tags))
    for stream in info.get("streams", []):
        tag_sources.append((f"stream:{stream.get('index')}", stream.get("tags", {})))

    for scope, tags in tag_sources:
        if not tags:
            continue
        for tag_name, tag_value in tags.items():
            if tag_name.lower() not in [t.lower() for t in _METADATA_GPS_TAGS]:
                continue
            parsed = _parse_iso6709(tag_value)
            if parsed:
                lat, lon = parsed
                return GPSResult(
                    video_filename=video_path.name,
                    location_status="embedded",
                    source=f"ffprobe:{scope}:{tag_name}",
                    latitude=lat,
                    longitude=lon,
                    raw_value=tag_value,
                    confidence="high",
                    notes="Parsed from embedded container/stream metadata.",
                )
    return None


# --------------------------------------------------------------------------
# Step 2: Burned-in overlay via OCR
# --------------------------------------------------------------------------

# Matches things like "Lat: 19.076000 Long: 72.877700", "19.0760, 72.8777",
# "LAT 19.0760 LON 72.8777", case-insensitive.
_OCR_COORD_PATTERNS = [
    re.compile(r"lat[a-z]*[:\s]+(-?\d{1,3}\.\d{3,8})[,\s]+lo?n[a-z]*[:\s]+(-?\d{1,3}\.\d{3,8})", re.I),
    re.compile(r"(-?\d{1,2}\.\d{4,8})\s*,\s*(-?\d{1,3}\.\d{4,8})"),
]


def _preprocess_for_ocr(frame: np.ndarray) -> np.ndarray:
    """Upscale + threshold to make small burned-in overlay text more readable."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def _sample_frame_indices(total_frames: int, n_samples: int) -> list[int]:
    if total_frames <= 0:
        return []
    n_samples = min(n_samples, total_frames)
    step = max(total_frames // n_samples, 1)
    return list(range(0, total_frames, step))[:n_samples]


def check_overlay_ocr(video_path: Path, n_samples: int = 8,
                       roi_fraction: float = 0.20) -> Optional[GPSResult]:
    """
    Sample frames from the video and run OCR on the region where dashcam
    overlays typically live (bottom strip). Falls back to full frame if
    the bottom-strip search finds nothing.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = _sample_frame_indices(total_frames, n_samples)

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue

        h, w = frame.shape[:2]
        roi_h = int(h * roi_fraction)
        regions_to_try = [
            ("bottom_strip", frame[h - roi_h:h, 0:w]),
            ("top_strip", frame[0:roi_h, 0:w]),
            ("full_frame", frame),
        ]

        for region_name, region in regions_to_try:
            processed = _preprocess_for_ocr(region)
            text = pytesseract.image_to_string(processed)
            if not text.strip():
                continue

            for pattern in _OCR_COORD_PATTERNS:
                match = pattern.search(text)
                if match:
                    lat, lon = float(match.group(1)), float(match.group(2))
                    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                        continue  # sanity check, avoid garbage OCR matches
                    cap.release()
                    return GPSResult(
                        video_filename=video_path.name,
                        location_status="overlay_ocr",
                        source=f"ocr:frame_{idx}:{region_name}",
                        latitude=lat,
                        longitude=lon,
                        raw_value=text.strip().replace("\n", " | "),
                        confidence="low",
                        notes="Parsed from OCR on burned-in overlay text; verify against raw OCR output.",
                    )

    cap.release()
    return None


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def detect_gps(video_path: str | Path) -> GPSResult:
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Step 1: embedded metadata
    result = check_embedded_metadata(video_path)
    if result:
        return result

    # Step 2: OCR overlay
    result = check_overlay_ocr(video_path)
    if result:
        return result

    # Step 3: neither source exists
    return GPSResult(
        video_filename=video_path.name,
        location_status="gps_unavailable",
        source=None,
        latitude=None,
        longitude=None,
        raw_value=None,
        confidence=None,
        notes="No embedded GPS metadata and no OCR-readable overlay found. "
              "Downstream detections will be identified by filename/frame/timestamp only.",
    )


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gps_detector.py <video_path>")
        sys.exit(1)

    result = detect_gps(sys.argv[1])
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
