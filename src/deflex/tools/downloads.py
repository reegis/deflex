# -*- coding: utf-8 -*-

"""Download test files.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""

import logging
import os
from zipfile import ZipFile

import requests

from deflex import config as cfg

TEST_PATH = os.path.join(
    os.path.expanduser("~"), ".deflex", "tmp_test_32traffic_43"
)


def download(fn, url, force=False):
    """
    Download a file from a given url into a specific file if the file does not
    exist. Use `force=True` to force the download.

    Parameters
    ----------
    fn : str
        Filename with the full path, where to store the downloaded file.
    url : str
        Full url of the file including (https:// etc.)
    force : bool
        Set to `True` to download the file even if it already exists.

    Examples
    --------
    >>> my_url = "https://upload.wikimedia.org/wikipedia/commons/d/d3/Test.pdf"
    >>> download("/home/name/Downloads/filename.pdf", my_url)  # doctest: +SKIP

    """
    if not os.path.isfile(fn) or force:
        logging.info("Downloading '%s' from %s", os.path.basename(fn), url)
        req = requests.get(url)
        with open(fn, "wb") as fout:
            fout.write(req.content)
            logging.info("%s downloaded from %s.", url, fn)


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
