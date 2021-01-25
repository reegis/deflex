# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

# import os
# from unittest.mock import MagicMock
# import pandas as pd
# from deflex import scenario_builder, geometries, demand


# def test_scenario_creation():
#     data = {}
#     for name in ["volatile_series", "demand_series"]:
#         fn = os.path.join(
#             os.path.dirname(__file__),
#             "data",
#             "deflex_2014_de21_test_csv",
#             name + ".csv",
#         )
#         data[name] = pd.read_csv(fn, index_col=[0], header=[0, 1])
#
#     name = "heat_demand_deflex"
#     fn = os.path.join(os.path.dirname(__file__), "data", name + ".csv")
#     data[name] = pd.read_csv(fn, index_col=[0], header=[0, 1])
#
#     name = "transformer_balance"
#     fn = os.path.join(os.path.dirname(__file__), "data", name + ".csv")
#     data[name] = pd.read_csv(fn, index_col=[0, 1, 2], header=[0])
#
#     basic_scenario.scenario_feedin = MagicMock(
#         return_value=data["volatile_series"]
#     )
#     basic_scenario.scenario_demand = MagicMock(
#         return_value=data["demand_series"]
#     )
#     energy_balance.get_transformation_balance_by_region = MagicMock(
#         return_value=data["transformer_balance"]
#     )
#     demand.get_heat_profiles_deflex = MagicMock(
#         return_value=data["heat_demand_deflex"]
#     )
#     regions = geometries.deflex_regions(rmap="de21")
#     table_collection = basic_scenario.create_scenario(regions, 2014, "de21")
#     eq_(
#         sorted(list(table_collection.keys())),
#         sorted(
#             [
#                 "meta",
#                 "storages",
#                 "transformer",
#                 "volatile_source",
#                 "chp_hp",
#                 "transmission",
#                 "decentralised_heat",
#                 "commodity_source",
#                 "volatile_series",
#                 "demand_series",
#                 "mobility_energy_content",
#                 "mobility_mileage",
#                 "mobility_spec_demand",
#             ]
#         ),
#     )
#     eq_(len(list(table_collection.keys())), 13)
