# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

Copyright (c) 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

from nose.tools import assert_raises_regexp
import os
from deflex import scenario_tools


def test_scenario_building():
    sc = scenario_tools.DeflexScenario(name='test', year=2014)
    csv_path = os.path.join(
        os.path.dirname(__file__), 'data', 'deflex_2014_de21_test_csv')
    sc.load_csv(csv_path)
    sc.table2es()

def test_node_dict(self):
    nc = scenario_tools.NodeDict()
    nc['g'] = 5
    nc['h'] = 6
    msg = ("Key 'g' already exists. Duplicate keys are not allowed in a "
           "node dictionary.")
    with assert_raises_regexp(KeyError, msg):
        nc['g'] = 7
