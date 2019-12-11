# -*- coding: utf-8 -*-

"""
Test the power plant module.

Copyright (c) 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
from pandas import errors
from warnings import filterwarnings
from nose.tools import assert_raises_regexp
from unittest.mock import MagicMock
from deflex import config as cfg, powerplants, geometries
from reegis.tools import download_file

filterwarnings("ignore", category=errors.PerformanceWarning)


def test_01_download_reegis_power_plants():
    url = "https://osf.io/ude5c/download"
    path = cfg.get("paths", "powerplants")
    file = "reegis_pp_test.h5"
    filename = os.path.join(path, file)

    download_file(filename, url)


def test_02_create_deflex_powerplants():
    de = geometries.deflex_regions("de21")
    fn_in = os.path.join(cfg.get("paths", "powerplants"), "reegis_pp_test.h5")
    fn_out = os.path.join(cfg.get("paths", "powerplants"), "deflex_pp_test.h5")
    powerplants.pp_reegis2deflex(
        de, "de21", filename_in=fn_in, filename_out=fn_out
    )


def test_03_not_existing_file():
    old_value = cfg.get("paths", "powerplants")
    cfg.tmp_set("paths", "powerplants", "/home/pet/")
    de = geometries.deflex_regions("de22")
    powerplants.pp_reegis2deflex = MagicMock(return_value="/home/pet/pp.h5")

    with assert_raises_regexp(
        Exception, "File /home/pet/pp.h5 does not exist"
    ):
        powerplants.get_deflex_pp_by_year(de, 2012, "de22")
    cfg.tmp_set("paths", "powerplants", old_value)
