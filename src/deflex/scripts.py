# -*- coding: utf-8 -*-

"""Main script.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

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
from functools import partial

import pandas as pd

from deflex.postprocessing.basic import get_all_results
from deflex.scenario_tools.scenario_io import create_scenario
from deflex.tools.files import dict2file


def stopwatch():
    """Track the running time."""
    if not hasattr(stopwatch, "start"):
        stopwatch.start = datetime.now()
    return str(datetime.now() - stopwatch.start)[:-7]


def model_multi_scenarios(
    scenarios, cpu_fraction=0.2, log_file=None, results=False
):
    """
    Model multi scenarios in parallel. Keep in mind that the memory usage
    is the critical resource for large models. So start with a low
    cpu_fraction to avoid memory errors.

    Parameters
    ----------
    scenarios : iterable
        Multiple scenarios to be modelled in parallel.
    cpu_fraction : float
        Fraction of available cpu cores to use for the parallel modelling.
        A resulting dezimal number of cores will be rounded up to an integer.
    log_file : str
        Filename to store the log file.
    results : bool
        Store an spreadsheet results file (default: False).

    Examples
    --------
    >>> from deflex import fetch_test_files, TEST_PATH
    >>> fn1 = fetch_test_files("de03_fictive_csv")
    >>> fn2 = fetch_test_files("de03_fictive_broken.xlsx")
    >>> my_log_file = os.path.join(TEST_PATH, "my_log_file.csv")
    >>> my_scenarios = [fn1, fn2]
    >>> model_multi_scenarios(my_scenarios, log_file=my_log_file)
    >>> my_log = pd.read_csv(my_log_file, index_col=[0])
    >>> good = my_log.loc["de03_fictive_csv"]
    >>> rv = good["return_value"]
    >>> datetime.strptime(rv, "%Y-%m-%d %H:%M:%S.%f").year > 2019
    True
    >>> good["trace"]
    nan
    >>> os.path.basename(good["dump"])
    'de03_fictive_csv.dflx'
    >>> good["results"]
    False
    >>> broken = my_log.loc["de03_fictive_broken.xlsx"]
    >>> broken["return_value"].replace("'", "")  # doctest: +ELLIPSIS
    'ValueError(Missing time series for geothermal (capacity: 12.56) in DE02...
    >>> broken["trace"]  # doctest: +ELLIPSIS
    'Traceback (most recent call last)...
    >>> broken["dump"]
    nan
    >>> os.remove(my_log_file)
    >>> os.remove(good["dump"])
    """
    start = datetime.now()
    maximal_number_of_cores = int(
        round(multiprocessing.cpu_count() * cpu_fraction + 0.4999)
    )
    logging.info(f"Multiprocessing will use {maximal_number_of_cores} cores.")
    p = multiprocessing.Pool(maximal_number_of_cores)
    bms = partial(batch_model_scenario, results=results, flat_tuple=True)
    logs = p.map(bms, scenarios)
    p.close()
    p.join()
    out = namedtuple(
        "out",
        ["name", "return_value", "trace", "dump", "results", "start_time"],
    )
    logs = [
        out(
            name=lo[0],
            return_value=lo[1],
            trace=lo[2],
            dump=lo[3],
            results=lo[4],
            start_time=lo[5],
        )
        for lo in logs
    ]
    failing = {
        log.name: log.return_value
        for log in logs
        if isinstance(log.return_value, BaseException)
    }
    logger = pd.DataFrame()
    for log in logs:
        logger.loc[log.name, "start"] = start
        logger.loc[log.name, "start_time"] = log.start_time
        if isinstance(log.return_value, BaseException):
            logger.loc[log.name, "return_value"] = repr(log.return_value)
        else:
            logger.loc[log.name, "return_value"] = log.return_value
        logger.loc[log.name, "trace"] = log.trace
        logger.loc[log.name, "dump"] = log.dump
        logger.loc[log.name, "results"] = log.results

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


def batch_model_scenario(
    path, file_type=None, ignore_errors=True, flat_tuple=False, **kwargs
):
    """
    Model a single scenario in batch mode. By default errors will be ignored
    and returned together with the traceback.

    Parameters
    ----------
    path : str
        A valid deflex scenario.
    file_type : str or None
        Type of the input data. Valid values are 'csv', 'xlsx', None. If the
        input is non the path should end on 'csv', '.xlsx'.
    ignore_errors : bool
        Set True to stop the script if an error occurs for debugging. By
        default errors are ignored and returned.
    flat_tuple : bool
        Return a normal tuple instead of a named tuple. This is needed for
        multi-process use. (default: False)

    Other Parameters
    ----------------
    dump : str or bool
        Path to store the dump file. If True the results will be stored along
        with the scenarios using the same name and the suffix `.dflx`. If False
        no dump will be stored (default: True).
    results : str or bool
        Path to store the results in an spreadsheet. If True the results will
        be stored along with the scenarios using the same name and the suffix
        `_results.xlsx`. If False no results will be stored (default: False).
    solver : str
        The solver to use for the optimisation (default: cbc).

    Returns
    -------
    namedtuple

    Examples
    --------
    >>> from deflex import fetch_test_files
    >>> fi = fetch_test_files("de02_heat_csv")
    >>> r = batch_model_scenario(fi, ignore_errors=False)  # doctest: +ELLIPSIS
    Welcome to the CBC MILP ...
    >>> r.name
    'de02_heat_csv'
    >>> my_dump_file = r.dump
    >>> os.path.basename(my_dump_file)
    'de02_heat_csv.dflx'
    >>> r.trace
    >>> r.return_value.year > 2019
    True
    >>> f_wrong = os.path.join("wrong_file.xlsx")
    >>> r = batch_model_scenario(f_wrong)
    >>> r.name
    'wrong_file.xlsx'
    >>> repr(r.return_value)
    "FileNotFoundError(2, 'No such file or directory')"
    >>> r.results
    >>> r.trace  # doctest: +ELLIPSIS
    'Traceback (most recent call last):...
    >>> os.remove(my_dump_file)
    """
    out = namedtuple(
        "out",
        ["name", "return_value", "trace", "dump", "results", "start_time"],
    )
    name = os.path.basename(path)
    logging.info("Next scenario: %s", name)
    start_time = datetime.now()

    if ignore_errors:
        try:
            back = model_scenario(path, file_type, **kwargs)
            rv = None
        except Exception as e:
            back = None
            rv = out(
                name=name,
                return_value=e,
                trace=traceback.format_exc(),
                dump=None,
                results=None,
                start_time=start_time,
            )
    else:
        back = model_scenario(path, file_type, **kwargs)
        rv = None

    if rv is None:
        rv = out(
            name=name,
            return_value=datetime.now(),
            trace=None,
            dump=back.dump,
            results=back.results,
            start_time=start_time,
        )
    if flat_tuple is True:
        rv = tuple([getattr(rv, f) for f in rv._fields])
    return rv


def model_scenario(
    path=None, file_type=None, dump=True, results=False, solver="cbc"
):
    """
    Compute a deflex scenario with the full work flow:

        * creating a scenario
        * loading the input data
        * computing the scenario
        * storing the results

    Parameters
    ----------
    path : str or None
        File or directory with a valid deflex scenario. If no path is given an
        energy system (es) has to be passed.
    file_type : str or None
        Type of the input data. Valid values are 'csv', 'xlsx', None. If the
        input is non the path should end on 'csv' or '.xlsx'.
    dump : str or bool
        Path to store the dump file. If True the results will be stored along
        with the scenarios using the same name and the suffix `.dflx`. If False
        no dump will be stored (default: True).
    results : str or bool
        Path to store the results in an spreadsheet. If True the results will
        be stored along with the scenarios using the same name and the suffix
        `_results.xlsx`. If False no results will be stored (default: False).
    solver : str
        The solver to use for the optimisation (default: cbc).

    Returns
    -------

    Examples
    --------
    >>> from deflex import fetch_test_files, TEST_PATH
    >>> fn = fetch_test_files("de02_no-heat.xlsx")
    >>> r = model_scenario(fn, file_type="xlsx", dump=True
    ...     )  # doctest: +ELLIPSIS
    Welcome to the CBC MILP ...
    >>> os.remove(fn.replace(".xlsx", ".dflx"))
    """
    stopwatch()

    out = namedtuple(
        "out",
        ["dump", "results"],
    )

    if dump is None and results is None:
        msg = (
            "You cannot compute a scenario without storing or dumping the "
            "results in any form,\nSet 'dump' or 'results' to True or define "
            "a dump path or a results path to store the results or dump the "
            "scenario."
        )
        raise AttributeError(msg)

    meta = {
        "model_base": "deflex",
        "solver": solver,
        "start_time": datetime.now(),
    }
    logging.info("Start modelling: %s", stopwatch())

    if file_type is None:
        if "xlsx" in os.path.basename(path):
            file_type = "xlsx"
        else:
            file_type = "csv"

    sc = create_scenario(path, file_type)

    # If a meta table exists in the table collection update meta dict
    sc.meta.update(meta)

    # Use name from meta or from filename
    sc.meta["auto_name"] = (
        os.path.basename(path) + "_" + datetime.now().strftime("%Y%d%m_%H%M%S")
    )
    if "name" not in sc.meta:
        sc.meta["name"] = sc.meta["auto_name"]

    logging.info("Solve the optimisation model: %s", stopwatch())
    sc.compute(solver=solver)

    logging.info("Solved. Dump results: %s", stopwatch())

    if dump is True:
        if file_type == "xlsx":
            dump = path.replace(".xlsx", ".dflx")
        else:
            dump = path + ".dflx"

    if dump is not None:
        os.makedirs(os.path.dirname(dump), exist_ok=True)
        logging.info("Dump file to %s", dump)
        sc.meta["end_time"] = datetime.now()
        if dump[-5:] != ".dflx":
            dump += ".dflx"
        sc.dump(dump)

    if results is True:
        if file_type == "xlsx":
            results = path.replace(".xlsx", "_results.xlsx")
        else:
            results = path + "_results"

    if results:
        os.makedirs(os.path.dirname(results), exist_ok=True)
        res = sc.results
        res["input_data"] = sc.input_data
        all_results = get_all_results(res)
        dict2file(all_results, results, file_type, drop_empty_columns=True)
        logging.info("Results have been written to %s", results)

    logging.info(
        "%s - deflex scenario finished without errors: %s",
        stopwatch(),
        sc.meta["name"],
    )
    return out(dump=dump, results=results)


if __name__ == "__main__":
    pass
