# -*- coding: utf-8 -*-

"""Results handling in deflex.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import logging
import os

import pandas as pd
import requests


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
    import os
    >>> my_url = "https://upload.wikimedia.org/wikipedia/commons/d/d3/Test.pdf"
    >>> download("filename.pdf", my_url)
    >>> os.remove("filename.pdf")

    """
    if not os.path.isfile(fn) or force:
        logging.info("Downloading '%s' from %s", os.path.basename(fn), url)
        req = requests.get(url)
        with open(fn, "wb") as fout:
            fout.write(req.content)
            logging.info("%s downloaded from %s.", url, fn)


def dict2file(tables, path, filetype="xlsx", drop_empty_columns=False):
    """

    Parameters
    ----------
    tables
    path
    filetype
    drop_empty_columns

    Returns
    -------

    """
    if filetype == "xlsx":
        _dict2spreadsheet(tables, path, drop_empty_columns)
    elif filetype == "csv":
        _dict2csv(tables, path, drop_empty_columns)
    else:
        msg = "No function implemented for filetype: '{}'".format(filetype)
        raise NotImplementedError(msg)


def _clean_table(table, drop_empty_columns):
    table.sort_index(axis=1, inplace=True)
    if drop_empty_columns:
        table = table.loc[:, (table.sum(axis=0) != 0)]
    return table


def _dict2spreadsheet(tables, path, drop_empty_columns=False):
    logging.info(f"Writing table to {path}")
    writer = pd.ExcelWriter(path)
    for name, table in tables.items():
        if isinstance(table, pd.DataFrame):
            table = _clean_table(table, drop_empty_columns)
        table.to_excel(writer, name)
    writer.save()


def _dict2csv(tables, path, drop_empty_columns=False):
    os.makedirs(path, exist_ok=True)
    logging.info(f"Writing table to {path}")
    for name, table in tables.items():
        if isinstance(table, pd.DataFrame):
            table = _clean_table(table, drop_empty_columns)
        fn = os.path.join(path, name + ".csv")
        table.to_csv(fn)
