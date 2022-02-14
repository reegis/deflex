# -*- coding: utf-8 -*-

"""
Processing a list of power plants in Germany.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import logging
import os

import pytest

from deflex import fetch_test_files
from deflex.scenario_tools.example_files import download


def test_download(caplog, monkeypatch):
    url = (
        "https://files.de-1.osf.io/v1/resources/a5xrj/providers/osfstorage/"
        "5fdc7e3df0df5405452ef7ae?action=download&direct&version=1"
    )
    fn = os.path.join(os.path.expanduser("~"), ".tmp_test_x456FG6")
    caplog.set_level(logging.DEBUG)
    assert not os.path.isfile(fn)
    download(fn, url)
    assert ".tmp_test_x456FG6" in caplog.text
    assert os.path.isfile(fn)
    caplog.clear()
    download(fn, url)
    assert "Downloading" not in caplog.text
    os.remove(fn)


def test_fetching_not_existing_file():
    msg = "Example file 'not_existing_file.xlsx' not in"
    with pytest.raises(ValueError, match=msg):
        fetch_test_files("not_existing_file.xlsx")
