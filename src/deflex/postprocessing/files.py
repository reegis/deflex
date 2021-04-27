# -*- coding: utf-8 -*-

"""Results handling in deflex.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import os
import pickle

import pandas as pd

from deflex.scenario import DeflexScenario
from deflex.scenario import restore_scenario


def search_results(path, extension="dflx", **parameter_filter):
    """Filter results by extension and meta data.

    The function will search the $HOME folder recursively for files with the
    '.esys' extension. Afterwards all files will filtered by the meta data.

    Parameters
    ----------
    path : str
        Start folder from where to search recursively.
    extension : str
        Extension of the results files (default: ".dflx")
    **parameter_filter
        Set filter always with lists e.g. map=["de21"] or map=["de21", "de22"].
        The values in the list have to be strings. Two filters will be
        connected with 'AND', the values within one filter with `OR`.
        The filters year=["2014"], map=["de21", "de22"] will find all scenarios
        with: year==2014 and (map=="de21" or map=="de22")

    Returns
    -------

    Examples
    --------
    >>> from deflex.tools import TEST_PATH
    >>> from deflex.tools import fetch_test_files
    >>> my_file_name = fetch_test_files("de17_heat.dflx")
    >>> res = search_results(path=TEST_PATH, map=["de17"])
    >>> len(res)
    2
    >>> sorted(res)[0].split(os.sep)[-1]
    'de17_heat.dflx'
    >>> res = search_results(path=TEST_PATH, map=["de17", "de21"])
    >>> len(res)
    4
    >>> res = search_results(
    ...     path=TEST_PATH, map=["de17", "de21"], heat=["True"])
    >>> len(res)
    1
    >>> res[0].split(os.sep)[-1]
    'de17_heat.dflx'
    """
    result_files = []
    for root, dirs, files in os.walk(path):
        files = [f for f in files if not f[0] == "."]
        dirs[:] = [d for d in dirs if not d[0] == "."]
        if "." + extension in str(files):
            for f in files:
                if f.split(".")[-1] == extension:
                    result_files.append(os.path.join(root, f))
    files = {}

    # filter by meta data.
    for name in result_files:
        fn = os.path.join(path, name)
        f = open(fn, "rb")
        files[name] = pickle.load(f)
        f.close()
    for filter_key, filter_value in parameter_filter.items():
        iterate = list(files.keys())
        for fn in iterate:
            meta = files[fn]
            if str(meta.get(filter_key)) not in filter_value:
                files.pop(fn, None)
    return list(files.keys())


def restore_results(file_names, scenario_class=DeflexScenario):
    """
    Load results from a file or a list of files. The results will be a deflex
    result dictionary with the following keys:

     * main – Results of all variables
     * param – Input parameter
     * meta – Meta information and tags of the scenario
     * problem – Information about the linear problem such as lower bound,
       upper bound etc.
     * solver – Solver results
     * solution – Information about the found solution and the objective value

    Parameters
    ----------
    file_names : list or string
        All file names (full path) that should be loaded.
    scenario_class : deflex.Scenario
        The Scenario class. ToDo How to reference the class and an object.

    Returns
    -------
    list : A list of results dictionaries or a single dictionary if one file
        name is given.

    Examples
    --------
    >>> from deflex.tools import fetch_test_files
    >>> fn1 = fetch_test_files("de21_no-heat_transmission.dflx")
    >>> fn2 = fetch_test_files("de02_no-heat.dflx")
    >>> sorted(restore_results(fn1).keys())
    ['Main', 'Meta', 'Param', 'Problem', 'Solution', 'Solver']
    >>> sorted(restore_results([fn1, fn2])[0].keys())
    ['Main', 'Meta', 'Param', 'Problem', 'Solution', 'Solver']
    """
    if not isinstance(file_names, list):
        file_names = list((file_names,))
    results = []

    for path in file_names:
        tmp_res = restore_scenario(path, scenario_class).results
        tmp_res["meta"]["filename"] = os.path.basename(path)
        results.append(tmp_res)

    if len(results) < 2:
        results = results[0]
    return results


def dict2file(tables, path, filetype=None, drop_empty_columns=False):
    os.makedirs(path, exist_ok=True)

    if filetype is None:
        filetype = path.split(".")[-1]

    if filetype == "xlsx":
        dict2spreadsheet(tables, path, drop_empty_columns)
    elif filetype == "csv":
        dict2csv(tables, path, drop_empty_columns)
    else:
        msg = "No function implemented for filetype: '{}'".format(filetype)
        raise NotImplementedError(msg)


def dict2spreadsheet(tables, path, drop_empty_columns=False):
    writer = pd.ExcelWriter(path)
    for name, table in tables.items():
        if isinstance(table, pd.DataFrame):
            table.sort_index(axis=1, inplace=True)
            if drop_empty_columns:
                table = table.loc[:, (table.sum(axis=0) != 0)]
        table.to_excel(writer, name)
    writer.save()


def dict2csv(tables, path, drop_empty_columns=False):
    for name, table in tables.items():
        fn = os.path.join(path, name + ".csv")
        table.to_csv(fn)
