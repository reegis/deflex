import os
from nose.tools import eq_
from unittest.mock import MagicMock
import pandas as pd
from deflex import basic_scenario, geometries, demand
from reegis import energy_balance


def test_scenario_creation():
    data = {}
    for name in ['volatile_series', 'demand_series']:
        fn = os.path.join(os.path.dirname(__file__), 'data',
                          'deflex_2014_de21_test_csv', name + '.csv')
        data[name] = pd.read_csv(fn, index_col=[0], header=[0, 1])

    name = 'heat_demand_deflex'
    fn = os.path.join(os.path.dirname(__file__), 'data', name + '.csv')
    data[name] = pd.read_csv(fn, index_col=[0], header=[0, 1])

    name = 'transformer_balance'
    fn = os.path.join(os.path.dirname(__file__), 'data', name + '.csv')
    data[name] = pd.read_csv(fn, index_col=[0, 1, 2], header=[0])

    basic_scenario.scenario_feedin = MagicMock(
        return_value=data['volatile_series'])
    basic_scenario.scenario_demand = MagicMock(
        return_value=data['demand_series'])
    energy_balance.get_transformation_balance_by_region = MagicMock(
        return_value=data['transformer_balance'])
    demand.get_heat_profiles_deflex = MagicMock(
        return_value=data['heat_demand_deflex'])
    regions = geometries.deflex_regions(rmap='de21')
    table_collection = basic_scenario.create_scenario(regions, 2014, 'de21')
    eq_(list(table_collection.keys()), [
        'storages', 'Storage', 'transformer', 'volatile_source',
        'transmission', 'decentralised_heat', 'commodity_source',
        'volatile_series', 'demand_series'])
    eq_(len(list(table_collection.keys())), 9)
