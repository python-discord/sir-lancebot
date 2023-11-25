import logging
import logging.handlers
import os
import sys
from pathlib import Path

import coloredlogs
import sentry_sdk
from pydis_core.utils import logging as core_logging
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from bot.constants import Client, GIT_SHA, Logging


def setup() -> None:
    """Set up loggers."""
    root_logger = core_logging.get_logger()

    if Logging.file_logs:
        # Set up file logging
        log_file = Path("logs", "sir-lancebot.log")
        log_file.parent.mkdir(exist_ok=True)

        # File handler rotates logs every 5 MB
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * (2 ** 20), backupCount=10, encoding="utf-8",
        )
        file_handler.setFormatter(core_logging.log_format)
        root_logger.addHandler(file_handler)

    if "COLOREDLOGS_LEVEL_STYLES" not in os.environ:
        coloredlogs.DEFAULT_LEVEL_STYLES = {
            **coloredlogs.DEFAULT_LEVEL_STYLES,
            "trace": {"color": 246},
            "critical": {"background": "red"},
            "debug": coloredlogs.DEFAULT_LEVEL_STYLES["info"],
        }

    if "COLOREDLOGS_LOG_FORMAT" not in os.environ:
        coloredlogs.DEFAULT_LOG_FORMAT = core_logging.log_format._fmt

    coloredlogs.install(level=core_logging.TRACE_LEVEL, stream=sys.stdout)

    root_logger.setLevel(logging.DEBUG if Logging.debug else logging.INFO)

    logging.getLogger("PIL").setLevel(logging.ERROR)
    logging.getLogger("matplotlib").setLevel(logging.ERROR)

    _set_trace_loggers()
    root_logger.info("Logging initialization complete")


def setup_sentry() -> None:
    """Set up the Sentry logging integrations."""
    sentry_logging = LoggingIntegration(
        level=logging.DEBUG,
        event_level=logging.WARNING
    )

    sentry_sdk.init(
        dsn=Client.sentry_dsn,
        integrations=[
            sentry_logging,
            RedisIntegration(),
        ],
        release=f"bot@{GIT_SHA}",
        traces_sample_rate=0.5,
        _experiments={
            "profiles_sample_rate": 0.5,
        },
    )


def _set_trace_loggers() -> None:
    """
    Set loggers to the trace level according to the value from the BOT_TRACE_LOGGERS env var.

    When the env var is a list of logger names delimited by a comma,
    each of the listed loggers will be set to the trace level.

    If this list is prefixed with a "!", all of the loggers except the listed ones will be set to the trace level.

    Otherwise if the env var begins with a "*",
    the root logger is set to the trace level and other contents are ignored.
    """
    level_filter = Logging.trace_loggers
    if level_filter:
        if level_filter.startswith("*"):
            core_logging.get_logger().setLevel(core_logging.TRACE_LEVEL)

        elif level_filter.startswith("!"):
            core_logging.get_logger().setLevel(core_logging.TRACE_LEVEL)
            for logger_name in level_filter.strip("!,").split(","):
                core_logging.get_logger(logger_name).setLevel(logging.DEBUG)

        else:
            for logger_name in level_filter.strip(",").split(","):
                core_logging.get_logger(logger_name).setLevel(core_logging.TRACE_LEVEL)
