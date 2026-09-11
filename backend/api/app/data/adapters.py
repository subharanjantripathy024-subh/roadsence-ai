import json
import csv
from typing import List, Optional

from app.models.domain import DamageInstance, M1Detection


class M1Adapter:
    @staticmethod
    def _parse_optional_float(value):
        """
        Convert a CSV value to float.
        Return None when the value is empty/unavailable.
        """
        if value is None:
            return None

        value = str(value).strip()

        if value == "":
            return None

        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def load_csv(file_path: str) -> List[M1Detection]:
        detections = []

        try:
            with open(
                file_path,
                mode="r",
                encoding="utf-8"
            ) as f:

                reader = csv.DictReader(f)

                for row in reader:

                    detections.append(
                        M1Detection(
                            detection_id=row["detection_id"],
                            timestamp=row["timestamp"],

                            latitude=M1Adapter._parse_optional_float(
                                row.get("latitude")
                            ),

                            longitude=M1Adapter._parse_optional_float(
                                row.get("longitude")
                            ),

                            road_id=row.get(
                                "road_id",
                                "unknown"
                            ),

                            damage_type=row.get(
                                "damage_type",
                                "unknown"
                            ),

                            confidence=float(
                                row.get(
                                    "confidence",
                                    0
                                )
                            ),

                            frame_id=row.get(
                                "frame_id",
                                ""
                            ),

                            severity=row.get(
                                "severity"
                            ),

                            priority=(
                                int(row["priority"])
                                if row.get("priority")
                                else None
                            )
                        )
                    )

        except FileNotFoundError:
            print(
                f"Warning: M1 data file not found at {file_path}"
            )

        return detections


class M2Adapter:

    @staticmethod
    def load_geojson(
        file_path: str
    ) -> List[DamageInstance]:

        instances = []

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

                if data.get("type") == "FeatureCollection":

                    for feature in data.get(
                        "features",
                        []
                    ):

                        props = feature.get(
                            "properties",
                            {}
                        )

                        geom = feature.get(
                            "geometry",
                            {}
                        )

                        # ----------------------------------
                        # Coordinates
                        # ----------------------------------

                        lat = props.get(
                            "latitude"
                        )

                        lon = props.get(
                            "longitude"
                        )

                        if (
                            lat is None
                            or lon is None
                        ):

                            if (
                                geom
                                and geom.get("type")
                                == "Point"
                            ):

                                coords = geom.get(
                                    "coordinates",
                                    [0, 0]
                                )

                                lon = coords[0]
                                lat = coords[1]

                        # ----------------------------------
                        # Create M2 instance
                        # ----------------------------------

                        instances.append(
                            DamageInstance(
                                damage_id=props.get(
                                    "damage_id",
                                    ""
                                ),

                                road_id=props.get(
                                    "road_id",
                                    ""
                                ),

                                road_name=props.get(
                                    "road_name"
                                ),

                                damage_type=props.get(
                                    "damage_type",
                                    ""
                                ),

                                severity=props.get(
                                    "severity",
                                    ""
                                ),

                                priority=props.get(
                                    "priority",
                                    99
                                ),

                                estimated_repair_cost=props.get(
                                    "estimated_repair_cost",
                                    0.0
                                ),

                                latitude=(
                                    lat
                                    if lat is not None
                                    else 0.0
                                ),

                                longitude=(
                                    lon
                                    if lon is not None
                                    else 0.0
                                ),

                                **{
                                    k: v
                                    for k, v in props.items()
                                    if k not in [
                                        "damage_id",
                                        "road_id",
                                        "road_name",
                                        "damage_type",
                                        "severity",
                                        "priority",
                                        "estimated_repair_cost",
                                        "latitude",
                                        "longitude"
                                    ]
                                }
                            )
                        )

        except FileNotFoundError:
            print(
                f"Warning: M2 data file not found at {file_path}"
            )

        return instances