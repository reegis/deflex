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


def test_download(caplog, monkeypatch):
    from deflex import tools

    url = (
        "https://files.de-1.osf.io/v1/resources/a5xrj/providers/osfstorage/"
        "5fdc7e3df0df5405452ef7ae?action=download&direct&version=1"
    )
    fn = os.path.join(os.path.expanduser("~"), ".tmp_test_x456FG6")
    caplog.set_level(logging.DEBUG)
    assert not os.path.isfile(fn)
    tools.download(fn, url)
    assert ".tmp_test_x456FG6" in caplog.text
    assert os.path.isfile(fn)
    caplog.clear()
    tools.download(fn, url)
    assert "Downloading" not in caplog.text
    os.remove(fn)
