# -*- coding: utf-8 -*-

"""Download test files.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import logging
import os
from zipfile import ZipFile

from deflex import config as cfg
from deflex.tools.files import download

TEST_PATH = os.path.join(
    os.path.expanduser("~"), ".deflex", "tmp_test_32traffic_43"
)


def download_full_examples(path):
    """Download and unzip scenarios (if zip-file does not exist)"""
    fn = os.path.join(path, "deflex_full_examples_v04.zip")
    url = cfg.get("url", "osfbase") + cfg.get("url", "examples")
    if not os.path.isfile(fn):
        download(fn, url)
    with ZipFile(fn, "r") as zip_ref:
        zip_ref.extractall(path)
    logging.info("All software examples extracted to %s.", url)


def fetch_published_figures_example_files(path):
    """Download and unzip scenarios (if zip-file does not exist)"""
    fn = os.path.join(path, "deflex_softwarex_examples_v04.zip")
    url = cfg.get("url", "osfbase") + cfg.get("url", "published_figures")
    if not os.path.isfile(fn):
        download(fn, url)
    with ZipFile(fn, "r") as zip_ref:
        zip_ref.extractall(path)
    logging.info("All software examples extracted to %s.", url)


def fetch_test_files(path, subdir="scenarios"):
    """Download example results to enable tests.

    Make sure that the examples will
    have the same structure as the actual deflex results.
    """
    test_path = os.path.join(TEST_PATH, subdir)

    zip_file = os.path.join(TEST_PATH, "deflex_test_files.zip")
    zip_url = cfg.get("url", "osfbase") + cfg.get("url", "tests")

    os.makedirs(test_path, exist_ok=True)
    if ".dflx" in path:
        file_name = os.path.join(test_path, "results_cbc", path)
    else:
        file_name = os.path.join(test_path, path)
    if not (os.path.isfile(file_name) or os.path.isdir(file_name)):
        download(zip_file, zip_url, force=False)
        with ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(os.path.dirname(zip_file))
    if not (os.path.isfile(file_name) or os.path.isdir(file_name)):
        msg = "Example file '{0}' not in '{1}', downloaded from {2}".format(
            path, zip_file, zip_url
        )
        raise ValueError(msg)
    return file_name
