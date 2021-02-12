# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
from unittest.mock import MagicMock

import pandas as pd
from reegis import config
from scenario_builder import demand
from scenario_builder import feedin
from scenario_builder import powerplants

from deflex import __file__ as dfile
from deflex import config as cfg
from deflex import scenario_creator
from deflex import scenario_tools as st
from deflex.geometries import deflex_power_lines
from deflex.geometries import deflex_regions


class TestScenarioCreation:
    @classmethod
    def setup_class(cls):
        path = os.path.join(
            os.path.dirname(__file__), "data", "deflex_2014_de21_test_csv"
        )
        sc = st.DeflexScenario()
        sc.load_csv(path)
        cls.tables = sc.table_collection
        tmp_tables = {}
        parameter = {
            "costs_source": "ewi",
            "downtime_bioenergy": 0.1,
            "limited_transformer": "bioenergy",
            "local_fuels": "district heating",
            "map": "de21",
            "mobility_other": "petrol",
            "round": 1,
            "separate_heat_regions": "de22",
            "copperplate": False,
            "default_transmission_efficiency": 0.9,
            "group_transformer": False,
            "heat": True,
            "use_CO2_costs": False,
            "use_downtime_factor": True,
            "use_variable_costs": False,
            "year": 2014,
        }
        config.init(paths=[os.path.dirname(dfile)])
        for option, value in parameter.items():
            cfg.tmp_set("creator", option, str(value))
            config.tmp_set("creator", option, str(value))

        name = "heat_demand_deflex"
        fn = os.path.join(os.path.dirname(__file__), "data", name + ".csv")
        tmp_tables[name] = pd.read_csv(fn, index_col=[0], header=[0, 1])

        name = "transformer_balance"
        fn = os.path.join(os.path.dirname(__file__), "data", name + ".csv")
        tmp_tables[name] = pd.read_csv(fn, index_col=[0, 1, 2], header=[0])

        powerplants.scenario_powerplants = MagicMock(
            return_value={
                "volatile_source": cls.tables["volatile_source"],
                "transformer": cls.tables["transformer"],
            }
        )

        powerplants.scenario_chp = MagicMock(
            return_value={
                "chp_hp": cls.tables["chp_hp"],
                "transformer": cls.tables["transformer"],
            }
        )

        feedin.scenario_feedin = MagicMock(
            return_value=cls.tables["volatile_series"]
        )
        demand.scenario_demand = MagicMock(
            return_value=cls.tables["demand_series"]
        )

        name = "de21"

        polygons = deflex_regions(rmap=parameter["map"], rtype="polygons")
        lines = deflex_power_lines(parameter["map"]).index
        cls.table_collection = scenario_creator.create_scenario(
            polygons, 2014, name, lines
        )
        for key in cls.tables.keys():
            print(key)
            fn = "/home/uwe/{0}_{1}.csv".format(key, "{0}")
            print(fn)
            cls.tables[key].to_csv(fn.format("a"))
            cls.table_collection[key].to_csv(fn.format("b"))

    @classmethod
    def teardown_class(cls):
        pass

    def test_volatile_source(self):
        pd.testing.assert_frame_equal(
            self.tables["volatile_source"],
            self.table_collection["volatile_source"],
        )

    def test_storages(self):
        a = self.tables["storages"].apply(pd.to_numeric)
        b = self.table_collection["storages"].apply(pd.to_numeric)
        for col in a.columns:
            pd.testing.assert_series_equal(a[col], b[col])
        # pd.testing.assert_frame_equal(a, b)

    def test_demand_series(self):
        pd.testing.assert_frame_equal(
            self.tables["demand_series"],
            self.table_collection["demand_series"],
        )

    def test_transmission(self):
        pd.testing.assert_frame_equal(
            self.tables["transmission"].apply(pd.to_numeric),
            self.table_collection["transmission"].apply(pd.to_numeric),
        )

    def test_transformer(self):
        pd.testing.assert_frame_equal(
            self.tables["transformer"],
            self.table_collection["transformer"],
        )

    def test_meta(self):
        pd.testing.assert_frame_equal(
            self.tables["meta"].astype(str).sort_index(),
            self.table_collection["meta"].astype(str).sort_index(),
        )

    def test_commodity_source(self):
        pd.testing.assert_frame_equal(
            self.tables["commodity_source"],
            self.table_collection["commodity_source"],
        )

    def test_mobility_series(self):
        pd.testing.assert_frame_equal(
            self.tables["mobility_series"],
            self.table_collection["mobility_series"],
        )

    def test_mobility(self):
        self.table_collection["mobility"]["efficiency"] = pd.to_numeric(
            self.table_collection["mobility"]["efficiency"]
        )
        pd.testing.assert_frame_equal(
            self.tables["mobility"],
            self.table_collection["mobility"],
        )

    def test_chp_hp(self):
        pd.testing.assert_frame_equal(
            self.tables["chp_hp"],
            self.table_collection["chp_hp"],
        )

    def test_decentralised_heat(self):
        pd.testing.assert_frame_equal(
            self.tables["decentralised_heat"],
            self.table_collection["decentralised_heat"],
        )

    def test_volatile_series(self):
        pd.testing.assert_frame_equal(
            self.tables["volatile_series"],
            self.table_collection["volatile_series"],
        )

    def test_length(self):
        assert sorted(list(self.tables.keys())) == sorted(
            list(self.table_collection.keys())
        )
