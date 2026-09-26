"""Logging setup shared by the robot entry point and mission code."""

import logging
import os
import json
import platform
import signal
import subprocess
import sys
import atexit
import shutil
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parents[1] / "assets" / "logs"
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUPS = 2
_cleanup_callbacks = []
_run_finished = False
_run_code = None
_run_logger = None
_manifest = {}


def New_Run_Code():
    """Use the same unique code for this run's log and video."""
    return "run_{}_{}".format(datetime.now().strftime("%Y%m%d_%H%M%S_%f"), os.getpid())


def _git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL,
            text=True, cwd=Path(__file__).resolve().parents[2],
        ).strip()
    except Exception:
        return None


def Create_Manifest(run_code, video_path=None):
    """Create a small machine-readable record tying artifacts to one run."""
    global _run_code, _manifest
    _run_code = run_code
    _manifest = {
        "run_code": run_code,
        "pid": os.getpid(),
        "start_time": datetime.now().astimezone().isoformat(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version,
        "git_commit": _git_commit(),
        "log_file": str(LOG_DIR / (run_code + ".log")),
        "video_file": video_path,
        "status": "running",
    }
    _Write_Manifest()
    return _manifest


def _Write_Manifest():
    if not _manifest or not _run_code:
        return
    manifest_path = LOG_DIR / (_run_code + ".json")
    try:
        manifest_path.write_text(
            json.dumps(_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        if _run_logger:
            _run_logger.exception("Failed to write run manifest")


def Add_Cleanup(callback):
    """Register a best-effort cleanup callback for normal and failed exits."""
    if callback is not None:
        _cleanup_callbacks.append(callback)


def Finish_Run(status, logger=None, error=None):
    """Close registered resources and persist the final run status once."""
    global _run_finished
    if _run_finished:
        return
    _run_finished = True
    if logger is not None:
        logger.info("RUN_END status=%s", status)
    for callback in reversed(_cleanup_callbacks):
        try:
            callback()
        except Exception:
            if logger is not None:
                logger.exception("Cleanup callback failed")
    if _manifest:
        _manifest["status"] = status
        _manifest["end_time"] = datetime.now().astimezone().isoformat()
        if error is not None:
            _manifest["error"] = repr(error)
        _Write_Manifest()
    if logger is not None:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def Install_Runtime_Handlers(logger, run_code):
    """Install exception, signal, and interpreter-exit handlers."""
    global _run_logger
    _run_logger = logger

    def log_unhandled(exc_type, exc_value, exc_traceback):
        if _run_finished:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        if issubclass(exc_type, KeyboardInterrupt):
            logger.warning("RUN_END status=keyboard_interrupt")
            Finish_Run("keyboard_interrupt", logger, exc_value)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        Finish_Run("uncaught_exception", logger, exc_value)

    def handle_signal(signum, _frame):
        logger.warning("Received signal %s", signum)
        Finish_Run("signal_{}".format(signum), logger)
        raise SystemExit(128 + signum)

    sys.excepthook = log_unhandled
    for signal_name in ("SIGINT", "SIGTERM"):
        signal_value = getattr(signal, signal_name, None)
        if signal_value is not None:
            signal.signal(signal_value, handle_signal)
    atexit.register(lambda: Finish_Run("process_exit", logger))


def Logger_Setup(mission_code="Logistic_Handling",
                 level_list=(logging.DEBUG, logging.INFO, logging.DEBUG)):
    level_logger, level_file, level_console = level_list
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("public_logger")
    logger.setLevel(level_logger)

    # Reconfiguration must not duplicate output or leave a file open.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        LOG_DIR / "{}.log".format(mission_code),
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUPS,
        encoding="utf-8",
    )
    # Keep the primary log compact; all DEBUG records remain in .debug.log.
    file_handler.setLevel(max(level_file, logging.INFO))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    debug_file_handler = RotatingFileHandler(
        LOG_DIR / "{}.debug.log".format(mission_code),
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUPS,
        encoding="utf-8",
    )
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(formatter)
    logger.addHandler(debug_file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level_console)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


def Check_Disk_Space(path=None, minimum_free_mb=512, logger=None):
    """Return whether enough storage remains for video and diagnostic files."""
    target = path or LOG_DIR
    usage = shutil.disk_usage(target)
    free_mb = usage.free / (1024 * 1024)
    if logger is not None:
        logger.info("DISK free_mb=%.1f total_mb=%.1f", free_mb,
                    usage.total / (1024 * 1024))
        if free_mb < minimum_free_mb:
            logger.error("DISK_LOW free_mb=%.1f threshold_mb=%s", free_mb,
                         minimum_free_mb)
    return free_mb >= minimum_free_mb


def Install_Exception_Hook(logger):
    """Backward-compatible wrapper for callers using the old API."""
    Install_Runtime_Handlers(logger, _run_code or "unknown")
