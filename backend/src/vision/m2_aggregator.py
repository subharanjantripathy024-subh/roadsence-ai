import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "m1_output"
    / "prioritized_detections.csv"
)

DEFAULT_OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "m2_output"
    / "damage_instances.geojson"
)


def calculate_repair_cost(
    damage_type: str,
    severity: str
) -> float:

    damage_type = damage_type.lower()
    severity = severity.lower()

    if damage_type == "pothole":
        base = 5000
    elif "alligator" in damage_type:
        base = 7000
    elif "transverse" in damage_type:
        base = 3500
    elif "longitudinal" in damage_type:
        base = 3000
    else:
        base = 4000

    multiplier = {
        "critical": 1.5,
        "high": 1.25,
        "medium": 1.0,
        "low": 0.75,
    }.get(severity, 1.0)

    return round(base * multiplier, 2)


def build_geojson(
    input_file: Path,
    output_file: Path
) -> bool:

    if not input_file.exists():
        raise FileNotFoundError(
            f"M1 input file not found: {input_file}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        input_file,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    if not rows:
        raise ValueError(
            "M1 input file contains no detections."
        )

    # ---------------------------------------------------------
    # Group detections
    #
    # GPS available:
    #     group by latitude + longitude + damage type
    #
    # GPS unavailable:
    #     group by frame + damage type
    #
    # This prevents different GPS-less detections from being
    # silently discarded while avoiding fabricated coordinates.
    # ---------------------------------------------------------

    groups = defaultdict(list)

    for row in rows:

        latitude = (
            row.get("latitude", "")
            or ""
        ).strip()

        longitude = (
            row.get("longitude", "")
            or ""
        ).strip()

        damage_type = (
            row.get(
                "damage_type",
                "unknown"
            )
            .lower()
            .strip()
        )

        frame_id = (
            row.get(
                "frame_id",
                ""
            )
            or ""
        ).strip()

        if latitude and longitude:

            key = (
                "gps",
                latitude,
                longitude,
                damage_type
            )

        else:

            key = (
                "no_gps",
                frame_id,
                damage_type
            )

        groups[key].append(row)

    # ---------------------------------------------------------
    # Build GeoJSON features
    # ---------------------------------------------------------

    features = []

    instance_number = 1

    for key, group in groups.items():

        # Highest-confidence detection represents the group
        best = max(
            group,
            key=lambda x: float(
                x.get(
                    "confidence",
                    0
                )
            )
        )

        latitude_raw = (
            best.get("latitude", "")
            or ""
        ).strip()

        longitude_raw = (
            best.get("longitude", "")
            or ""
        ).strip()

        latitude = (
            float(latitude_raw)
            if latitude_raw
            else None
        )

        longitude = (
            float(longitude_raw)
            if longitude_raw
            else None
        )

        confidence = float(
            best.get(
                "confidence",
                0
            )
        )

        severity = best.get(
            "severity",
            "low"
        )

        priority = int(
            best.get(
                "priority",
                4
            )
        )

        damage_type = (
            best.get(
                "damage_type",
                "unknown"
            )
            .lower()
        )

        repair_cost = calculate_repair_cost(
            damage_type,
            severity
        )

        properties = {
            "damage_id":
                f"damage-{instance_number:04d}",

            "road_id":
                best.get(
                    "road_id",
                    "unknown"
                ),

            "damage_type":
                damage_type,

            "severity":
                severity,

            "priority":
                priority,

            "confidence":
                confidence,

            "estimated_repair_cost":
                repair_cost,

            "status":
                "pending",

            "detection_count":
                len(group),

            "frame_id":
                best.get(
                    "frame_id",
                    ""
                ),

            "timestamp":
                best.get(
                    "timestamp",
                    ""
                ),

            "gps_available":
                latitude is not None
                and longitude is not None
        }

        # -----------------------------------------------------
        # GPS available → Point geometry
        # GPS unavailable → geometry = null
        # -----------------------------------------------------

        if (
            latitude is not None
            and longitude is not None
        ):

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        longitude,
                        latitude
                    ]
                },
                "properties": properties
            }

        else:

            feature = {
                "type": "Feature",
                "geometry": None,
                "properties": properties
            }

        features.append(feature)

        instance_number += 1

    # ---------------------------------------------------------
    # Create GeoJSON
    # ---------------------------------------------------------

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            geojson,
            file,
            indent=2
        )

    print(
        "[SUCCESS] M2 aggregation completed."
    )

    print(
        f"[INFO] Input detections: {len(rows)}"
    )

    print(
        f"[INFO] Damage instances: {len(features)}"
    )

    gps_count = sum(
        1
        for feature in features
        if feature["properties"]["gps_available"]
    )

    no_gps_count = (
        len(features) - gps_count
    )

    print(
        f"[INFO] GPS instances: {gps_count}"
    )

    print(
        f"[INFO] No-GPS instances: {no_gps_count}"
    )

    print(
        f"[INFO] Output: {output_file}"
    )

    return True


def main():

    parser = argparse.ArgumentParser(
        description=(
            "ROADSense M2 damage aggregation"
        )
    )

    parser.add_argument(
        "--input",
        default=str(
            DEFAULT_INPUT_FILE
        ),
        help="Prioritized M1 CSV input"
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT_FILE
        ),
        help="M2 GeoJSON output"
    )

    args = parser.parse_args()

    success = build_geojson(
        input_file=Path(
            args.input
        ).resolve(),

        output_file=Path(
            args.output
        ).resolve()
    )

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()