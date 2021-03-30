# -*- coding: utf-8 -*-

"""
Test the postprocessing module. There are many doctests within the module.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
import pandas as pd
from oemof import solph

from deflex import postprocessing as pp
from deflex.tools import fetch_test_files


class TestReshapeBusView:
    @classmethod
    def setup_class(cls):
        fn = fetch_test_files("de21_no-heat.dflx")
        my_es = pp.restore_scenario(fn).es
        my_buses = sorted(
            pp.search_nodes(
                my_es.results, node_type=solph.Bus, tag="electricity"
            )
        )

        m_cols = pd.MultiIndex(
            levels=[[], [], [], [], []], codes=[[], [], [], [], []]
        )

        data = pd.DataFrame(columns=m_cols)

        agg1 = [("cat", "line", "all"), ("tag", "pp", -1)]
        agg2 = [("cat", "line", "all"), ("tag", "pp", 1)]

        df1 = pp.reshape_bus_view(my_es.results, my_buses, aggregate=agg1)
        df2 = pp.reshape_bus_view(my_es.results, my_buses)
        df3 = pp.reshape_bus_view(my_es.results, my_buses, aggregate=agg2)
        df4 = pp.reshape_bus_view(my_es.results, my_buses[0], data=data)

        cls.df1 = df1.groupby(level=[1, 2, 3, 4], axis=1).sum().sort_index(1)
        cls.df2 = df2.groupby(level=[1, 2, 3, 4], axis=1).sum().sort_index(1)
        cls.df3 = df3.groupby(level=[1, 2, 3, 4], axis=1).sum().sort_index(1)
        cls.df4 = df4.groupby(level=[1, 2, 3, 4], axis=1).sum().sort_index(1)

    def test_electricity_line(self):
        assert list(self.df1["in", "line", "electricity"].columns[:5]) == [
            "all"
        ]
        assert list(self.df2["in", "line", "electricity"].columns[:5]) == [
            "DE01",
            "DE02",
            "DE03",
            "DE04",
            "DE05",
        ]
        assert list(self.df3["in", "line", "electricity"].columns[:5]) == [
            "all"
        ]
        assert list(self.df4["in", "line", "electricity"].columns)[:5] == [
            "DE03",
            "DE04",
            "DE13",
            "DE14",
            "DE15",
        ]

    def test_power_plants(self):
        assert list(self.df1["in", "trsf", "pp"].columns[:4]) == [
            "bioenergy",
            "hard coal",
            "lignite",
            "natural gas",
        ]
        assert list(self.df2["in", "trsf", "pp"].columns[:4]) == [
            "bioenergy_038",
            "bioenergy_042",
            "bioenergy_045",
            "hard coal_023",
        ]
        assert list(self.df3["in", "trsf", "pp"].columns[:4]) == [
            "018",
            "023",
            "025",
            "027",
        ]
