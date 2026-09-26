"""Offline checks for logging and debug export; no hardware access."""

import json
import logging
import tempfile
from pathlib import Path

from mission import Run_Logging


def main():
    with tempfile.TemporaryDirectory() as directory:
        Run_Logging.LOG_DIR = Path(directory)
        logger = Run_Logging.Logger_Setup(
            "diagnostic_check", (logging.DEBUG, logging.INFO, logging.CRITICAL)
        )
        Run_Logging.Create_Manifest("diagnostic_check", "video.avi")
        logger.debug("diagnostic debug record")
        logger.info("diagnostic info record")
        Run_Logging.Finish_Run("self_check", logger)
        manifest = json.loads(
            (Path(directory) / "diagnostic_check.json").read_text(encoding="utf-8")
        )
        assert manifest["status"] == "self_check"
        assert (Path(directory) / "diagnostic_check.log").exists()
        assert (Path(directory) / "diagnostic_check.debug.log").exists()
    print("diagnostic checks passed")


if __name__ == "__main__":
    main()
