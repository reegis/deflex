# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
import shutil
import pandas as pd
from oemof import solph
from deflex import main, config as cfg, scenario_tools
from nose.tools import assert_raises_regexp, eq_


class TestMain:
    @classmethod
    def setup_class(cls):
        cls.date_time_index = pd.date_range("1/1/2014", periods=30, freq="H")
        cls.es = solph.EnergySystem(timeindex=cls.date_time_index)
        cls.base_path = os.path.join(os.path.dirname(__file__), "data")
        cfg.tmp_set("paths", "scenario", cls.base_path)

    @classmethod
    def teardown_class(cls):
        base_path = os.path.join(os.path.dirname(__file__), "data")
        shutil.rmtree(os.path.join(base_path, "deflex", "2014", "results_cbc"))
        shutil.rmtree(os.path.join(base_path, "deflex", "2013", "results_cbc"))

    def test_main_secure(self):
        main.main_secure(1910, "de55")

    def test_main_secure_with_es(self):
        main.main(2014, "de21", es=self.es, extra_regions=["DE03", "DE07"])
        fn = os.path.join(
            self.base_path,
            "deflex",
            "2014",
            "results_cbc",
            "deflex_2014_de21.esys",
        )
        assert os.path.isfile(fn)
        sc = scenario_tools.Scenario()
        sc.restore_es(fn)
        flows = [x for x in sc.es.results["main"].keys() if x[1] is not None]
        commodity_regions = [
            x[0].label.region
            for x in flows
            if x[1].label.tag == "commodity"
            and x[1].label.subtag == "natural_gas"
            and x[1].label.cat == "bus"
            and x[0].label.cat == "source"
        ]
        eq_(commodity_regions, ["DE", "DE03", "DE07"])

    def test_main_secure_with_xls_file(self):
        my_es = solph.EnergySystem(timeindex=self.date_time_index)
        main.main(2013, "de02", csv=False, es=my_es)
        assert os.path.isfile(
            os.path.join(
                self.base_path,
                "deflex",
                "2013",
                "results_cbc",
                "deflex_2013_de02.esys",
            )
        )

    def test_model_scenario(self):
        ip = os.path.join(
            self.base_path, "deflex", "2013", "deflex_2013_de02.xls"
        )
        my_es = solph.EnergySystem(timeindex=self.date_time_index)
        main.model_scenario(
            xls_file=ip, name="test_02", rmap="de", year=2025, es=my_es
        )
        assert os.path.isfile(
            os.path.join(
                self.base_path, "deflex", "2013", "results_cbc", "test_02.esys"
            )
        )


def test_duplicate_input():
    msg = "It is not allowed to define more than one input."
    with assert_raises_regexp(ValueError, msg):
        main.model_scenario(xls_file="something", csv_path="something")
