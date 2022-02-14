import logging
import os
import pickle
import pprint as pp
import warnings

from deflex.scenario import DeflexScenario


def search_dumped_scenarios(path, extension="dflx", **parameter_filter):
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
    >>> from deflex import TEST_PATH
    >>> from deflex  import fetch_test_files
    >>> my_file_name = fetch_test_files("de17_heat.dflx")
    >>> res = search_dumped_scenarios(path=TEST_PATH, map=["de17"])
    >>> len(res)
    2
    >>> sorted(res)[0].split(os.sep)[-1]
    'de17_heat.dflx'
    >>> res = search_dumped_scenarios(path=TEST_PATH, map=["de17", "de21"])
    >>> len(res)
    6
    >>> res = search_dumped_scenarios(
    ...     path=TEST_PATH, map=["de17", "de21"], heat=["True"])
    >>> len(res)
    3
    >>> sorted(res)[0].split(os.sep)[-1]
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
        files = {
            k: v
            for k, v in files.items()
            if any(
                [
                    str(v.get(filter_key)).lower() == str(f).lower()
                    for f in filter_value
                ]
            )
        }
    return list(files.keys())


def search_input_scenarios(path, csv=True, xlsx=False, exclude=None):
    """
    Search for files with an .xlsx extension or directories ending with '_csv'.

    By now it is not possible to distinguish between valid deflex scenarios and
    other xlsx-files or directories ending with '_csv'. Therefore, the given
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
    exclude : str
        A string that is not allowed in the filename. Filenames containing this
        strings will be excluded.
    Returns
    -------
    list : Scenarios found in the given directory.

    Examples
    --------
    >>> import shutil
    >>> from deflex import fetch_test_files, search_input_scenarios
    >>> test_file = fetch_test_files("de02_heat.xlsx")
    >>> test_path = os.path.dirname(test_file)
    >>> my_csv = search_input_scenarios(test_path)
    >>> len(my_csv)
    16
    >>> os.path.basename(my_csv[0])
    'de02_heat_csv'
    >>> my_xlsx = search_input_scenarios(test_path, csv=False, xlsx=True)
    >>> len(my_xlsx)
    17
    >>> os.path.basename([e for e in my_xlsx][0])
    'de02_heat.xlsx'
    >>> len(search_input_scenarios(test_path, xlsx=True))
    33
    >>> scenario = create_scenario([e for e in my_xlsx][0])
    >>> csv_path = os.path.join(test_path, "de02_new_csv")
    >>> scenario.to_csv(csv_path)
    >>> len(search_input_scenarios(test_path, xlsx=True))
    34
    >>> len(search_input_scenarios(test_path, xlsx=True, exclude="de02"))
    25
    >>> len(search_input_scenarios(test_path, xlsx=True, exclude="test"))
    34
    >>> shutil.rmtree(csv_path)  # remove test results, skip this line to go on

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
    all_scenarios = csv_scenarios + xls_scenarios
    if exclude is not None:
        all_scenarios = [
            s for s in all_scenarios if exclude not in os.path.basename(s)
        ]
    return all_scenarios


def search_results(path, extension="dflx", **parameter_filter):
    """Keep the old name to keep the old API"""
    msg = (
        "'search_results' is deprecated. Use 'search_dumped_scenarios` "
        "instead."
    )
    warnings.warn(msg, FutureWarning)
    search_dumped_scenarios(path, extension, **parameter_filter)


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
    >>> from deflex import fetch_test_files
    >>> fn1 = fetch_test_files("de21_no-heat_transmission.dflx")
    >>> fn2 = fetch_test_files("de02_no-heat.dflx")
    >>> sorted(restore_results(fn1).keys())
    ['Input data', 'Main', 'Meta', 'Param', 'Problem', 'Solution', 'Solver']
    >>> sorted(restore_results([fn1, fn2])[0].keys())
    ['Input data', 'Main', 'Meta', 'Param', 'Problem', 'Solution', 'Solver']
    """
    if not isinstance(file_names, list):
        file_names = list((file_names,))
    results = []

    for path in file_names:
        sc = restore_scenario(path, scenario_class)
        tmp_res = sc.results
        tmp_res["meta"]["filename"] = os.path.basename(path)
        tmp_res["input_data"] = sc.input_data
        results.append(tmp_res)

    if len(results) < 2:
        results = results[0]
    return results


def restore_scenario(filename, scenario_class=DeflexScenario):
    """
    Create a Scenario from a dump file (`.dflx`). By default a DeflexScenario
    is created but a different Scenario class can be passed. The Scenario
    has to be equal to the dumped Scenario otherwise the restore will fail.

    Parameters
    ----------
    filename : str
        The path to the dumped file (`.dflx`).
    scenario_class : class
        A child of the deflex.Scenario class or the Scenario class itself.

    Returns
    -------
    deflex.Scenario

    """
    if filename.split(".")[-1] != "dflx":
        msg = (
            "The suffix of a valid deflex scenario has to be '.dflx'.\n"
            "Cannot open {0}.".format(filename)
        )
        raise IOError(msg)
    f = open(filename, "rb")
    meta = pickle.load(f)
    logging.info("Meta information:\n %s", pp.pformat(meta))
    sc = scenario_class()
    sc.__dict__ = pickle.load(f)
    f.close()
    logging.info("Results restored from %s.", filename)
    return sc


def create_scenario(path, file_type=None):
    """
    Create a deflex scenario object from file.

    Parameters
    ----------
    path : str
        A valid deflex scenario file.
    file_type : str or None
        Type of the input data. Valid values are 'csv', 'xlsx', None. If the
        input is non the path should end on 'csv', '.xlsx' to allow
        auto-detection.

    Returns
    -------
    deflex.DeflexScenario

    Examples
    --------
    >>> from deflex import fetch_test_files, TEST_PATH
    >>> fn = fetch_test_files("de17_heat.xlsx")
    >>> s = create_scenario(fn, file_type="xlsx")
    >>> type(s)
    <class 'deflex.scenario.DeflexScenario'>
    >>> int(s.input_data["volatile plants"]["capacity"]["DE01", "wind"])
    3815
    >>> type(create_scenario(fn))
    <class 'deflex.scenario.DeflexScenario'>
    >>> create_scenario(fn, file_type="csv"
    ...     )  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
     ...
    NotADirectoryError: [Errno 20] Not a directory:

    """
    sc = DeflexScenario()

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
        elif file_type == "csv":
            sc.read_csv(path)
    return sc
