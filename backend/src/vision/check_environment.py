"""
Phase 0 - Environment & Hardware Check
RoadSense AI - Member 1 (Vision & Data)

Verifies that the required tooling is present and logs hardware
capability (CPU/GPU) so later phases (esp. YOLOv8 training) can decide
whether to use a lighter model/config, per the plan's risk mitigation
for "Limited GPU/RAM".

Run:
    python3 check_environment.py
Output:
    Prints a report and writes logs/environment_report.json
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
LOG_DIR.mkdir(exist_ok=True)


def _binary_available(name: str) -> bool:
    return shutil.which(name) is not None


def _module_available(module_name: str) -> str | None:
    try:
        mod = __import__(module_name)
        return getattr(mod, "__version__", "unknown-version")
    except ImportError:
        return None


def check_gpu() -> dict:
    """Check for a usable GPU via torch (if installed) or nvidia-smi."""
    gpu_info = {"gpu_available": False, "device_name": None, "detection_method": None}

    torch_version = _module_available("torch")
    if torch_version:
        import torch  # local import, only if present

        if torch.cuda.is_available():
            gpu_info["gpu_available"] = True
            gpu_info["device_name"] = torch.cuda.get_device_name(0)
            gpu_info["detection_method"] = "torch.cuda"
            return gpu_info

    # Fallback: nvidia-smi
    if _binary_available("nvidia-smi"):
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if out.returncode == 0 and out.stdout.strip():
                gpu_info["gpu_available"] = True
                gpu_info["device_name"] = out.stdout.strip().splitlines()[0]
                gpu_info["detection_method"] = "nvidia-smi"
        except Exception:
            pass

    return gpu_info


def run_check() -> dict:
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "binaries": {
            "ffmpeg": _binary_available("ffmpeg"),
            "ffprobe": _binary_available("ffprobe"),
            "tesseract": _binary_available("tesseract"),
        },
        "python_packages": {
            "opencv (cv2)": _module_available("cv2"),
            "pytesseract": _module_available("pytesseract"),
            "pymediainfo": _module_available("pymediainfo"),
            "gpxpy": _module_available("gpxpy"),
            "ultralytics": _module_available("ultralytics"),
            "torch": _module_available("torch"),
        },
        "hardware": check_gpu(),
    }

    report["recommended_training_mode"] = (
        "GPU (full YOLOv8s/m training)" if report["hardware"]["gpu_available"]
        else "CPU (use yolov8n, small image size, fewer epochs, or Colab/Kaggle GPU)"
    )
    return report


def main():
    report = run_check()

    print("=" * 60)
    print("RoadSense AI - Phase 0 Environment Report")
    print("=" * 60)
    print(json.dumps(report, indent=2))

    missing_binaries = [k for k, v in report["binaries"].items() if not v]
    missing_packages = [k for k, v in report["python_packages"].items()
                         if v is None and k not in ("ultralytics", "torch")]

    out_path = LOG_DIR / "environment_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\nReport saved to: {out_path}")

    if missing_binaries:
        print(f"\n[WARN] Missing system binaries: {missing_binaries}")
        print("       Install via apt (e.g. `sudo apt install ffmpeg tesseract-ocr`).")
    if missing_packages:
        print(f"\n[WARN] Missing Python packages: {missing_packages}")
        print("       Install via `pip install -r requirements.txt`.")
    if not missing_binaries and not missing_packages:
        print("\n[OK] Core Phase 0/1 dependencies are all present.")


if __name__ == "__main__":
    main()
