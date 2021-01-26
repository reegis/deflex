# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import logging
import os

import requests


def download(fn, url):
    if not os.path.isfile(fn):
        logging.info(
            "Downloading '%s' from %s" % (os.path.basename(fn), url)
        )
        req = requests.get(url)
        with open(fn, "wb") as fout:
            fout.write(req.content)
            logging.info("%s downloaded from %s." % (url, fn))
