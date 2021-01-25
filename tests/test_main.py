# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os

import pandas as pd
from oemof import solph


class TestMain:
    @classmethod
    def setup_class(cls):
        cls.date_time_index = pd.date_range("1/1/2014", periods=30, freq="H")
        cls.es = solph.EnergySystem(timeindex=cls.date_time_index)
        cls.base_path = os.path.join(os.path.dirname(__file__), "data")

    @classmethod
    def teardown_class(cls):
        pass

    def test_something(self):
        pass
