# -*- coding: utf-8 -*-

"""Create a basic scenario from the internal data structure.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


from oemof.tools import logger

from deflex import geometries

# from basic_scenario import create_basic_scenario


def create_electricity_market_scenario(regions, year, name):
    """pass"""
    logger.define_logging()
    # create_basic_scenario(year, "de02")


if __name__ == "__main__":
    de01 = geometries.deflex_regions("de01")
    create_electricity_market_scenario(de01, 2014, "de01")
