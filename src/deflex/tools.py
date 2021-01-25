# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import logging
import os

try:
    import requests
except ModuleNotFoundError:
    requests = None


def download(fn, url):
    if requests is None:
        raise ModuleNotFoundError(
            "You cannot download a file without >requests< installed."
            "Use:\n pip install requests"
        )
    if not os.path.isfile(fn):
        logging.info(
            "Downloading '{0}' from {1}".format(os.path.basename(fn), url)
        )
        req = requests.get(url)
        with open(fn, "wb") as fout:
            fout.write(req.content)
            logging.info("{1} downloaded from {0}.".format(url, fn))
