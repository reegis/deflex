import os
import shutil
import pandas as pd
from oemof import solph
from deflex import main, config as cfg, scenario_tools


def test_main():
    date_time_index = pd.date_range('1/1/2014', periods=30, freq='H')
    es = solph.EnergySystem(timeindex=date_time_index)
    base_path = os.path.join(os.path.dirname(__file__), 'data')
    cfg.tmp_set('paths', 'scenario', base_path)
    main.main_secure(2014, 'de22')
    main.main_secure(2014, 'de21', es=es)
    shutil.rmtree(os.path.join(base_path, 'deflex', '2014', 'results_cbc'))
