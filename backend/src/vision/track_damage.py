import argparse
from pathlib import Path
import json

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = ROOT / "models" / "road_damage.pt"

DEFAULT_VIDEO_PATH = (
    ROOT
    / "data"
    / "raw"
    / "demo_clip"
    / "pothole_video.mp4"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "tracking_output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def run_tracking(
    video_path: Path
) -> dict:

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    print("[INFO] Loading model...")
    model = YOLO(str(MODEL_PATH))

    print("[INFO] Starting ByteTrack...")
    print(f"[INFO] Video: {video_path}")

    results = model.track(
        source=str(video_path),
        tracker="bytetrack.yaml",
        conf=0.20,
        persist=True,
        save=True,
        project=str(OUTPUT_DIR),
        name="tracked_video",
        exist_ok=True,
        verbose=False,
        stream=True,
    )

    unique_tracks = set()
    total_tracked_detections = 0
    pothole_tracks = set()

    for result in results:

        if (
            result.boxes is None
            or result.boxes.id is None
        ):
            continue

        track_ids = (
            result.boxes.id
            .cpu()
            .tolist()
        )

        classes = (
            result.boxes.cls
            .cpu()
            .tolist()
        )

        for track_id, class_id in zip(
            track_ids,
            classes
        ):

            track_id = int(track_id)

            class_name = model.names[
                int(class_id)
            ]

            unique_tracks.add(track_id)

            total_tracked_detections += 1

            if class_name == "Pothole":
                pothole_tracks.add(track_id)

    summary = {
        "total_tracked_detections":
            total_tracked_detections,

        "unique_tracked_objects":
            len(unique_tracks),

        "unique_pothole_tracks":
            len(pothole_tracks),

        "pothole_track_ids":
            sorted(pothole_tracks),

        "video":
            str(video_path),

        "video_filename":
            video_path.name,
    }

    summary_path = (
        OUTPUT_DIR
        / "tracking_summary.json"
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            summary,
            f,
            indent=2
        )

    print("\n[SUCCESS] Tracking completed.")

    print(
        "[INFO] Total tracked detections: "
        f"{total_tracked_detections}"
    )

    print(
        "[INFO] Unique tracked objects: "
        f"{len(unique_tracks)}"
    )

    print(
        "[INFO] Unique pothole tracks: "
        f"{len(pothole_tracks)}"
    )

    print(
        "[INFO] Pothole Track IDs: "
        f"{sorted(pothole_tracks)}"
    )

    print(
        f"[INFO] Summary saved to: "
        f"{summary_path}"
    )

    print(
        "[INFO] Output directory: "
        f"{OUTPUT_DIR / 'tracked_video'}"
    )

    return summary


def main():

    parser = argparse.ArgumentParser(
        description=(
            "ROADSense ByteTrack damage tracking"
        )
    )

    parser.add_argument(
        "video_path",
        nargs="?",
        default=str(DEFAULT_VIDEO_PATH),
        help=(
            "Road video to track"
        )
    )

    args = parser.parse_args()

    run_tracking(
        Path(args.video_path).resolve()
    )


if __name__ == "__main__":
    main()