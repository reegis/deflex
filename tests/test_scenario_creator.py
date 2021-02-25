# -*- coding: utf-8 -*-

"""
Test the main module

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
import shutil
from unittest.mock import MagicMock

import pandas as pd
from reegis import config
from scenario_builder import demand
from scenario_builder import feedin
from scenario_builder import powerplants

from deflex import __file__ as dfile
from deflex import config as cfg
from deflex import scenario_creator
from deflex import scenario as st
from deflex.geometries import deflex_power_lines
from deflex.geometries import deflex_regions


class TestScenarioCreationFull:
    @classmethod
    def setup_class(cls):
        path = os.path.join(
            os.path.dirname(__file__), "data", "deflex_2014_de21_test_csv"
        )
        sc = st.DeflexScenario()
        sc.read_csv(path)
        cls.tables = sc.input_data
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
                "volatile plants": cls.tables["volatile plants"],
                "power plants": cls.tables["power plants"],
            }
        )

        powerplants.scenario_chp = MagicMock(
            return_value={
                "chp-heat plants": cls.tables["chp-heat plants"],
                "power plants": cls.tables["power plants"],
            }
        )

        feedin.scenario_feedin = MagicMock(
            return_value=cls.tables["volatile series"]
        )
        demand.scenario_demand = MagicMock(
            return_value=cls.tables["demand series"]
        )

        name = "de21"

        polygons = deflex_regions(rmap=parameter["map"], rtype="polygons")
        lines = deflex_power_lines(parameter["map"]).index
        cls.input_data = scenario_creator.create_scenario(
            polygons, 2014, name, lines
        )

    @classmethod
    def teardown_class(cls):
        pass

    def test_volatile_source(self):
        pd.testing.assert_frame_equal(
            self.tables["volatile plants"],
            self.input_data["volatile plants"],
        )

    def test_storages(self):
        a = self.tables["storages"].apply(pd.to_numeric).astype(float)
        b = self.input_data["storages"].apply(pd.to_numeric)
        for col in a.columns:
            pd.testing.assert_series_equal(a[col], b[col])
        # pd.testing.assert_frame_equal(a, b)

    def test_demand_series(self):
        print(list(self.input_data.keys()))
        pd.testing.assert_frame_equal(
            self.tables["demand series"],
            self.input_data["demand series"],
        )

    def test_transmission(self):
        self.tables["power lines"].to_csv("/home/uwe/mobt.csv")
        self.input_data["power lines"].to_csv("/home/uwe/mobi.csv")
        pd.testing.assert_frame_equal(
            self.tables["power lines"].apply(pd.to_numeric),
            self.input_data["power lines"].apply(pd.to_numeric),
            rtol=1e-3
        )

    def test_transformer(self):
        pd.testing.assert_frame_equal(
            self.tables["power plants"],
            self.input_data["power plants"],
        )

    def test_meta(self):

        pd.testing.assert_series_equal(
            self.tables["general"].apply(str).sort_index(),
            self.input_data["general"].apply(str).sort_index(),
        )

    def test_commodity_source(self):
        pd.testing.assert_frame_equal(
            self.tables["commodity sources"],
            self.input_data["commodity sources"],
        )

    def test_mobility_series(self):
        pd.testing.assert_frame_equal(
            self.tables["mobility series"],
            self.input_data["mobility series"],
        )

    def test_mobility(self):
        self.input_data["mobility"]["efficiency"] = pd.to_numeric(
            self.input_data["mobility"]["efficiency"]
        )
        pd.testing.assert_frame_equal(
            self.tables["mobility"],
            self.input_data["mobility"],
        )

    def test_chp_hp(self):
        pd.testing.assert_frame_equal(
            self.tables["chp-heat plants"],
            self.input_data["chp-heat plants"],
        )

    def test_decentralised_heat(self):
        pd.testing.assert_frame_equal(
            self.tables["decentralised heat"],
            self.input_data["decentralised heat"],
        )

    def test_volatile_series(self):
        pd.testing.assert_frame_equal(
            self.tables["volatile series"],
            self.input_data["volatile series"],
        )

    def test_length(self):
        assert len(self.tables.keys()) == len(self.input_data.keys())
        assert sorted(list(self.tables.keys())) == sorted(
            list(self.input_data.keys())
        )


class TestScenarioCreationPart:
    @classmethod
    def setup_class(cls):
        path = os.path.join(
            os.path.dirname(__file__), "data", "deflex_2014_de21_part_csv"
        )
        sc = st.DeflexScenario()
        sc.read_csv(path)
        cls.tables = sc.input_data
        tmp_tables = {}

        name = "heat_demand_deflex"
        fn = os.path.join(os.path.dirname(__file__), "data", name + ".csv")
        tmp_tables[name] = pd.read_csv(fn, index_col=[0], header=[0, 1])

        name = "transformer_balance"
        fn = os.path.join(os.path.dirname(__file__), "data", name + ".csv")
        tmp_tables[name] = pd.read_csv(fn, index_col=[0, 1, 2], header=[0])

        powerplants.scenario_powerplants = MagicMock(
            return_value={
                "volatile plants": cls.tables["volatile plants"],
                "power plants": cls.tables["power plants"],
            }
        )

        feedin.scenario_feedin = MagicMock(
            return_value=cls.tables["volatile series"]
        )
        demand.scenario_demand = MagicMock(
            return_value=cls.tables["demand series"]
        )

        name = "de21"

        my_parameter = {
            "copperplate": False,
            "group_transformer": True,
            "heat": False,
            "use_variable_costs": True,
            "use_CO2_costs": True,
            "map": "de21",
        }

        my_name = "deflex"
        for k, v in my_parameter.items():
            my_name += "_" + str(k) + "-" + str(v)

        polygons = deflex_regions(rmap=my_parameter["map"], rtype="polygons")
        lines = deflex_power_lines(my_parameter["map"]).index
        base = os.path.join(os.path.expanduser("~"), ".tmp_x345234dE_deflex")
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, "deflex_test{0}")

        scenario_creator.create_basic_reegis_scenario(
            name=name,
            regions=polygons,
            lines=lines,
            parameter=my_parameter,
            excel_path=path.format(".xlsx"),
            csv_path=path.format("_csv"),
        )

        sc_new = st.DeflexScenario()
        sc_new.read_csv(path.format("_csv"))
        cls.input_data = sc_new.input_data

    @classmethod
    def teardown_class(cls):
        base = os.path.join(os.path.expanduser("~"), ".tmp_x345234dE_deflex")
        shutil.rmtree(base)

    def test_volatile_source(self):
        pd.testing.assert_frame_equal(
            self.tables["volatile plants"],
            self.input_data["volatile plants"],
        )

    def test_storages(self):
        a = self.tables["storages"].apply(pd.to_numeric)
        b = self.input_data["storages"].apply(pd.to_numeric)
        for col in a.columns:
            pd.testing.assert_series_equal(a[col], b[col])
        # pd.testing.assert_frame_equal(a, b)

    def test_demand_series(self):
        pd.testing.assert_frame_equal(
            self.tables["demand series"],
            self.input_data["demand series"],
        )

    def test_transmission(self):
        pd.testing.assert_frame_equal(
            self.tables["power lines"].apply(pd.to_numeric),
            self.input_data["power lines"].apply(pd.to_numeric),
        )

    def test_transformer(self):
        pd.testing.assert_frame_equal(
            self.tables["power plants"],
            self.input_data["power plants"],
        )

    def test_meta(self):
        pd.testing.assert_frame_equal(
            self.tables["general"].astype(str).sort_index(),
            self.input_data["general"].astype(str).sort_index(),
        )

    def test_commodity_source(self):
        pd.testing.assert_frame_equal(
            self.tables["commodity sources"],
            self.input_data["commodity sources"],
        )

    def test_mobility_series(self):
        pd.testing.assert_frame_equal(
            self.tables["mobility series"],
            self.input_data["mobility series"],
        )

    def test_mobility(self):
        self.input_data["mobility"]["efficiency"] = pd.to_numeric(
            self.input_data["mobility"]["efficiency"]
        )
        pd.testing.assert_frame_equal(
            self.tables["mobility"],
            self.input_data["mobility"],
        )

    def test_volatile_series(self):
        pd.testing.assert_frame_equal(
            self.tables["volatile series"],
            self.input_data["volatile series"],
        )

    def test_length(self):
        assert len(self.tables.keys()) == len(self.input_data.keys())
        assert sorted(list(self.tables.keys())) == sorted(
            list(self.input_data.keys())
        )
