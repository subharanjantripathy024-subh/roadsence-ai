from pathlib import Path
import argparse
import csv

from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = PROJECT_ROOT / "models" / "road_damage.pt"

DEFAULT_FRAMES_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "frames_output"
    / "frames"
)

DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "frames_output"
    / "frame_manifest.csv"
)

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "yolo_output"
)


def load_frame_timestamps(manifest_path: Path):
    timestamps = {}

    if not manifest_path.exists():
        return timestamps

    with open(
        manifest_path,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            try:
                saved_index = int(
                    row["saved_index"]
                )

                timestamps[saved_index] = float(
                    row["timestamp_sec"]
                )

            except (
                KeyError,
                ValueError,
                TypeError
            ):
                continue

    return timestamps


def run_detection(
    frames_dir: Path,
    manifest_path: Path,
    output_dir: Path,
    output_csv: Path,
    confidence_threshold: float = 0.20
):

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"YOLO model not found: {MODEL_PATH}"
        )

    if not frames_dir.exists():
        raise FileNotFoundError(
            f"Frames directory not found: {frames_dir}"
        )

    frame_files = sorted(
        frames_dir.glob("*.jpg")
    )

    if not frame_files:
        print(
            "[ERROR] No JPG frames found."
        )
        return False

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_csv.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "[INFO] Loading YOLO model..."
    )

    model = YOLO(
        str(MODEL_PATH)
    )

    print(
        f"[INFO] Model: {MODEL_PATH}"
    )

    print(
        f"[INFO] Frames: {frames_dir}"
    )

    print(
        f"[INFO] Confidence threshold: "
        f"{confidence_threshold}"
    )

    print(
        f"[INFO] Found {len(frame_files)} frames."
    )

    timestamps = load_frame_timestamps(
        manifest_path
    )

    results = model.predict(
        source=str(frames_dir),
        conf=confidence_threshold,
        save=True,
        project=str(output_dir),
        name="annotated",
        exist_ok=True,
        verbose=True
    )

    rows = []
    total_detections = 0

    for index, result in enumerate(results):

        frame_file = frame_files[index]

        frame_number = (
            frame_file.stem
            .replace("frame_", "")
        )

        try:
            frame_number_int = int(
                frame_number
            )
        except ValueError:
            frame_number_int = index

        timestamp = timestamps.get(
            frame_number_int,
            float(
                frame_number_int
            )
        )

        if result.boxes is None:
            continue

        for box in result.boxes:

            confidence = float(
                box.conf[0]
            )

            class_id = int(
                box.cls[0]
            )

            damage_class = model.names[
                class_id
            ]

            x1, y1, x2, y2 = map(
                float,
                box.xyxy[0].tolist()
            )

            rows.append({
                "frame_number":
                    frame_number,

                "timestamp":
                    timestamp,

                "x1":
                    round(x1, 2),

                "y1":
                    round(y1, 2),

                "x2":
                    round(x2, 2),

                "y2":
                    round(y2, 2),

                "damage_class":
                    damage_class,

                "confidence":
                    round(
                        confidence,
                        4
                    )
            })

            total_detections += 1

    fieldnames = [
        "frame_number",
        "timestamp",
        "x1",
        "y1",
        "x2",
        "y2",
        "damage_class",
        "confidence"
    ]

    with open(
        output_csv,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print(
        "[SUCCESS] YOLO detection completed."
    )

    print(
        f"[INFO] Total detections: "
        f"{total_detections}"
    )

    print(
        f"[INFO] CSV saved to: {output_csv}"
    )

    return True


def main():

    parser = argparse.ArgumentParser(
        description="ROADSense YOLO detector"
    )

    parser.add_argument(
        "--frames",
        default=str(
            DEFAULT_FRAMES_DIR
        ),
        help="Directory containing JPG frames"
    )

    parser.add_argument(
        "--manifest",
        default=str(
            DEFAULT_MANIFEST_PATH
        ),
        help="Frame manifest CSV"
    )

    parser.add_argument(
        "--output-dir",
        default=str(
            DEFAULT_OUTPUT_DIR
        ),
        help="YOLO output directory"
    )

    parser.add_argument(
        "--output-csv",
        default=str(
            DEFAULT_OUTPUT_DIR
            / "detections.csv"
        ),
        help="Detection CSV path"
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.20,
        help="YOLO confidence threshold"
    )

    args = parser.parse_args()

    run_detection(
        frames_dir=Path(
            args.frames
        ).resolve(),

        manifest_path=Path(
            args.manifest
        ).resolve(),

        output_dir=Path(
            args.output_dir
        ).resolve(),

        output_csv=Path(
            args.output_csv
        ).resolve(),

        confidence_threshold=
            args.confidence
    )


if __name__ == "__main__":
    main()