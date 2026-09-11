"""
Phase 2 - Frame Extraction & Preprocessing
RoadSense AI - Member 1 (Vision & Data)

Plan requirements (section 7):
  - Configurable extraction interval, 1 FPS default.
  - Use ACTUAL frame timestamps, not an assumed constant-FPS calculation.
  - Laplacian-variance blur check; flag low-quality frames, don't delete them.
  - Log total processed frames and count flagged as low quality.

Run:
    python3 extract_frames.py <video_path> [--interval 1.0] [--out data/processed/frames]
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import cv2

DEFAULT_BLUR_THRESHOLD = 100.0  # Laplacian variance below this = flagged as blurry


@dataclass
class FrameRecord:
    frame_number: int          # original frame index in the source video
    saved_index: int           # sequential index among *extracted* frames
    timestamp_sec: float       # actual timestamp from the video (cv2 CAP_PROP_POS_MSEC / 1000)
    filename: str
    laplacian_variance: float
    is_blurry: bool

    def to_dict(self) -> dict:
        return asdict(self)


def laplacian_variance(frame) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def extract_frames(video_path: Path, out_dir: Path, interval_sec: float = 1.0,
                    blur_threshold: float = DEFAULT_BLUR_THRESHOLD) -> dict:
    """
    Extracts frames at `interval_sec` using actual timestamps (not just
    frame_count // fps math), flags blurry frames, and writes:
      - JPEGs into out_dir/frames/
      - a manifest CSV into out_dir/frame_manifest.csv
      - a summary dict (also written as out_dir/extraction_summary.json)
    """
    video_path = Path(video_path)
    out_dir = Path(out_dir)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    source_fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    total_source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    records: list[FrameRecord] = []
    saved_index = 0
    next_target_time = 0.0
    frame_number = -1

    while True:
        ok = cap.grab()
        if not ok:
            break
        frame_number += 1

        # Actual timestamp for this frame, from the container itself.
        timestamp_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        if timestamp_sec + 1e-6 < next_target_time:
            continue  # not yet time to sample this interval

        ok, frame = cap.retrieve()
        if not ok:
            continue

        var = laplacian_variance(frame)
        is_blurry = var < blur_threshold

        filename = f"frame_{saved_index:05d}.jpg"
        cv2.imwrite(str(frames_dir / filename), frame)

        records.append(FrameRecord(
            frame_number=frame_number,
            saved_index=saved_index,
            timestamp_sec=round(timestamp_sec, 3),
            filename=filename,
            laplacian_variance=round(var, 2),
            is_blurry=is_blurry,
        ))

        saved_index += 1
        next_target_time += interval_sec

    cap.release()

    # Manifest CSV
    manifest_path = out_dir / "frame_manifest.csv"
    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "frame_number", "saved_index", "timestamp_sec",
            "filename", "laplacian_variance", "is_blurry",
        ])
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())

    n_blurry = sum(1 for r in records if r.is_blurry)
    summary = {
        "video_filename": video_path.name,
        "source_fps": round(source_fps, 3),
        "source_total_frames": total_source_frames,
        "extraction_interval_sec": interval_sec,
        "blur_threshold": blur_threshold,
        "frames_extracted": len(records),
        "frames_flagged_blurry": n_blurry,
        "frames_dir": str(frames_dir),
        "manifest_csv": str(manifest_path),
    }

    summary_path = out_dir / "extraction_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    return summary


def main():
    parser = argparse.ArgumentParser(description="Phase 2 frame extraction")
    parser.add_argument("video_path", help="Path to source video")
    parser.add_argument("--interval", type=float, default=1.0,
                         help="Sampling interval in seconds (default: 1.0 = 1 FPS)")
    parser.add_argument("--out", default="data/processed/frames_output",
                         help="Output directory for frames + manifest")
    parser.add_argument("--blur-threshold", type=float, default=DEFAULT_BLUR_THRESHOLD,
                         help="Laplacian variance below this is flagged as blurry")
    args = parser.parse_args()

    summary = extract_frames(
        Path(args.video_path), Path(args.out),
        interval_sec=args.interval, blur_threshold=args.blur_threshold,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
