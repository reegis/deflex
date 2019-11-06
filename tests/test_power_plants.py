import os
import requests
from nose.tools import eq_, assert_raises_regexp
from unittest.mock import MagicMock
from deflex import config as cfg, powerplants, geometries


def test_01_download_reegis_power_plants():
    url = 'https://osf.io/ude5c/download'
    path = cfg.get('paths', 'powerplants')
    file = 'reegis_pp_test.h5'
    filename = os.path.join(path, file)

    if not os.path.isfile(filename):
        req = requests.get(url)
        with open(filename, 'wb') as fout:
            fout.write(req.content)


def test_02_create_deflex_powerplants():
    de = geometries.deflex_regions('de21')
    fn_in = os.path.join(cfg.get('paths', 'powerplants'), 'reegis_pp_test.h5')
    fn_out = os.path.join(cfg.get('paths', 'powerplants'), 'deflex_pp_test.h5')
    powerplants.pp_reegis2deflex(de, 'de21', filename_in=fn_in,
                                 filename_out=fn_out)


def test_03_download_deflex_full_pp():
    url = 'https://osf.io/qdx2c/download'
    filename = os.path.join(
            cfg.get('paths', 'powerplants'),
            cfg.get('powerplants', 'deflex_pp')).format(
                map=cfg.get('init', 'map'))
    if not os.path.isfile(filename):
        req = requests.get(url)
        with open(filename, 'wb') as fout:
            fout.write(req.content)


def test_04_deflex_power_plants_by_year():
    de = geometries.deflex_regions('de21')
    pp = powerplants.get_deflex_pp_by_year(de, 2014, 'de21',
                                           overwrite_capacity=True)
    eq_(int(pp['capacity'].sum()), 181489)


def test_05_not_existing_file():
    cfg.tmp_set('paths', 'powerplants', '/home/pet/')
    de = geometries.deflex_regions('de22')
    powerplants.pp_reegis2deflex = MagicMock(return_value='/home/pet/pp.h5')

    with assert_raises_regexp(Exception,
                              "File /home/pet/pp.h5 does not exist"):
        powerplants.get_deflex_pp_by_year(de, 2012, 'de22')
