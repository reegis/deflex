# -*- coding: utf-8 -*-

"""
Test the main module

Copyright (c) 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
import shutil
import pandas as pd
from oemof import solph
from deflex import main, config as cfg
from nose.tools import assert_raises_regexp


class TestMain:
    @classmethod
    def setUpClass(cls):
        cls.date_time_index = pd.date_range('1/1/2014', periods=30, freq='H')
        cls.es = solph.EnergySystem(timeindex=cls.date_time_index)
        cls.base_path = os.path.join(os.path.dirname(__file__), 'data')
        cfg.tmp_set('paths', 'scenario', cls.base_path)

    @classmethod
    def tearDownClass(cls):
        base_path = os.path.join(os.path.dirname(__file__), 'data')
        shutil.rmtree(os.path.join(base_path, 'deflex', '2014', 'results_cbc'))
        shutil.rmtree(os.path.join(base_path, 'deflex', '2013', 'results_cbc'))

    def test_main_secure(self):
        main.main_secure(1910, 'de55')

    def test_main_secure_with_es(self):
        main.main(2014, 'de21', es=self.es)

    def test_main_secure_with_xls_file(self):
        my_es = solph.EnergySystem(timeindex=self.date_time_index)
        main.main(2013, 'de02', csv=False, es=my_es)

    def test_model_scenario(self):
        ip = os.path.join(
            self.base_path, 'deflex', '2013', 'deflex_2013_de02.xls')
        my_es = solph.EnergySystem(timeindex=self.date_time_index)
        main.model_scenario(xls_file=ip, name='test_02', rmap='de', year=2025,
                            es=my_es)


def test_duplicate_input():
    msg = "It is not allowed to define more than one input."
    with assert_raises_regexp(ValueError, msg):
        main.model_scenario(xls_file='something', csv_path='something')
