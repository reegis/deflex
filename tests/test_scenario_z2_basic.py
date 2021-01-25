# -*- coding: utf-8 -*-

"""
Processing a list of power plants in Germany.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

# from unittest.mock import MagicMock
# from nose.tools import ok_, eq_
# import os
# from deflex import scenario_tools, config as cfg
#
#
# def clean_time_series():
#     sc = scenario_tools.DeflexScenario(name="test", year=2014)
#     csv_path = os.path.join(
#         os.path.dirname(__file__), "data", "deflex_2014_de21_test_csv"
#     )
#     sc.load_csv(csv_path)
#     # before cleaning
#     ok_(("DE05", "solar") in sc.table_collection["volatile_series"])
#     ok_(("DE04", "district heating") in sc.table_collection["demand_series"])
#
#     sc.table_collection["volatile_source"].loc["DE05", "solar"] = 0
#     sc.table_collection["demand_series"]["DE04", "district heating"] = 0
#     basic_scenario.clean_time_series(sc.table_collection)
#
#     # after cleaning
#     ok_(("DE05", "solar") not in sc.table_collection["volatile_series"])
#     ok_(
#         ("DE04", "district heating")
#         not in sc.table_collection["demand_series"]
#     )
#
#
# def scenario_creation_main():
#     sc = scenario_tools.DeflexScenario(name="test", year=2014)
#     csv_path = os.path.join(
#         os.path.dirname(__file__), "data", "deflex_2014_de21_test_csv"
#     )
#     sc.load_csv(csv_path)
#     basic_scenario.create_scenario = MagicMock(
#         return_value=sc.table_collection
#     )
#     cfg.tmp_set(
#         "paths",
#         "scenario",
#         os.path.join(os.path.expanduser("~"), "deflex_tmp_test_dir"),
#     )
#
#     fn = basic_scenario.create_basic_scenario(2014, "de21", only_out="csv")
#     ok_(fn.xls is None)
#     eq_(
#         fn.csv[-70:],
#         (
#             "deflex_tmp_test_dir/deflex/2014/"
#             "deflex_2014_de21_heat_no-reg-merit_csv"
#         ),
#     )
#
#     fn = basic_scenario.create_basic_scenario(2014, "de21", only_out="xls")
#     ok_(fn.csv is None)
#     eq_(
#         fn.xls[-70:],
#         (
#             "deflex_tmp_test_dir/deflex/2014/"
#             "deflex_2014_de21_heat_no-reg-merit.xls"
#         ),
#     )
#
#     fn = basic_scenario.create_basic_scenario(
#         2014, "de21", csv_dir="fancy_csv", xls_name="fancy.xls"
#     )
#     eq_(fn.xls[-41:], "deflex_tmp_test_dir/deflex/2014/fancy.xls")
#     eq_(fn.csv[-41:], "deflex_tmp_test_dir/deflex/2014/fancy_csv")
