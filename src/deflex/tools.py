# -*- coding: utf-8 -*-

"""Processing a list of power plants in Germany.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import logging
import os
from zipfile import ZipFile

import requests

TEST_PATH = os.path.join(
    os.path.expanduser("~"), ".deflex", "tmp_test_32traffic_43"
)


def download(fn, url):
    if not os.path.isfile(fn):
        logging.info("Downloading '%s' from %s", os.path.basename(fn), url)
        req = requests.get(url)
        with open(fn, "wb") as fout:
            fout.write(req.content)
            logging.info("%s downloaded from %s.", url, fn)


def fetch_example_results(key):
    """Download example results to enable tests.

    Make sure that the examples will
    have the same structure as the actual deflex results.
    """

    urls = {
        "de02.dflx": "https://osf.io//download",
        "de02_co2-price_var-costs.dflx": "https://osf.io//download",
        "de02_heat.dflx": "https://osf.io//download",
        "de17_heat.dflx": "https://osf.io//download",
        "de21_copperplate.dflx": "https://osf.io//download",
        "de21_transmission-losses.dflx": "https://osf.io//download",
        "de02_short.xlsx": "https://osf.io//download",
        "de02_short_broken.xlsx": "https://osf.io//download",
    }
    os.makedirs(TEST_PATH, exist_ok=True)
    file_name = os.path.join(TEST_PATH, key)
    download(file_name, urls[key])
    if os.path.basename(file_name).split(".")[-1] == "zip":
        with ZipFile(file_name, "r") as zip_ref:
            zip_ref.extractall(os.path.dirname(file_name))
    return file_name
