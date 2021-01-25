# -*- coding: utf-8 -*-

"""
Test the demand module

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os

from nose.tools import eq_
from nose.tools import with_setup

from deflex import config as cfg
from deflex import geometries
from deflex import scenario_builder
from deflex.tools import download


def setup_func():
    """Download pp-file from osf."""

    url = "https://osf.io/m435r/download"
    path = cfg.get("paths", "demand")
    file = "heat_profile_state_2014_weather_2014.csv"
    filename = os.path.join(path, file)
    download(filename, url)

    url = "https://osf.io/6vmdh/download"
    file = "oep_ego_demand_combined.h5"
    filename = os.path.join(path, file)
    download(filename, url)


@with_setup(setup_func)
def scenario_demand():
    """Test scenario demand."""
    regions = geometries.deflex_regions(rmap="de21")
    d = scenario_builder.scenario_demand(regions, 2014, "de21")
    eq_(int(d["DE01", "district heating"].sum()), 18639262)
    eq_(int(d["DE05", "electrical_load"].sum()), 10069304)
