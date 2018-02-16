"""
Reegis geometry tools.

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import logging

# oemof libraries
from oemof.tools import logger

# Internal libraries
import de21.geometries
import reegis_tools.geometries
import reegis_tools.ew


def get_ew_by_de21(year):
    name = 'de21_region'
    de21_regions = de21.geometries.de21_regions()
    return reegis_tools.ew.get_ew_by_region(year, de21_regions, name)


if __name__ == "__main__":
    logger.define_logging()
    logging.info("Getting inhabitants by region for de21.")
    print(get_ew_by_de21(2015))
