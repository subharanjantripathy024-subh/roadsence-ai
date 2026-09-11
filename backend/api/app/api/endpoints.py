from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
)
from typing import List, Optional

from app.models.domain import DamageInstance, M1Detection
from app.models.api import AgentRequest, AgentResponse
from app.data.repository import repository
from app.agent.agent import agent

import tempfile
import os
import subprocess
import sys
from pathlib import Path
import json


router = APIRouter()


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[4]

VIDEO_UPLOAD_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "video_uploads"
)

VIDEO_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CUSTOM EXCEPTION
# ============================================================

class ROADException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400
    ):
        self.code = code
        self.message = message
        self.status_code = status_code


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ROADSense M3 Backend"
    }


# ============================================================
# DAMAGE ENDPOINTS
# ============================================================

@router.get(
    "/damages",
    response_model=List[DamageInstance]
)
def get_damages(
    severity: Optional[str] = None
):
    damages = repository.get_all_damages()

    if severity:
        damages = [
            d
            for d in damages
            if d.severity.lower() == severity.lower()
        ]

    return damages


@router.get(
    "/damages/{damage_id}",
    response_model=DamageInstance
)
def get_damage(
    damage_id: str
):
    damage = repository.get_damage_by_id(
        damage_id
    )

    if not damage:
        raise ROADException(
            code="DAMAGE_NOT_FOUND",
            message=(
                f"Damage {damage_id} was not found "
                "in the current dataset."
            ),
            status_code=404
        )

    return damage


# ============================================================
# PRIORITY
# ============================================================

@router.get("/priority")
def get_priority_damages():
    """
    Return prioritized M1 road-damage detections.
    """

    if not repository._is_loaded:
        repository.load_data()

    return sorted(
        repository._m1_data,
        key=lambda x: (
            x.priority
            if hasattr(x, "priority")
            and x.priority is not None
            else 999
        )
    )


# ============================================================
# EXISTING GEOJSON UPLOAD
# ============================================================

@router.post("/upload")
def upload_data(
    file: UploadFile = File(...)
):
    """
    Upload an M2 GeoJSON file.
    """

    filename = file.filename or ""

    if not filename.lower().endswith(
        ".geojson"
    ):
        raise ROADException(
            "INVALID_FILE_TYPE",
            "File must be a GeoJSON.",
            400
        )

    fd, path = tempfile.mkstemp(
        suffix=".geojson"
    )

    try:

        with os.fdopen(
            fd,
            "wb"
        ) as f:

            f.write(
                file.file.read()
            )

        success = repository.load_data(
            m2_path=path
        )

        if not success:
            raise ROADException(
                "INVALID_SCHEMA",
                (
                    "The uploaded GeoJSON could "
                    "not be validated or loaded."
                ),
                400
            )

        return {
            "message":
                "Dataset successfully updated.",
            "filename":
                filename
        }

    finally:

        if os.path.exists(path):
            os.remove(path)


# ============================================================
# VIDEO UPLOAD + COMPLETE VISION PIPELINE
# ============================================================

@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...)
):
    """
    Complete uploaded-video pipeline:

        Video
          ↓
        Frame Extraction
          ↓
        YOLO Detection
          ↓
        M1 Adapter
          ↓
        Severity + Priority
          ↓
        M2 Aggregation
          ↓
        ByteTrack
          ↓
        Backend Reload
          ↓
        Dashboard
    """

    filename = file.filename or ""

    allowed_extensions = {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv"
    }

    extension = Path(
        filename
    ).suffix.lower()

    # --------------------------------------------------------
    # Validate video
    # --------------------------------------------------------

    if extension not in allowed_extensions:
        raise ROADException(
            "INVALID_VIDEO_TYPE",
            (
                "File must be an MP4, AVI, MOV, "
                "or MKV video."
            ),
            400
        )

    # --------------------------------------------------------
    # Safe filename
    # --------------------------------------------------------

    safe_filename = Path(
        filename
    ).name

    video_path = (
        VIDEO_UPLOAD_DIR
        / safe_filename
    )

    # --------------------------------------------------------
    # Processing directory
    # --------------------------------------------------------

    frame_output_dir = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "video_upload_test"
    )

    # --------------------------------------------------------
    # Save uploaded video
    # --------------------------------------------------------

    try:

        with open(
            video_path,
            "wb"
        ) as f:

            f.write(
                await file.read()
            )

        # ====================================================
        # STEP 1 — FRAME EXTRACTION
        # ====================================================

        extract_cmd = [
            sys.executable,

            str(
                PROJECT_ROOT
                / "backend"
                / "src"
                / "vision"
                / "extract_frames.py"
            ),

            str(video_path),

            "--out",

            str(frame_output_dir)
        ]

        result = subprocess.run(
            extract_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            raise ROADException(
                "FRAME_EXTRACTION_FAILED",
                (
                    result.stderr
                    or "Frame extraction failed."
                ),
                500
            )

        # ====================================================
        # STEP 2 — YOLO DETECTION
        # ====================================================

        frames_dir = (
            frame_output_dir
            / "frames"
        )

        manifest_path = (
            frame_output_dir
            / "frame_manifest.csv"
        )

        yolo_cmd = [
            sys.executable,

            str(
                PROJECT_ROOT
                / "backend"
                / "src"
                / "vision"
                / "yolo_detector.py"
            ),

            "--frames",
            str(frames_dir),

            "--manifest",
            str(manifest_path)
        ]

        result = subprocess.run(
            yolo_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            raise ROADException(
                "YOLO_DETECTION_FAILED",
                (
                    result.stderr
                    or "YOLO detection failed."
                ),
                500
            )

        # ====================================================
        # STEP 3 — M1 ADAPTER
        # ====================================================

        m1_cmd = [
            sys.executable,

            str(
                PROJECT_ROOT
                / "backend"
                / "src"
                / "vision"
                / "m1_adapter.py"
            ),

            str(video_path)
        ]

        result = subprocess.run(
            m1_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            raise ROADException(
                "M1_PROCESSING_FAILED",
                (
                    result.stderr
                    or "M1 processing failed."
                ),
                500
            )

        # ====================================================
        # STEP 4 — SEVERITY + PRIORITY
        # ====================================================

        severity_cmd = [
            sys.executable,

            str(
                PROJECT_ROOT
                / "backend"
                / "src"
                / "vision"
                / "severity_priority.py"
            )
        ]

        result = subprocess.run(
            severity_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            raise ROADException(
                "SEVERITY_PROCESSING_FAILED",
                (
                    result.stderr
                    or (
                        "Severity and priority "
                        "calculation failed."
                    )
                ),
                500
            )

        # ====================================================
        # STEP 5 — M2 AGGREGATION
        # ====================================================

        m2_cmd = [
            sys.executable,

            str(
                PROJECT_ROOT
                / "backend"
                / "src"
                / "vision"
                / "m2_aggregator.py"
            )
        ]

        result = subprocess.run(
            m2_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            raise ROADException(
                "M2_AGGREGATION_FAILED",
                (
                    result.stderr
                    or "M2 aggregation failed."
                ),
                500
            )

        # ====================================================
        # STEP 6 — BYTE TRACK
        # ====================================================

        tracking_cmd = [
            sys.executable,

            str(
                PROJECT_ROOT
                / "backend"
                / "src"
                / "vision"
                / "track_damage.py"
            ),

            str(video_path)
        ]

        result = subprocess.run(
            tracking_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            raise ROADException(
                "TRACKING_FAILED",
                (
                    result.stderr
                    or "ByteTrack processing failed."
                ),
                500
            )

        # ====================================================
        # STEP 7 — RELOAD BACKEND DATA
        # ====================================================

        success = repository.load_data()

        if not success:
            raise ROADException(
                "DATA_RELOAD_FAILED",
                (
                    "The processed M1/M2 data could "
                    "not be reloaded."
                ),
                500
            )

        m1_detections = (
            repository._m1_data
        )

        damages = (
            repository.get_all_damages()
        )

        total_cost = sum(
            d.estimated_repair_cost
            for d in damages
        )

        # ====================================================
        # LOAD TRACKING SUMMARY
        # ====================================================

        tracking_summary_path = (
            PROJECT_ROOT
            / "data"
            / "processed"
            / "tracking_output"
            / "tracking_summary.json"
        )

        tracking_summary = {}

        if tracking_summary_path.exists():

            try:

                with open(
                    tracking_summary_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    tracking_summary = (
                        json.load(f)
                    )

            except Exception:
                tracking_summary = {}

        # ====================================================
        # RETURN RESULT
        # ====================================================

        return {
            "message":
                "Video processed successfully.",

            "filename":
                filename,

            "detections":
                len(m1_detections),

            "damage_instances":
                len(damages),

            "total_estimated_cost":
                total_cost,

            "tracking":
                tracking_summary,

            "gps_note": (
                "GPS coordinates are used only "
                "when available from the uploaded "
                "video. No coordinates are fabricated."
            )
        }

    finally:

        # ----------------------------------------------------
        # Delete uploaded video after processing
        # ----------------------------------------------------

        if video_path.exists():

            try:
                video_path.unlink()

            except Exception:
                pass


# ============================================================
# SUMMARY
# ============================================================

@router.get("/summary")
def get_summary():

    damages = (
        repository.get_all_damages()
    )

    total_cost = sum(
        d.estimated_repair_cost
        for d in damages
    )

    return {
        "total_damages":
            len(damages),

        "total_estimated_cost":
            total_cost
    }


# ============================================================
# AI AGENT
# ============================================================

@router.post(
    "/agent/ask",
    response_model=AgentResponse
)
def ask_agent(
    req: AgentRequest
):

    return agent.process_request(
        question=req.question,
        session_id=req.session_id
    )


# ============================================================
# M1 DETECTIONS
# ============================================================

@router.get(
    "/m1/detections",
    response_model=List[M1Detection]
)
def get_m1_detections():
    """
    Return M1 vision detections
    from the configured CSV.
    """

    if not repository._is_loaded:
        repository.load_data()

    return repository._m1_data


# ============================================================
# BYTE TRACK SUMMARY
# ============================================================

@router.get("/tracking/summary")
def get_tracking_summary():
    """
    Return the latest ByteTrack tracking summary.
    """

    summary_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "tracking_output"
        / "tracking_summary.json"
    )

    if not summary_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Tracking summary not available."
            )
        )

    with open(
        summary_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)