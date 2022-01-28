# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
# import deflex.tools

__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

from oemof.solph import Bus, GenericStorage, Sink, Source, Transformer

from deflex import postprocessing, scenario
from deflex.tools import fetch_test_files, restore_results


def test_string_label():
    label = scenario.nodes.Label(
        cat="my*category", tag="my+tag", subtag="my-subtag", region="my-region"
    )
    assert label.tag == "my+tag"
    assert postprocessing.analyses.label2str(label) == (
        "my*category_my+tag_my-subtag_my-region"
    )


class TestAnalysis:
    @classmethod
    def setup_class(cls):
        cls.results = restore_results(fetch_test_files("de02_no-heat.dflx"))

    def test_all_nodes_from_results(self):
        nodes = postprocessing.analyses.get_all_nodes_from_results(
            self.results
        )
        assert len(nodes) == 141
        # 15 + 26 + 87 + 1 + 12 = 141
        assert len([n for n in nodes if isinstance(n, Sink)]) == 15
        assert len([n for n in nodes if isinstance(n, Source)]) == 26
        assert len([n for n in nodes if isinstance(n, Transformer)]) == 87
        assert len([n for n in nodes if isinstance(n, GenericStorage)]) == 1
        assert len([n for n in nodes if isinstance(n, Bus)]) == 12
        print(set([type(n) for n in nodes]))

    def test_graph_and_nodes(self):
        graph = postprocessing.DeflexGraph(self.results)
        nodes = postprocessing.analyses.get_all_nodes_from_results(
            self.results
        )
        n = 0
        for k, v in graph.group_nodes_by_type().items():
            n += len(v)
            assert len([n for n in nodes if isinstance(n, k)]) == len(v)
        assert n == len(nodes)
        print(n)

    def test_nodes_to_table(self):
        """
        The sum of all inputs must be the sum of all outputs.
        In the de02-example the sum of the outflows of the electricity Bus must
        equal the input flows of the storage and the demand Sink.
        """
        all_nodes = postprocessing.nodes2table(self.results)
        assert int(all_nodes.sum()["out"]) == int(all_nodes.sum()["in"])
        assert int(
            all_nodes.loc[("Bus", "electricity", "all", "all", "DE01"), "out"]
        ) == int(
            all_nodes.loc["Sink", "electricity demand"]["in"].sum()
            + all_nodes.loc["GenericStorage"]["in"].sum()
        )

    def test_resource_parameter(self):
        nodes = postprocessing.analyses.get_all_nodes_from_results(
            self.results
        )
        buses = [
            n
            for n in nodes
            if isinstance(n, Bus) and n.label.cat == "commodity"
        ]
        all_costs = 0
        emission = 0
        number = 0
        for bus in buses:
            number += 1
            all_costs += postprocessing.analyses.get_resource_parameters(
                self.results, bus
            )["scalars"]["variable_costs"]
            emission += postprocessing.analyses.get_resource_parameters(
                self.results, bus
            )["scalars"]["emission"]
        assert round(all_costs / number, 2) == 19.19
        assert round(emission / number, 4) == 0.1804

    def test_converter_parameters(self):
        nodes = postprocessing.analyses.get_all_nodes_from_results(
            self.results
        )
        transformer = [
            n
            for n in nodes
            if isinstance(n, Transformer) and n.label.subtag == "lignite"
        ]
        cp = postprocessing.analyses.fetch_converter_parameters(
            self.results, transformer
        )
        assert cp["fuel"].unique() == ["lignite, DE"]
        assert round(cp["efficiency, electricity"].mean(), 3) == 0.361

    def test_time_index(self):
        time_index = postprocessing.analyses.get_time_index(self.results)
        assert len(time_index) == 48
        assert time_index[5].year == 2014
        assert time_index[20].hour == 20

    def test_parameter_of_commodity_sources(self):
        postprocessing.fetch_parameter_of_commodity_sources(self.results)

    def test_marginal_costs(self):
        nodes = postprocessing.analyses.get_all_nodes_from_results(
            self.results
        )
        transformer = [
            n
            for n in nodes
            if isinstance(n, Transformer) and n.label.subtag == "hard coal"
        ]
        cp = postprocessing.analyses.fetch_converter_parameters(
            self.results, transformer
        )
        mc = postprocessing.calculate_marginal_costs(cp)
        assert round(mc["marginal costs"].mean(), 2) == 47.51

    def test_electricity_flows(self):
        postprocessing.analyses.fetch_electricity_flows(self.results)

    def test_calculate_key_values(self):
        postprocessing.calculate_key_values(self.results)

    def test_combined_bus_balance(self):
        postprocessing.get_combined_bus_balance(self.results)

    def test_converter_balance(self):
        postprocessing.get_converter_balance(self.results)
