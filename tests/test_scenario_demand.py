import os
import requests
from nose.tools import eq_, assert_raises_regexp, with_setup
from unittest.mock import MagicMock
from deflex import config as cfg, basic_scenario, geometries
from reegis.tools import download_file


def setup_func():
    """Download pp-file from osf."""

    url = 'https://osf.io/m435r/download'
    path = cfg.get('paths', 'demand')
    file = 'heat_profile_state_2014_weather_2014.csv'
    filename = os.path.join(path, file)
    download_file(filename, url)

    url = 'https://osf.io/m435r/download'
    file = 'heat_profile_state_2014_weather_2014.csv'
    filename = os.path.join(path, file)
    download_file(filename, url)


@with_setup(setup_func)
def scenario_demand_test():
    regions = geometries.deflex_regions(rmap='de21')
    d = basic_scenario.scenario_demand(regions, 2014, 'de21')
    eq_(int(d['DE01', 'district heating'].sum()), 18639262)
    eq_(int(d['DE05', 'electrical_load'].sum()), 10069)
