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


def download(fn, url, force=False):
    if not os.path.isfile(fn) or force:
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

    zip_file = os.path.join(TEST_PATH, "deflex_examples.zip")
    zip_url = ("https://files.de-1.osf.io/v1/resources/a5xrj/providers"
               "/osfstorage/5fdc7e0bf0df5405452ef6f0/?zip=")
    os.makedirs(TEST_PATH, exist_ok=True)
    if ".dflx" in key:
        file_name = os.path.join(TEST_PATH, "results_cbc", key)
    else:
        file_name = os.path.join(TEST_PATH, key)
    if not os.path.isfile(file_name):
        download(zip_file, zip_url, force=True)
        with ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(os.path.dirname(zip_file))
    if not os.path.isfile(file_name):
        msg = "Example file '{0}' not in '{1}', downloaded from {2}".format(
            key, zip_file, zip_url
        )
        raise ValueError(msg)
    return file_name
