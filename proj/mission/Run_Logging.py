"""Logging setup shared by the robot entry point and mission code."""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parents[1] / "assets" / "logs"
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUPS = 2


def New_Run_Code():
    """Use the same unique code for this run's log and video."""
    return "run_{}_{}".format(datetime.now().strftime("%Y%m%d_%H%M%S_%f"), os.getpid())


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
    file_handler.setLevel(level_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level_console)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


def Install_Exception_Hook(logger):
    """Record uncaught startup and main-loop exceptions in the run log."""
    def log_unhandled(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = log_unhandled
