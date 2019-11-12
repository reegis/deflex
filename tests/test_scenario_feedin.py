import os
import requests
from nose.tools import eq_, assert_raises_regexp, with_setup
from unittest.mock import MagicMock
from deflex import config as cfg, basic_scenario, geometries
from reegis.tools import download_file


def setup_func():
    """Download pp-file from osf."""

    downloads = [
        ('n7ahr', 'geothermal'),
        ('5n7t3', 'hydro'),
        ('2qwv7', 'solar'),
        ('9dvpf', 'wind')]

    for d in downloads:
        url = 'https://osf.io/{0}/download'.format(d[0])
        path = os.path.join(
            cfg.get('paths', 'feedin'), 'de21', '2014')
        file = '2014_feedin_de21_normalised_{0}.csv'.format(d[1])
        filename = os.path.join(path, file)
        os.makedirs(path, exist_ok=True)
        download_file(filename, url)


@with_setup(setup_func)
def scenario_feedin_test():
    regions = geometries.deflex_regions(rmap='de21')
    f = basic_scenario.scenario_feedin(regions, 2014, 'de21')
    # eq_(int(d['DE01', 'district heating'].sum()), 18639262)
    # eq_(int(d['DE05', 'electrical_load'].sum()), 10069)
