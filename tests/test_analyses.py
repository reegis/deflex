# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
import deflex.tools

__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


from deflex import analyses
from deflex import post_processing


def test_flow_results():
    """The flow results are not fetched or calculated correctly.n"""
    my_fn = deflex.tools.fetch_example_results("de02.dflx")
    my_res = post_processing.restore_results(my_fn)
    mo = analyses.merit_order_from_results(my_res)
    seq = analyses.get_flow_results(my_res)

    for trsf in seq["cost", "specific", "trsf"].columns:
        for w in [("cost", "costs_total"), ("emission", "spec_emission")]:
            base = ("trsf",) + tuple(trsf)
            weight_spec = (w[0], "specific") + base
            weight_abs = (w[0], "absolute") + base
            val_absolute = ("values", "absolute") + base
            if seq[val_absolute].sum() > 0:
                assert seq[weight_spec].max() == mo.loc[base][w[1]]
            if seq[val_absolute].sum() > 0:
                assert round(
                    seq[weight_abs].div(seq[val_absolute]).max(), 3
                ) == round(mo.loc[base][w[1]], 3)
