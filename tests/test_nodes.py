# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""


from deflex import main
from deflex import scenario
from deflex import nodes as nd
from deflex.tools import fetch_test_files


class TestNodes:
    @classmethod
    def setup_class(cls):
        fn = fetch_test_files("de03_fictive_csv")
        cls.sc = main.load_scenario(fn, file_type="csv")
        cls.sc.initialise_energy_system()

    def test_fuel_bus_with_source(self):
        nodes = scenario.NodeDict()
        nodes = nd.create_fuel_bus_with_source(
            nodes, "lignite", "DE", self.sc.input_data
        )
        self.sc.add_nodes_to_es(nodes)
        src = [v for k, v in nodes.items() if k.cat == "source"][0]
        trg = [v for k, v in nodes.items() if k.cat == "bus"][0]
        flow = self.sc.es.flows()[(src, trg)]
        assert flow.variable_costs[0] == 11.988
        assert flow.nominal_value is None
        assert flow.emission[0] == 0.404
