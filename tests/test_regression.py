# -*- coding: utf-8 -*-

"""
Regression tests.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


from deflex import geometries


def test_prevent_mutable_region_object():
    """Make sure the region object is not mutated."""
    reg = geometries.deflex_regions("de21")
    assert reg.geometry.iloc[0].geom_type == "MultiPolygon"
    assert geometries.divide_off_and_onshore(reg).offshore == [
        "DE19",
        "DE20",
        "DE21",
    ]
    assert reg.geometry.iloc[0].geom_type == "MultiPolygon"
