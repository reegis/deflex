# -*- coding: utf-8 -*-

"""
Test feed-in.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
from shutil import copyfile

from deflex import config as cfg
from deflex import geometries
from deflex import tools


class TestFeedin:
    @classmethod
    def setup_class(cls):
        """Download pp-file from osf."""

        downloads = [
            ("n7ahr", "geothermal"),
            ("5n7t3", "hydro"),
            ("2qwv7", "solar"),
            ("9dvpf", "wind"),
        ]

        for d in downloads:
            url = "https://osf.io/{0}/download".format(d[0])
            path = os.path.join(cfg.get("paths", "feedin"), "de21", "2014")
            file = "2014_feedin_de21_normalised_{0}.csv".format(d[1])
            filename = os.path.join(path, file)
            os.makedirs(path, exist_ok=True)
            tools.download(filename, url)

        src = os.path.join(
            os.path.dirname(__file__), "data", "windzone_de21.csv"
        )
        trg = os.path.join(
            cfg.get("paths", "powerplants"), "windzone_de21.csv"
        )
        copyfile(src, trg)
        cfg.tmp_set("init", "map", "de21")
        regions = geometries.deflex_regions(rmap="de21")
        cls.f = dict()
        print(regions)
        # cls.f = scenario_builder.scenario_feedin(regions, 2014, "de21")

    def scenario_feedin_wind1(self):
        """Test scenario feed-in."""
        assert int(self.f["DE01"].sum()["wind"]) == 2159

    def scenario_feedin_wind2(self):
        assert int(self.f["DE16"].sum()["wind"]) == 1753

    def scenario_feedin_solar(self):
        assert int(self.f["DE01"].sum()["solar"]) == 913
