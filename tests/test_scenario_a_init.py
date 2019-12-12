# -*- coding: utf-8 -*-

"""
Test download of power plants.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
import requests
from deflex import config as cfg


def test_download_pp_from_osf():
    """Download pp-file from osf."""
    url = 'https://osf.io/qtc56/download'
    path = cfg.get('paths', 'powerplants')
    file = 'de21_pp.h5'
    filename = os.path.join(path, file)

    if not os.path.isfile(filename):
        req = requests.get(url)
        with open(filename, 'wb') as fout:
            fout.write(req.content)
