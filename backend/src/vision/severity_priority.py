from pathlib import Path
import argparse
import csv


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_INPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "m1_output"
    / "m1_detections.csv"
)

DEFAULT_OUTPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "m1_output"
    / "prioritized_detections.csv"
)


def calculate_severity(
    damage_type: str,
    confidence: float
) -> str:

    damage = damage_type.lower()
    confidence = float(confidence)

    if damage == "pothole":

        if confidence >= 0.50:
            return "critical"

        elif confidence >= 0.30:
            return "high"

        else:
            return "medium"


    elif damage == "other corruption":

        if confidence >= 0.50:
            return "high"

        return "medium"


    elif damage in [
        "longitudinal crack",
        "transverse crack"
    ]:

        if confidence >= 0.50:
            return "medium"

        return "low"


    elif damage == "alligator crack":

        if confidence >= 0.50:
            return "high"

        return "medium"


    return "low"


def calculate_priority(
    severity: str
) -> int:

    priority_map = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
    }

    return priority_map.get(
        severity,
        4
    )


def process_detections(
    input_csv: Path,
    output_csv: Path
) -> bool:

    if not input_csv.exists():

        print(
            f"[ERROR] Input file not found: "
            f"{input_csv}"
        )

        return False


    output_csv.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []


    # ---------------------------------------------------------
    # Read M1 detections
    # ---------------------------------------------------------

    with open(
        input_csv,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            severity = calculate_severity(
                row["damage_type"],
                row["confidence"]
            )

            priority = calculate_priority(
                severity
            )

            row["severity"] = severity
            row["priority"] = priority

            results.append(row)


    # ---------------------------------------------------------
    # Write prioritized M1 data
    # ---------------------------------------------------------

    fieldnames = [
        "detection_id",
        "timestamp",
        "latitude",
        "longitude",
        "road_id",
        "damage_type",
        "confidence",
        "frame_id",
        "severity",
        "priority",
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
        writer.writerows(results)


    print()

    print(
        "[SUCCESS] Severity and priority "
        "calculation completed."
    )

    print(
        f"[INFO] Input detections: "
        f"{len(results)}"
    )

    print(
        f"[INFO] Output: {output_csv}"
    )

    return True


def main():

    parser = argparse.ArgumentParser(
        description=(
            "ROADSense severity and "
            "priority processor"
        )
    )

    parser.add_argument(
        "--input",
        default=str(
            DEFAULT_INPUT_CSV
        ),
        help=(
            "Input M1 detections CSV"
        )
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT_CSV
        ),
        help=(
            "Output prioritized CSV"
        )
    )

    args = parser.parse_args()


    success = process_detections(
        input_csv=Path(
            args.input
        ).resolve(),

        output_csv=Path(
            args.output
        ).resolve()
    )


    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()