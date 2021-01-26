# -*- coding: utf-8 -*-

"""
Tests for the config module.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

from nose.tools import eq_, ok_, assert_raises_regexp
from configparser import NoOptionError, NoSectionError
import os
from reegis import config


def test_ini_filenames_basic():
    files = config.get_ini_filenames(use_importer=False, local=False)
    fn = sorted([f.split(os.sep)[-1] for f in files])
    eq_(
        fn,
        [
            "dictionary.ini",
            "mobility.ini",
            "reegis.ini",
            "solar.ini",
            "wind.ini",
        ],
    )


def test_ini_filenames_local_path():
    local_path = os.path.join(os.path.expanduser("~"), ".reegis")
    os.makedirs(local_path, exist_ok=True)
    new_file = os.path.join(local_path, "test_ini_file.ini")
    f = open(new_file, "w+")
    f.close()
    files = config.get_ini_filenames()
    fn = sorted([f.split(os.sep)[-1] for f in files])
    ok_("test_ini_file.ini" in fn)
    os.remove(new_file)


def test_ini_filenames_additional_path():
    additional_path = [os.path.join(os.path.dirname(__file__), "data")]
    files = config.get_ini_filenames(
        use_importer=False, local=False, additional_paths=additional_path
    )
    fn = sorted([f.split(os.sep)[-1] for f in files])
    assert (
        fn ==
        [
            "config_test.ini",
            "dictionary.ini",
            "mobility.ini",
            "reegis.ini",
            "solar.ini",
            "wind.ini",
        ]
    )


def test_init_basic():
    config.init()
    fn = sorted([f.split(os.sep)[-1] for f in config.FILES])
    eq_(
        fn,
        [
            "dictionary.ini",
            "mobility.ini",
            "reegis.ini",
            "solar.ini",
            "wind.ini",
        ],
    )


def test_init_additional_path():
    additional_path = [os.path.join(os.path.dirname(__file__), "data")]
    config.init(paths=additional_path)
    fn = sorted([f.split(os.sep)[-1] for f in config.FILES])
    eq_(
        fn,
        [
            "config_test.ini",
            "dictionary.ini",
            "mobility.ini",
            "reegis.ini",
            "solar.ini",
            "wind.ini",
        ],
    )


def test_init_own_file_list():
    files = [
        os.path.join(os.path.dirname(__file__), "data", "config_test.ini")
    ]
    config.init(files=files)
    fn = sorted([f.split(os.sep)[-1] for f in config.FILES])
    eq_(fn, ["config_test.ini"])
    eq_(config.get("tester", "my_test"), "my_value")


def test_check_functions():
    files = [
        os.path.join(os.path.dirname(__file__), "data", "config_test.ini")
    ]
    config.init(files=files)
    ok_(config.has_section("tester"))
    ok_(not (config.has_section("teste")))
    ok_(config.has_option("tester", "my_test"))


def test_get_function():
    """Read config file."""
    files = [
        os.path.join(os.path.dirname(__file__), "data", "config_test.ini")
    ]
    config.init(files=files)
    ok_(config.get("type_tester", "my_bool"))
    ok_(isinstance(config.get("type_tester", "my_int"), int))
    ok_(isinstance(config.get("type_tester", "my_float"), float))
    ok_(isinstance(config.get("type_tester", "my_string"), str))
    ok_(isinstance(config.get("type_tester", "my_None"), type(None)))
    ok_(isinstance(config.get("type_tester", "my_list"), str))
    eq_(int(config.get_list("type_tester", "my_list")[2]), 7)


def test_missing_value():
    files = [
        os.path.join(os.path.dirname(__file__), "data", "config_test.ini")
    ]
    config.init(files=files)
    with assert_raises_regexp(
        NoOptionError, "No option 'blubb' in section: 'type_tester'"
    ):
        config.get("type_tester", "blubb")
    with assert_raises_regexp(NoSectionError, "No section: 'typetester'"):
        config.get("typetester", "blubb")


def test_dicts():
    """Test dictionaries in config file."""
    files = [
        os.path.join(os.path.dirname(__file__), "data", "config_test.ini")
    ]
    config.init(files=files)
    d = config.get_dict("type_tester")
    eq_(d["my_list"], "4,6,7,9")
    d = config.get_dict_list("type_tester")
    eq_(d["my_list"][1], "6")
    eq_(d["my_None"][0], None)
    eq_(d["my_int"][0], 5)
    d = config.get_dict_list("type_tester", string=True)
    eq_(d["my_list"][1], "6")
    eq_(d["my_None"][0], "None")
    eq_(d["my_int"][0], "5")


def test_set_temp_value():
    files = [
        os.path.join(os.path.dirname(__file__), "data", "config_test.ini")
    ]
    config.init(files=files)
    with assert_raises_regexp(
        NoOptionError, "No option 'blubb' in section: 'type_tester'"
    ):
        config.get("type_tester", "blubb")
    config.tmp_set("type_tester", "blubb", "None")
    eq_(config.get("type_tester", "blubb"), None)
    config.tmp_set("type_tester", "blubb", "5.5")
    eq_(config.get("type_tester", "blubb"), 5.5)


def test_set_temp_without_init():
    config.tmp_set("type_tester", "blubb", "None")
