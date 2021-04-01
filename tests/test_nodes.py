# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
import pytest
from oemof import solph

from deflex import main
from deflex import nodes as nd
from deflex import scenario
from deflex.tools import fetch_test_files


class TestNodes:
    @classmethod
    def setup_class(cls):
        fn = fetch_test_files("de03_fictive_csv")
        cls.sc = main.load_scenario(fn, file_type="csv")

    def test_fuel_bus_with_source(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nodes = nd.create_fuel_bus_with_source(
            nodes, "lignite", "DE", self.sc.input_data
        )
        nodes_copy = nodes.copy()
        nodes = nd.create_fuel_bus_with_source(
            nodes, "lignite", "DE", self.sc.input_data
        )
        assert nodes == nodes_copy
        self.sc.add_nodes_to_es(nodes)
        src = [v for k, v in nodes.items() if k.cat == "source"][0]
        trg = [v for k, v in nodes.items() if k.cat == "bus"][0]
        flow = self.sc.es.flows()[(src, trg)]
        assert flow.variable_costs[0] == 11.988
        assert flow.nominal_value is None
        assert flow.emission[0] == 0.404

    def test_electricity_bus(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.create_electricity_bus(nodes, "DE01")
        nodes_copy = nodes.copy()
        nd.create_electricity_bus(nodes, "DE01")
        assert nodes == nodes_copy
        assert len(nodes.keys()) == 1
        assert list(nodes.keys())[0] == nd.Label(
            "bus", "electricity", "all", "DE01"
        )

    def test_volatile_sources(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.add_volatile_sources(self.sc.input_data, nodes)
        self.sc.add_nodes_to_es(nodes)
        src = [v for k, v in nodes.items() if k.cat == "source"]
        for s in src:
            region = s.label.region
            trg = [
                v
                for k, v in nodes.items()
                if k.cat == "bus" and k.region == region
            ][0]
            flow = self.sc.es.flows()[(s, trg)]
            idx = (region, s.label.subtag)
            assert (
                flow.fix.sum()
                == self.sc.input_data["volatile series"][idx].sum()
            )
            assert (
                flow.nominal_value
                == self.sc.input_data["volatile plants"].loc[idx, "capacity"]
            )
            flow.nominal_value = 12.29
            assert flow.emission[0] == 0
            assert trg.label == nd.Label("bus", "electricity", "all", region)
        s0 = sorted(src)[0]
        t0 = [
            v
            for k, v in nodes.items()
            if k.cat == "bus" and k.region == s0.label.region
        ][0]
        flow = self.sc.es.flows()[(s0, t0)]
        assert flow.fix.sum() == 24.0
        assert flow.nominal_value == 12.29

    def test_decentralised_heating_systems(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.add_decentralised_heating_systems(self.sc.input_data, nodes)
        assert len(nodes) == 34
        self.sc.add_nodes_to_es(nodes)
        oil_heat_bus = [
            v
            for k, v in nodes.items()
            if k.cat == "bus" and k.tag == "heat" and k.subtag == "oil"
        ][0]
        oil_heat_demand = [
            v
            for k, v in nodes.items()
            if k.cat == "demand" and k.tag == "heat" and k.subtag == "oil"
        ][0]
        oil_heat_transformer = [
            v
            for k, v in nodes.items()
            if k.cat == "trsf" and k.tag == "heat" and k.subtag == "oil"
        ][0]
        flow = self.sc.es.flows()[(oil_heat_bus, oil_heat_demand)]
        idx = ("DE", "oil")
        assert (
            flow.fix.sum()
            == self.sc.input_data["heat demand series"][idx].sum()
        )
        assert int(flow.fix.sum()) == 2593093
        assert flow.nominal_value == 1
        assert (
            oil_heat_transformer.conversion_factors[oil_heat_bus][0]
            == self.sc.input_data["decentralised heat"].loc[idx, "efficiency"]
        )

    def test_add_electricity_demand(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.create_electricity_bus(nodes, "DE01")
        self.sc.input_data["electricity demand series"][("DE01", "new")] = 0
        nd.add_electricity_demand(self.sc.input_data, nodes)
        self.sc.add_nodes_to_es(nodes)
        snk = [v for k, v in nodes.items() if k.cat == "demand"]
        values = {
            "demand_electricity_all_DE01": 1509776,
            "demand_electricity_all_DE02": 1006517,
        }
        for s in snk:
            region = s.label.region
            bus = [
                v
                for k, v in nodes.items()
                if k.cat == "bus" and k.region == region
            ][0]
            flow = self.sc.es.flows()[(bus, s)]
            idx = (region, s.label.subtag)
            assert (
                flow.fix.sum()
                == self.sc.input_data["electricity demand series"][idx].sum()
            )
            assert int(flow.fix.sum()) == values[str(s)]
            assert flow.nominal_value == 1

    def test_district_heating_demand(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        bus_label = nd.Label("bus", "heat", "district", "DE01")
        nodes[bus_label] = solph.Bus(label=bus_label)
        self.sc.input_data["heat demand series"][
            ("DE04", "district heating")
        ] = 0
        nd.add_district_heating_demand(self.sc.input_data, nodes)
        self.sc.add_nodes_to_es(nodes)
        snk = [v for k, v in nodes.items() if k.cat == "demand"]
        values = {"DE01": 1276776}
        for s in snk:
            region = s.label.region
            bus = [
                v
                for k, v in nodes.items()
                if k.cat == "bus" and k.region == region
            ][0]
            flow = self.sc.es.flows()[(bus, s)]
            idx = (region, "district heating")
            assert (
                flow.fix.sum()
                == self.sc.input_data["heat demand series"][idx].sum()
            )
            assert int(flow.fix.sum()) == values[region]
            assert flow.nominal_value == 1

    def test_transmission_lines_between_electricity_nodes_errors(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        msg = "Bus bus_electricity_all_{0} missing for power line from bus_"
        with pytest.raises(ValueError, match=msg.format("DE01")):
            nd.add_transmission_lines_between_electricity_nodes(
                self.sc.input_data, nodes
            )
        nd.create_electricity_bus(nodes, "DE01")
        with pytest.raises(ValueError, match=msg.format("DE02")):
            nd.add_transmission_lines_between_electricity_nodes(
                self.sc.input_data, nodes
            )

    def test_transmission_lines_between_electricity_nodes(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.create_electricity_bus(nodes, "DE01")
        nd.create_electricity_bus(nodes, "DE02")
        nd.create_electricity_bus(nodes, "DE03")
        nd.add_transmission_lines_between_electricity_nodes(
            self.sc.input_data, nodes
        )
        self.sc.add_nodes_to_es(nodes)
        ebus1 = [
            v
            for k, v in nodes.items()
            if isinstance(v, solph.Bus) and k.region == "DE01"
        ][0]
        ebus2 = [
            v
            for k, v in nodes.items()
            if isinstance(v, solph.Bus) and k.region == "DE02"
        ][0]
        ebus3 = [
            v
            for k, v in nodes.items()
            if isinstance(v, solph.Bus) and k.region == "DE03"
        ][0]
        trsf1_2 = [
            v
            for k, v in nodes.items()
            if isinstance(v, solph.Transformer)
            and k.subtag == "DE01"
            and k.region == "DE02"
        ][0]
        trsf1_3 = [
            v
            for k, v in nodes.items()
            if isinstance(v, solph.Transformer)
            and k.subtag == "DE01"
            and k.region == "DE03"
        ][0]
        trsf3_1 = [
            v
            for k, v in nodes.items()
            if isinstance(v, solph.Transformer)
            and k.subtag == "DE03"
            and k.region == "DE01"
        ][0]
        flow1_2 = self.sc.es.flows()[(trsf1_2, ebus2)]
        flow1_3 = self.sc.es.flows()[(trsf1_3, ebus3)]
        flow3_1 = self.sc.es.flows()[(trsf3_1, ebus1)]
        assert flow1_2.nominal_value is None
        assert flow1_3.nominal_value == 500.0
        assert flow3_1.nominal_value == 500.0
        assert (
            flow1_3.nominal_value
            == self.sc.input_data["power lines"].loc["DE01-DE03", "capacity"]
        )
        assert trsf1_3.conversion_factors[ebus3][0] == 0.95
        assert trsf1_2.conversion_factors[ebus2][0] == 1.0

    def test_check_in_out_buses(self):
        pass

    def test_power_plants(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.add_power_plants(self.sc.input_data, nodes)
        self.sc.input_data["power plants"].drop(
            ["annual electricity limit", "downtime_factor", "variable_costs"],
            axis=1,
            inplace=True,
        )
        nodes = {k: v for k, v in nodes.items() if k.cat != "trsf"}
        nd.add_power_plants(self.sc.input_data, nodes)

    def test_heat_and_chp_plants(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.add_heat_and_chp_plants(self.sc.input_data, nodes)
        nodes_copy = nodes.copy()
        nodes = {k: v for k, v in nodes.items() if k.cat != "trsf"}
        nd.add_heat_and_chp_plants(self.sc.input_data, nodes)
        for key, value in nodes.items():
            assert value.label == nodes_copy[key].label
        self.sc.add_nodes_to_es(nodes)

        src = self.sc.es.groups[
            str(nd.Label("bus", "commodity", "natural gas", "DE"))
        ]
        chp1 = self.sc.es.groups[
            str(nd.Label("trsf", "chp", "natural gas", "DE01"))
        ]
        hp2 = self.sc.es.groups[
            str(nd.Label("trsf", "hp", "natural gas", "DE01"))
        ]
        heat = self.sc.es.groups[
            str(nd.Label("bus", "heat", "district", "DE01"))
        ]
        elec = self.sc.es.groups[
            str(nd.Label("bus", "electricity", "all", "DE01"))
        ]
        print(self.sc.es.groups[str(chp1)])
        fflow1 = self.sc.es.flows()[(src, chp1)]
        eflow1 = self.sc.es.flows()[(chp1, elec)]
        hflow1 = self.sc.es.flows()[(chp1, heat)]
        fflow2 = self.sc.es.flows()[(src, hp2)]
        hflow2 = self.sc.es.flows()[(hp2, heat)]

        assert eflow1.nominal_value is None
        assert int(fflow1.nominal_value) == 27440
        assert hflow1.nominal_value is None
        assert round(fflow1.summed_max, 1) == 15.0
        assert chp1.conversion_factors[elec][0] == 0.25
        assert chp1.conversion_factors[heat][0] == 0.41
        assert hp2.conversion_factors[heat][0] == 0.75
        assert fflow2.nominal_value is None
        assert int(hflow2.nominal_value) == 6775
        assert round(hflow2.summed_max, 1) == 17.7

    def test_electricity_storages(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.create_electricity_bus(nodes, "DE01")
        nd.add_electricity_storages(self.sc.input_data, nodes)

    def test_mobility(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.add_mobility(self.sc.input_data, nodes)

    def test_shortage_excess(self):
        self.sc.initialise_energy_system()
        nodes = scenario.NodeDict()
        nd.add_shortage_excess(nodes)
