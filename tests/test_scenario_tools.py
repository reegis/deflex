# -*- coding: utf-8 -*-

"""
Processing a list of power plants in Germany.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
import shutil

import pytest

from deflex import scenario_tools


def test_basic_scenario_class():
    sc = scenario_tools.Scenario()
    sc.create_nodes()


def test_scenario_building():
    sc = scenario_tools.DeflexScenario(name="test", year=2014)
    csv_path = os.path.join(
        os.path.dirname(__file__), "data", "deflex_2014_de21_test_csv"
    )
    sc.load_csv(csv_path)
    sc.table2es()
    sc.check_table("volatile_series")
    sc.table_collection["volatile_series"].loc[5, ("DE01", "wind")] = float(
        "nan"
    )
    with pytest.raises(
        ValueError, match=r"Nan Values in the volatile_series table"
    ):
        sc.check_table("volatile_series")


def test_node_dict():
    nc = scenario_tools.NodeDict()
    nc["g"] = 5
    nc["h"] = 6
    msg = (
        "Key 'g' already exists. Duplicate keys are not allowed in a "
        "node dictionary."
    )
    with pytest.raises(KeyError, match=msg):
        nc["g"] = 7


def test_scenario_es_init():
    sc = scenario_tools.DeflexScenario(name="test", year=2012, debug=True)
    es1 = sc.initialise_energy_system()
    sc = scenario_tools.DeflexScenario(name="test", year=2012)
    es2 = sc.initialise_energy_system()
    sc = scenario_tools.DeflexScenario(name="test", year=2013)
    es3 = sc.initialise_energy_system()
    assert len(es1.timeindex) == 3
    assert len(es2.timeindex) == 8784
    assert len(es3.timeindex) == 8760


def test_scenario_es_init_error():
    sc = scenario_tools.DeflexScenario()
    msg = (
        "You cannot create an EnergySystem with self.year=2012, of type"
        " <class 'str'"
    )
    with pytest.raises(TypeError, match=msg):
        sc.initialise_es("2012")


def test_excel_reader():
    sc = scenario_tools.DeflexScenario(name="test", year=2014)
    xls_fn = os.path.join(
        os.path.dirname(__file__), "data", "deflex_2013_de02_test.xls"
    )
    sc.load_excel(xls_fn)
    sc.table2es()
    csv_path = os.path.join(
        os.path.expanduser("~"), "deflex_2014_de02_nose_test_csv"
    )
    sc.to_csv(csv_path)
    sc.to_csv(csv_path)
    xls_fn = os.path.join(
        os.path.expanduser("~"), "deflex_2014_de02_nose_test.xls"
    )
    sc.to_excel(xls_fn)
    shutil.rmtree(csv_path)
    os.remove(xls_fn)


def test_build_model_manually():
    sc = scenario_tools.DeflexScenario(name="my_test", year=2014, debug=True)
    xls_fn = os.path.join(
        os.path.dirname(__file__), "data", "deflex_2013_de02_test.xls"
    )
    sc.load_excel(xls_fn)
    nodes = sc.create_nodes()
    sc.add_nodes(nodes)
    dump_fn = os.path.join(os.path.expanduser("~"), "nose_test.deflex")
    sc.dump_es(dump_fn)
    sc.create_model()
    sc.solve(solver="cbc", with_duals=True)
    assert sc.es.results["meta"]["scenario"]["name"] == "my_test"
    sc.dump_es(dump_fn)
    sc.plot_nodes()
    sc.results_fn = dump_fn
    sc.restore_es(dump_fn)
    assert sc.meta["scenario"]["year"] == 2014
    os.remove(dump_fn)


def test_corrupt_data():
    sc = scenario_tools.DeflexScenario(year=2014)
    csv_path = os.path.join(
        os.path.dirname(__file__), "data", "deflex_2014_de02_test_csv"
    )
    sc.load_csv(csv_path)
    sc.table_collection["volatile_series"].drop(
        ("DE02", "solar"), inplace=True, axis=1
    )
    msg = "Missing time series for solar"
    with pytest.raises(ValueError, match=msg):
        sc.table2es()
