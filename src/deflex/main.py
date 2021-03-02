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
import traceback
from collections import namedtuple
from datetime import datetime

import pandas as pd

from deflex import config as cfg
from deflex import scenario


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
    >>> from deflex.tools import fetch_example_results, TEST_PATH
    >>> fn = fetch_example_results("de02_short.xlsx")
    >>> s = load_scenario(fn, file_type="xlsx")
    >>> type(s)
    <class 'deflex.scenario.DeflexScenario'>
    >>> int(s.input_data["volatile plants"]["capacity"]["DE02", "wind"])
    517
    >>> type(load_scenario(fn))
    <class 'deflex.scenario.DeflexScenario'>
    >>> load_scenario(fn, file_type="csv")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
     ...
    NotADirectoryError: [Errno 20] Not a directory:

    """
    sc = scenario.DeflexScenario()

    if path is not None:
        if file_type is None:
            if ".xlsx" in path[-5:]:
                file_type = "xlsx"
            elif "csv" in path[-4:]:
                file_type = "csv"
            else:
                file_type = None
        logging.info("Reading file: %s", path)
        if file_type == "xlsx":
            sc.read_xlsx(path)
            sc.to_xlsx(path)
        elif file_type == "csv":
            sc.read_csv(path)
    return sc


def fetch_scenarios_from_dir(path, csv=True, xlsx=False):
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
    xlsx : bool
        Search for xls files.

    Returns
    -------
    list : Scenarios found in the given directory.

    Examples
    --------
    >>> import shutil
    >>> from deflex.tools import TEST_PATH
    >>> test_data = os.path.join(os.path.dirname(__file__), os.pardir,
    ...                          os.pardir, "tests", "data")
    >>> my_csv = fetch_scenarios_from_dir(test_data)
    >>> len(my_csv)
    5
    >>> os.path.basename(my_csv[0])
    'deflex_2014_de02_co2-price_var-costs_csv'
    >>> my_excel = fetch_scenarios_from_dir(TEST_PATH, csv=False, xlsx=True)
    >>> len(my_excel)
    8
    >>> os.path.basename([e for e in my_excel if "short" in e][0])
    'de02_short.xlsx'
    >>> len(fetch_scenarios_from_dir(TEST_PATH, xlsx=True))
    8
    >>> s = load_scenario([e for e in my_excel if "short" in e][0])
    >>> csv_path = os.path.join(TEST_PATH, "de02_short_csv")
    >>> s.to_csv(csv_path)
    >>> len(fetch_scenarios_from_dir(TEST_PATH, xlsx=True))
    9
    >>> shutil.rmtree(csv_path)

    """
    xlsx_scenarios = []
    csv_scenarios = []
    for name in os.listdir(path):
        if name[-4:] == "xlsx" and xlsx is True:
            xlsx_scenarios.append(os.path.join(path, name))
        if name[-4:] == "_csv" and csv is True:
            csv_scenarios.append(os.path.join(path, name))
    csv_scenarios = sorted(csv_scenarios)
    xls_scenarios = sorted(xlsx_scenarios)
    logging.debug("Found xlsx scenario: %s", str(xls_scenarios))
    logging.debug("Found csv scenario: %s", str(csv_scenarios))
    return csv_scenarios + xls_scenarios


def model_multi_scenarios(scenarios, cpu_fraction=0.2, log_file=None):
    """

    Parameters
    ----------
    scenarios : iterable
        Multiple scenarios to be modelled in parallel.
    cpu_fraction : float
        Fraction of available cpu cores to use for the parallel modelling.
        A resulting dezimal number of cores will be rounded up to an integer.
    log_file : str
        Filename to store the log file.

    Returns
    -------

    Examples
    --------
    >>> from deflex.tools import fetch_example_results, TEST_PATH
    >>> fn1 = fetch_example_results("de02_short.xlsx")
    >>> fn2 = fetch_example_results("de02_short_broken.xlsx")
    >>> my_log_file = os.path.join(os.path.dirname(__file__), os.pardir,
    ...                            os.pardir, "tests", "data",
    ...                            "my_log_file.csv")
    >>> my_scenarios = [fn1, fn2]
    >>> model_multi_scenarios(my_scenarios, log_file=my_log_file)
    >>> my_log = pd.read_csv(my_log_file, index_col=[0])
    >>> good = my_log.loc["de02_short.xlsx"]
    >>> rv = good["return_value"]
    >>> datetime.strptime(rv, "%Y-%m-%d %H:%M:%S.%f").year > 2019
    True
    >>> good["trace"]
    nan
    >>> os.path.basename(good["result_file"])
    'de02_short.dflx'
    >>> broken = my_log.loc["de02_short_broken.xlsx"]
    >>> broken["return_value"].replace("'", "")  # doctest: +ELLIPSIS
    'ValueError(Missing time series for solar (capacity: 5.5) in DE02...
    >>> broken["trace"]  # doctest: +ELLIPSIS
    'Traceback (most recent call last)...
    >>> broken["result_file"]
    nan
    >>> os.remove(my_log_file)
    >>> os.remove(good["result_file"])
    """
    start = datetime.now()
    maximal_number_of_cores = int(
        round(multiprocessing.cpu_count() * cpu_fraction + 0.4999)
    )

    p = multiprocessing.Pool(maximal_number_of_cores)

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
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

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
    named : bool
        If True a named tuple with the following fields will be returned
    ignore_errors : bool
        Set True to stop the script if an error occurs for debugging. By
        default errors are ignored and returned.

    Returns
    -------
    namedtuple

    Examples
    --------
    >>> from deflex.tools import fetch_example_results
    >>> fn = fetch_example_results("de02_short.xlsx")
    >>> r = batch_model_scenario(fn, ignore_errors=False)  # doctest: +ELLIPSIS
    Welcome to the CBC MILP ...
    >>> r.name
    'de02_short.xlsx'
    >>> result_file = r.result_file
    >>> os.path.basename(result_file)
    'de02_short.dflx'
    >>> r.trace
    >>> r.return_value.year > 2019
    True
    >>> fn = os.path.join("wrong_file.xlsx")
    >>> r = batch_model_scenario(fn)
    >>> r.name
    'wrong_file.xlsx'
    >>> repr(r.return_value)
    "FileNotFoundError(2, 'No such file or directory')"
    >>> r.result_file
    >>> r.trace  # doctest: +ELLIPSIS
    'Traceback (most recent call last):...
    >>> os.remove(result_file)
    """
    out = namedtuple(
        "out", ["name", "return_value", "trace", "result_file", "start_time"]
    )
    name = os.path.basename(path)
    logging.info("Next scenario: %s", name)
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
        return_value = datetime.now()
        trace = None

    if not named:
        return name, return_value, trace, result_file, start_time

    return out(
        name=name,
        return_value=return_value,
        trace=trace,
        result_file=result_file,
        start_time=start_time,
    )


def model_scenario(
    path=None,
    file_type=None,
    result_path=None,
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
    result_path : str or None
        Path to store the output file. If None the results will be stored along
        with the scenarios.

    Returns
    -------

    Examples
    --------
    >>> from deflex.tools import fetch_example_results, TEST_PATH
    >>> fn = fetch_example_results("de02_short.xlsx")
    >>> r = model_scenario(fn, file_type="xlsx")  # doctest: +ELLIPSIS
    Welcome to the CBC MILP ...
    >>> f = os.path.join(os.path.dirname(fn), "results_cbc", "de02_short.dflx")
    >>> os.remove(f)
    """
    stopwatch()

    meta = {
        "model_base": "deflex",
        "solver": cfg.get("general", "solver"),
        "start_time": datetime.now(),
    }
    logging.info("Start modelling: %s", stopwatch())

    sc = load_scenario(path, file_type)

    # If a meta table exists in the table collection update meta dict
    sc.meta.update(meta)

    # Use name from meta or from filename
    sc.meta["auto_name"] = (
        os.path.basename(path) + "_" + datetime.now().strftime("%Y%d%m_%H%M%S")
    )
    if "name" not in sc.meta:
        sc.meta["name"] = sc.meta["auto_name"]

    if result_path is None:
        result_path = os.path.join(
            os.path.dirname(path),
            "results_{0}".format(cfg.get("general", "solver")),
            str(os.path.basename(path).split(".")[0]) + ".dflx",
        )

    logging.info("Solve the optimisation model: %s", stopwatch())
    sc.compute(solver=cfg.get("general", "solver"))

    logging.info("Solved. Dump results: %s", stopwatch())
    os.makedirs(os.path.dirname(result_path), exist_ok=True)

    logging.info("Dump file to %s", result_path)
    sc.meta["end_time"] = datetime.now()
    sc.dump(result_path)

    logging.info(
        "%s - deflex scenario finished without errors: %s",
        stopwatch(),
        sc.meta["name"],
    )
    return result_path


def plot_scenario(path, file_type=None, graphml_file=None):
    """
    Plot the graph of an energy system. If no filename is given the plot will
    be shown on the screen but not writen to an image file

    Parameters
    ----------
    path : str
        A valid deflex scenario file.
    file_type : str or None
        Type of the input data. Valid values are 'csv', 'excel', None. If the
        input is none the path should end on 'csv', '.xls', '.xlsx' to allow
        auto detection.
    graphml_file : str
        The path of the graphml.

    Returns
    -------
    TODO: Keep this test? It does not work without graphviz-dev and python3-dev
    Examples
    --------
    >>> from deflex.tools import fetch_example_results, TEST_PATH
    >>> fn = fetch_example_results("de02_short.xlsx")
    >>> fn_img = os.path.join(TEST_PATH, "test_es.graphml")
    >>> plot_scenario(fn, "xlsx", fn_img)
    >>> os.path.isfile(fn_img)
    True
    >>> os.remove(fn_img)
    >>> os.path.isfile(fn_img)
    False
    """
    sc = load_scenario(path, file_type)
    sc.table2es()

    show = graphml_file is None

    sc.plot_nodes(
        filename=graphml_file,
        show=show,
        remove_nodes_with_substrings=["bus_cs"],
    )


if __name__ == "__main__":
    pass
