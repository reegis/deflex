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

from deflex import config as cfg


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
    if drop_empty_columns:
        table = table.loc[:, (table.sum(axis=0) != 0)]
    return table.sort_index(axis=1)


def _dict2spreadsheet(tables, path, drop_empty_columns=False):
    logging.info(f"Writing table to {path}")
    writer = pd.ExcelWriter(path)
    for name, table in tables.items():
        if isinstance(table, pd.DataFrame):
            table = _clean_table(table, drop_empty_columns)
        table.to_excel(writer, name)
    writer.save()
    writer.close()


def _dict2csv(tables, path, drop_empty_columns=False):
    os.makedirs(path, exist_ok=True)
    logging.info(f"Writing table to {path}")
    for name, table in tables.items():
        if isinstance(table, pd.DataFrame):
            table = _clean_table(table, drop_empty_columns)
        fn = os.path.join(path, name + ".csv")
        table.to_csv(fn)


def file2dict(path, filetype=None, table_index_header=None):
    if table_index_header is None:
        table_index_header = cfg.get_dict_list("table_index_header")
    if filetype is None:
        if os.path.isdir(path):
            filetype = "csv"
        else:
            filetype = os.path.basename(path).split(".")[-1]
    if filetype == "csv":
        dct = _csv2dict(path, table_index_header)
    elif filetype == "xlsx":
        dct = _xlsx2dict(path, table_index_header)
    else:
        raise NotImplementedError(f"Cannot open {filetype}-file.")
    return dct


def _xlsx2dict(filename, table_index_header=None):
    """
    Load scenario data from an xlsx file. The full path has to be passed.

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de02_no-heat.xlsx")
    >>> sc = dflx.DeflexScenario()
    >>> len(sc.input_data)
    0
    >>> sc = sc.read_xlsx(fn)
    >>> len(sc.input_data)
    11
    """
    xlsx = pd.ExcelFile(filename)
    dct = {}
    for sheet in xlsx.sheet_names:
        index_header = table_index_header["result_" + sheet]
        dct[sheet] = xlsx.parse(
            sheet,
            index_col=list(range(int(index_header[0]))),
            header=list(range(int(index_header[1]))),
        )
        dct[sheet] = _squeeze_df(index_header, dct[sheet])
    return dct


def _csv2dict(path, table_index_header=None):
    """
    Load scenario from a csv-collection. The path of the directory has
    to be passed.

    Examples
    --------
    >>> import deflex as dflx
    >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
    >>> sc = dflx.DeflexScenario()
    >>> len(sc.input_data)
    0
    >>> sc = sc.read_csv(fn)
    >>> len(sc.input_data)
    11
    """
    dct = {}
    for file in os.listdir(path):
        if file[-4:] == ".csv":
            name = file[:-4]
            index_header = table_index_header["result_" + name]
            filename = os.path.join(path, file)
            dct[name] = pd.read_csv(
                filename,
                index_col=list(range(int(index_header[0]))),
                header=list(range(int(index_header[1]))),
            )
            dct[name] = _squeeze_df(index_header, dct[name])
    return dct


def _squeeze_df(index_header, df):
    if len(index_header) > 2 and index_header[2] == "s":
        return df.squeeze("columns")
    else:
        return df
