from oemof.tools import logger
from deflex import config as cfg
from logging import CRITICAL


def use_logging(**kwargs):

    kwargs.setdefault("logpath", cfg.get("path", "base"))
    kwargs.setdefault("logfile", cfg.get("path", "logfile"))
    kwargs.setdefault("file_level", CRITICAL)
    logger.define_logging(**kwargs)
