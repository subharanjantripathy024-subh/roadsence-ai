from pathlib import Path
import argparse
import csv
import uuid

from gps_detector import detect_gps


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "yolo_output"
    / "detections.csv"
)

DEFAULT_VIDEO_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "demo_clip"
    / "video_with_metadata.mp4"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "m1_output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "m1_detections.csv"
)


def convert_detections(video_path: Path):

    if not INPUT_CSV.exists():
        print(
            f"[ERROR] YOLO CSV not found: {INPUT_CSV}"
        )
        return False

    if not video_path.exists():
        print(
            f"[ERROR] Video not found: {video_path}"
        )
        return False

    # ---------------------------------------------------------
    # Detect GPS from the uploaded/current video
    # ---------------------------------------------------------

    print("[INFO] Detecting GPS...")
    print(f"[INFO] Video: {video_path}")

    gps = detect_gps(video_path)

    print(
        f"[INFO] GPS status: "
        f"{gps.location_status}"
    )

    print(
        f"[INFO] GPS source: "
        f"{gps.source}"
    )

    print(
        f"[INFO] Latitude: "
        f"{gps.latitude}"
    )

    print(
        f"[INFO] Longitude: "
        f"{gps.longitude}"
    )

    converted = []

    # ---------------------------------------------------------
    # Convert YOLO detections to M1 contract
    # ---------------------------------------------------------

    with open(
        INPUT_CSV,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            detection_id = (
                f"d-{uuid.uuid4().hex[:8]}"
            )

            converted.append({
                "detection_id": detection_id,
                "timestamp": row["timestamp"],

                "latitude": (
                    gps.latitude
                    if gps.latitude is not None
                    else ""
                ),

                "longitude": (
                    gps.longitude
                    if gps.longitude is not None
                    else ""
                ),

                "road_id": "unknown",

                "damage_type":
                    row["damage_class"],

                "confidence":
                    row["confidence"],

                "frame_id":
                    f"frame_{row['frame_number']}"
            })

    # ---------------------------------------------------------
    # Save M1 output
    # ---------------------------------------------------------

    fieldnames = [
        "detection_id",
        "timestamp",
        "latitude",
        "longitude",
        "road_id",
        "damage_type",
        "confidence",
        "frame_id"
    ]

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(converted)

    print()
    print(
        "[SUCCESS] M1 adapter completed."
    )

    print(
        f"[INFO] Converted detections: "
        f"{len(converted)}"
    )

    print(
        f"[INFO] Output: {OUTPUT_CSV}"
    )

    return True


def main():

    parser = argparse.ArgumentParser(
        description="ROADSense M1 adapter"
    )

    parser.add_argument(
        "video_path",
        nargs="?",
        default=str(DEFAULT_VIDEO_PATH),
        help="Video used for GPS extraction"
    )

    args = parser.parse_args()

    video_path = Path(
        args.video_path
    ).resolve()

    success = convert_detections(
        video_path
    )

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()