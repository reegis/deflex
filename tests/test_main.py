import os
import shutil
import pandas as pd
from oemof import solph
from deflex import main, config as cfg
from nose.tools import assert_raises_regexp


class TestMain:
    @classmethod
    def setUpClass(cls):
        date_time_index = pd.date_range('1/1/2014', periods=30, freq='H')
        cls.es = solph.EnergySystem(timeindex=date_time_index)
        base_path = os.path.join(os.path.dirname(__file__), 'data')
        cfg.tmp_set('paths', 'scenario', base_path)

    @classmethod
    def tearDownClass(cls):
        base_path = os.path.join(os.path.dirname(__file__), 'data')
        shutil.rmtree(os.path.join(
            base_path, 'deflex', '2014', 'results_cbc'))

    def test_main_secure(self):
        main.main_secure(2014, 'de22')

    def test_main_secure_with_es(self):
        main.main_secure(2014, 'de21', es=self.es)

    def test_main_secure_with_xls_file(self):
        main.main_secure(2014, 'de02', csv=False, es=self.es)


def test_duplicate_input():
    msg = "It is not allowed to define more than one input."
    with assert_raises_regexp(ValueError, msg):
        main.model_scenario(xls_file='something', csv_path='something')
