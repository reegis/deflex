# -*- coding: utf-8 -*-

"""Main script.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"


import logging
import multiprocessing
import os
import pprint
import traceback
from collections import namedtuple
from datetime import datetime

import pandas as pd

from deflex import config as cfg
from deflex import scenario_tools


def stopwatch():
    """Track the running time."""
    if not hasattr(stopwatch, "start"):
        stopwatch.start = datetime.now()
    return str(datetime.now() - stopwatch.start)[:-7]


def load_scenario(path, file_type=None):
    """
    Create a deflex scenario object from file.

    Parameters
    ----------
    path : str
        A valid deflex scenario file.
    file_type : str or None
        Type of the input data. Valid values are 'csv', 'excel', None. If the
        input is non the path should end on 'csv', '.xls', '.xlsx' to allow
        auto-detection.

    Returns
    -------
    deflex.DeflexScenario

    Examples
    --------
    >>> fn = os.path.join(os.path.dirname(__file__), os.pardir,
    ...      "tests", "data", "deflex_test_scenario.xls")
    >>> s = load_scenario(fn, file_type="excel")
    >>> type(s)
    <class 'deflex.scenario_tools.DeflexScenario'>
    >>> int(s.table_collection["volatile_source"]["capacity"]["DE02", "wind"])
    517
    >>> type(load_scenario(fn))
    <class 'deflex.scenario_tools.DeflexScenario'>
    >>> load_scenario(fn, file_type="csv")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
     ...
    NotADirectoryError: [Errno 20] Not a directory:

    """
    sc = scenario_tools.DeflexScenario()

    if path is not None:
        if file_type is None:
            if "xls" in path[-4:]:
                file_type = "excel"
            elif "csv" in path[-4:]:
                file_type = "csv"
            else:
                file_type = None
        logging.info("Start modelling: {0}".format(stopwatch()))
        logging.info("Reading file: {0}".format(path))
        if file_type == "excel":
            sc.load_excel(path)
        elif file_type == "csv":
            sc.load_csv(path)
    return sc


def fetch_scenarios_from_dir(path, csv=True, xls=False):
    """
    Search for files with an excel extension or directories ending with '_csv'.

    By now it is not possible to distinguish between valid deflex scenarios and
    other excel files or directories ending with 'csv'. Therefore, the given
    directory should only contain valid scenarios.

    The function will not search recursively.

    Parameters
    ----------
    path : str
        Directory with valid deflex scenarios.
    csv : bool
        Search for csv directories.
    xls : bool
        Search for xls files.

    Returns
    -------
    list : Scenarios found in the given directory.

    Examples
    --------
    >>> test_data = os.path.join(os.path.dirname(__file__), os.pardir, "tests",
    ...                          "data")
    >>> my_csv = fetch_scenarios_from_dir(test_data)
    >>> len(my_csv)
    2
    >>> os.path.basename(my_csv[0])
    'deflex_2014_de02_test_csv'
    >>> my_excel = fetch_scenarios_from_dir(test_data, csv=False, xls=True)
    >>> len(my_excel)
    3
    >>> os.path.basename(my_excel[0])
    'deflex_2013_de02_test.xls'
    >>> len(fetch_scenarios_from_dir(test_data, xls=True))
    5

    """
    xls_scenarios = []
    csv_scenarios = []
    for name in os.listdir(path):
        if (name[-4:] == ".xls" or name[-5:] == "xlsx") and xls is True:
            xls_scenarios.append(os.path.join(path, name))
        if name[-4:] == "_csv" and csv is True:
            csv_scenarios.append(os.path.join(path, name))
    csv_scenarios = sorted(csv_scenarios)
    xls_scenarios = sorted(xls_scenarios)
    logging.info(str(xls_scenarios))
    logging.info(str(csv_scenarios))
    return csv_scenarios + xls_scenarios


def model_multi_scenarios(scenarios, cpu_fraction=0.2, log_file=None):
    """

    Parameters
    ----------
    scenarios : iterable
        Multiple scenarios to be modelled in parallel.
    cpu_fraction : float
        Fraction of available cpu cores to use for the parallel modelling.
    log_file : str
        Filename to store the log file.

    Returns
    -------

    Examples
    --------
    >>> fn1 = os.path.join(os.path.dirname(__file__), os.pardir,
    ...      "tests", "data", "deflex_test_scenario.xls")
    >>> fn2 = os.path.join(os.path.dirname(__file__), os.pardir,
    ...      "tests", "data", "deflex_test_scenario_broken.xls")
    >>> my_log_file = os.path.join(os.path.dirname(__file__), os.pardir,
    ...      "tests", "data", "my_log_file.csv")
    >>> my_scenarios = [fn1, fn2]
    >>> model_multi_scenarios(my_scenarios, log_file=my_log_file)
    >>> my_log = pd.read_csv(my_log_file, index_col=[0])
    >>> good = my_log.loc["deflex_test_scenario.xls"]
    >>> rv = good["return_value"]
    >>> datetime.strptime(rv, "%Y-%m-%d %H:%M:%S.%f").year > 2019
    True
    >>> good["trace"]
    nan
    >>> os.path.basename(good["result_file"])
    'deflex_test_scenario_alpha.esys'
    >>> broken = my_log.loc["deflex_test_scenario_broken.xls"]
    >>> broken["return_value"].replace("'", "")
    'ValueError(Missing time series for geothermal (capacity: 31.4) in DE01.)'
    >>> broken["trace"]  # doctest: +ELLIPSIS
    'Traceback (most recent call last)...
    >>> broken["result_file"]
    nan
    """
    start = datetime.now()
    p = multiprocessing.Pool(int(multiprocessing.cpu_count() * cpu_fraction))

    logs = p.starmap(
        batch_model_scenario, zip(scenarios, [False] * len(scenarios))
    )
    p.close()
    p.join()
    failing = {n: r for n, r, t, f, s in logs if isinstance(r, BaseException)}

    logger = pd.DataFrame()
    for log in logs:
        logger.loc[log[0], "start"] = start
        if isinstance(log[1], BaseException):
            logger.loc[log[0], "return_value"] = repr(log[1])
        else:
            logger.loc[log[0], "return_value"] = log[1]
        logger.loc[log[0], "trace"] = log[2]
        logger.loc[log[0], "result_file"] = log[3]

    if log_file is None:
        log_file = os.path.join(
            os.path.expanduser("~"), ".deflex", "log_deflex.csv"
        )

    logger.to_csv(log_file)

    if len(failing) < 1:
        logging.info("Finished all scenarios without errors")
    else:
        logging.info(failing)


def batch_model_scenario(path, named=True, file_type=None, ignore_errors=True):
    """
    Model a single scenario in batch mode. By default errors will be ignored
    and returned together with the traceback.

    Parameters
    ----------
    path : str
        A valid deflex scenario.
    file_type : str or None
        Type of the input data. Valid values are 'csv', 'excel', None. If the
        input is non the path schould end on 'csv', '.xls', '.xlsx'.
    ignore_errors : bool
        Set True to stop the script if an error occurs for debugging. By
        default errors are ignored and returned.

    Returns
    -------
    namedtuple

    Examples
    --------
    >>> fn = os.path.join(os.path.dirname(__file__), os.pardir,
    ...      "tests", "data", "deflex_test_scenario.xls")
    >>> r = batch_model_scenario(fn)  # doctest: +ELLIPSIS
    Welcome to the CBC MILP ...
    >>> r.name
    'deflex_test_scenario.xls'
    >>> os.path.basename(r.result_file)
    'deflex_test_scenario_alpha.esys'
    >>> r.trace
    >>> r.return_value.year > 2019
    True
    >>> fn = os.path.join("wrong_file.xls")
    >>> r = batch_model_scenario(fn)
    >>> r.name
    'wrong_file.xls'
    >>> repr(r.return_value)
    "FileNotFoundError(2, 'No such file or directory')"
    >>> r.result_file
    >>> r.trace  # doctest: +ELLIPSIS
    'Traceback (most recent call last):...
    """
    out = namedtuple("out", ["name", "return_value", "trace", "result_file", "start_time"])
    name = os.path.basename(path)
    logging.info("Next scenario: {0}".format(name))
    start_time = datetime.now()
    if ignore_errors:
        try:
            result_file = model_scenario(path, file_type)
            return_value = datetime.now()
            trace = None
        except Exception as e:
            trace = traceback.format_exc()
            return_value = e
            result_file = None
    else:
        result_file = model_scenario(path, file_type)
        return_value = str(datetime.now())
        trace = None

    if named:
        return out(
            name=name,
            return_value=return_value,
            trace=trace,
            result_file=result_file,
            start_time=start_time
        )
    else:
        return name, return_value, trace, result_file, start_time


def model_scenario(
    path=None, file_type=None, es=None, result_path=None,
):
    """
    Compute a deflex scenario.

    Parameters
    ----------
    path : str or None
        File or directory with a valid deflex scenario. If no path is given an
        energy system (es) has to be passed.
    file_type : str or None
        Type of the input data. Valid values are 'csv', 'excel', None. If the
        input is non the path schould end on 'csv', '.xls', '.xlsx'.
    es : oemof.solph.EnergySystem
        A valid deflex energy system. If an energy system is defined the path
        parameter will be ignored.
    result_path : str or None
        Path to store the output file. If None the results will be stored along
        with the scenarios.

    Returns
    -------

    Examples
    --------
    >>> fn = os.path.join(os.path.dirname(__file__), os.pardir,
    ...      "tests", "data", "deflex_test_scenario.xls")
    >>> r = model_scenario(fn, file_type="excel")  # doctest: +ELLIPSIS
    Welcome to the CBC MILP ...

    """
    stopwatch()

    meta = {
        "model_base": "deflex",
        "solver": cfg.get("general", "solver"),
        "start_time": datetime.now(),
    }
    logging.info("Start modelling: {0}".format(stopwatch()))

    sc = load_scenario(path, file_type)
    sc.meta = meta

    # If a meta table exists in the table collection update meta dict
    if "meta" in sc.table_collection:
        meta.update(sc.table_collection["meta"].to_dict()["value"])

    # Use name from meta or from filename
    if "name" in meta:
        sc.name = meta["name"]
    else:
        meta["name"] = (
            os.path.basename(path)
            + "_"
            + datetime.now().strftime("%Y%d%m_%H%M%S")
        )
        sc.name = meta["name"]

    if result_path is None:
        result_path = os.path.join(
            os.path.dirname(path),
            "results_{0}".format(cfg.get("general", "solver")),
            sc.name + ".esys",
        )

    if es is not None:
        sc.es = es
    else:
        logging.info("Add nodes to the EnergySystem: {0}".format(stopwatch()))
        sc.table2es()

    logging.info("Create the concrete model: {0}".format(stopwatch()))
    sc.create_model()

    logging.info("Solve the optimisation model: {0}".format(stopwatch()))
    sc.solve(solver=cfg.get("general", "solver"))

    logging.info("Solved. Dump results: {0}".format(stopwatch()))
    os.makedirs(os.path.dirname(result_path), exist_ok=True)

    logging.info("Dump file to {0}".format(result_path))
    sc.meta["end_time"] = datetime.now()
    sc.dump_es(result_path)

    logging.info(
        "{0} - deflex scenario finished without errors: {1}".format(
            stopwatch(), sc.name
        )
    )
    return result_path


def plot_scenario(path, file_type=None, graphml_file=None):
    sc = load_scenario(path, file_type)

    if graphml_file is None:
        show = True
    else:
        show = False

    sc.plot_nodes(
        filename=graphml_file,
        show=show,
        remove_nodes_with_substrings=["bus_cs"],
    )


if __name__ == "__main__":
    pass
