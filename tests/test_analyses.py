# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
# import deflex.tools

__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

# from deflex import postprocessing
import pandas as pd

from deflex.postprocessing import analyses


def test_no_time_step_cycles():
    test_cycle = pd.DataFrame({
        "other-converter_Electrolysis_electricity_DE": [0, 2, 3, 4, 0, 6],
        "commodity_all_H2_DE": [7, 0, 9, 10, 11, 0],
        "power-plant_H2_H2_DE01": [13, 14, 0, 16, 17, 18],
        "electricity_all_all_DE01": [19, 20, 21, 0, 23, 24],
    })
    assert analyses.detect_time_step_cycle(test_cycle) is None


def test_time_step_cycles():
    test_cycle = pd.DataFrame({
        "other-converter_Electrolysis_electricity_DE": [0, 2, 3, 4, 0, 6],
        "commodity_all_H2_DE": [7, 8, 9, 10, 11, 0],
        "power-plant_H2_H2_DE01": [13, 14, 0, 16, 17, 18],
        "electricity_all_all_DE01": [19, 20, 21, 0, 23, 24],
    })
    rows = analyses.detect_time_step_cycle(test_cycle)
    assert rows is not None
    assert len(rows) == 1
    assert rows.index[0] == 1

# def test_flow_results():
#     """The flow results are not fetched or calculated correctly.n"""
#     my_fn = deflex.tools.fetch_test_files("de02_heat.dflx")
#     my_res = postprocessing.restore_results(my_fn)
#     mo = pp.merit_order_from_results(my_res)
#     seq = analyses.get_flow_results(my_res)
#
#     print(seq)
#
#     for trsf in seq["cost", "specific"].columns:
#         print(trsf)
#         for w in [("cost", "costs_total"), ("emission", "spec_emission")]:
#             base = ("trsf",) + tuple(trsf)
#             weight_spec = (w[0], "specific") + base
#             weight_abs = (w[0], "absolute") + base
#             val_absolute = ("values", "absolute") + base
#             if seq[val_absolute].sum() > 0:
#                 assert seq[weight_spec].max() == mo.loc[base][w[1]]
#             if seq[val_absolute].sum() > 0:
#                 assert round(
#                     seq[weight_abs].div(seq[val_absolute]).max(), 3
#                 ) == round(mo.loc[base][w[1]], 3)