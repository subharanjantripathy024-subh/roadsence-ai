"""
Creates 3 tiny synthetic videos so gps_detector.py can be verified
end-to-end without needing the real demo dashcam footage yet:

  1. video_with_overlay.mp4   -> burned-in "LAT 19.076000 LON 72.877700" text
                                  (tests the OCR overlay branch)
  2. video_no_gps.mp4         -> plain frames, no overlay, no metadata
                                  (tests the gps_unavailable branch)
  3. video_with_metadata.mp4  -> no visual overlay, but embedded location tag
                                  written via ffmpeg -metadata
                                  (tests the embedded-metadata branch)

Run:
    python3 make_test_videos.py
"""

import subprocess
from pathlib import Path

import cv2
import numpy as np

OUT_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "demo_clip"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT, FPS, SECONDS = 320, 240, 10, 2


def _write_plain_video(path: Path, overlay_text: str | None):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, FPS, (WIDTH, HEIGHT))
    for i in range(FPS * SECONDS):
        frame = np.full((HEIGHT, WIDTH, 3), (40, 40, 40), dtype=np.uint8)
        cv2.putText(frame, f"frame {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (200, 200, 200), 1, cv2.LINE_AA)
        if overlay_text:
            cv2.putText(frame, overlay_text, (5, HEIGHT - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        writer.write(frame)
    writer.release()


def make_overlay_video():
    path = OUT_DIR / "video_with_overlay.mp4"
    _write_plain_video(path, "LAT 19.076000 LON 72.877700")
    print(f"Created {path}")


def make_no_gps_video():
    path = OUT_DIR / "video_no_gps.mp4"
    _write_plain_video(path, overlay_text=None)
    print(f"Created {path}")


def make_metadata_video():
    """Write a plain video, then remux with ffmpeg to inject a location tag."""
    plain_path = OUT_DIR / "_tmp_plain_for_metadata.mp4"
    final_path = OUT_DIR / "video_with_metadata.mp4"
    _write_plain_video(plain_path, overlay_text=None)

    # ISO 6709 location string: Mumbai approx coordinates
    iso6709_location = "+19.0760+072.8777/"

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(plain_path),
         "-metadata", f"location={iso6709_location}",
         "-codec", "copy", str(final_path)],
        capture_output=True, text=True, check=True,
    )
    plain_path.unlink(missing_ok=True)
    print(f"Created {final_path}")


if __name__ == "__main__":
    make_overlay_video()
    make_no_gps_video()
    make_metadata_video()
    print("\nAll test videos created in:", OUT_DIR)
