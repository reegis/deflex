# -*- coding: utf-8 -*-

"""Work with the scenario data.

SPDX-FileCopyrightText: 2016-2021 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import datetime
import logging
import os
import shutil
import sys
import warnings

import dill as pickle
import pandas as pd
from oemof import solph
from oemof.network import graph

from deflex import config as cfg
from deflex.scenario_tools.nodes import create_solph_nodes_from_data

if sys.getrecursionlimit() < 3000:
    sys.setrecursionlimit(3000)


class NodeDict(dict):
    """
    A dictionary where existing key-value-pairs cannot be overwritten.

    A NodeDict can collect values with unique keys. Therefore a duplicate key
    will raise a ``KeyError`` instead of overwriting the existing key
    silently.
    """

    def __setitem__(self, key, item):
        if super().get(key) is None:
            super().__setitem__(key, item)
        else:
            msg = (
                "Key '{0}' already exists. ".format(key)
                + "Duplicate keys are not allowed in a node dictionary."
            )
            raise KeyError(msg)


class Scenario:
    """
    Basic scenario class.

    Attributes
    ----------
    input_data : dict
        The input data is organised in a dictionary of pandas.DataFrame/
        pandas.Series. The keys are the data names (string) and the values are
        the data tables.
    results : dict
        The results are stored in a dictionary with tuples as keys and the
        results as values (nested dictionary with pandas.DataFrame). The tuples
        contain the node object in the following form:
        (from_node, to_node) for flows and (node, None) for components. See the
        `solph documentation
        <https://oemof-solph.readthedocs.io/en/latest/usage.html#handling-results>`_
        for more details.
    meta : dict
        Meta information that can be used to search for in stored scenarios.
        The dictionary keys can be used like tags or categories.
    es : oemof.solph.EnergySystem
        This attribute will hold the oemof.solph.EnergySystem.

    """

    def __init__(self, meta=None, input_data=None, es=None, results=None):
        self.meta = {} if meta is None else meta
        self.input_data = {} if input_data is None else input_data
        self.es = es
        self.results = results

    def initialise_energy_system(self):
        """
        Create a solph.EnergySystem and store it in the es attribute. The
        input_data attribute has to contain the input data to use this method.

        Returns
        -------
        self

        """
        if not self.input_data:
            raise ValueError(
                "There is no input data in the scenario. You cannot "
                "initialise an energy system without a year and the number of "
                "time steps."
            )
        year = int(self.input_data["general"]["year"])
        time_steps = int(self.input_data["general"]["number of time steps"])

        # Check series tables
        for key in [t for t in self.input_data.keys() if "series" in t]:
            if time_steps != len(self.input_data[key]):
                msg = (
                    "Number of time steps is {0} but the length of the {1}"
                    " table is {2}."
                ).format(time_steps, key, len(self.input_data[key]))
                raise ValueError(msg)

        # Create datetime index
        date_time_index = pd.date_range(
            "1/1/{0}".format(year), periods=time_steps, freq="H"
        )

        self.es = solph.EnergySystem(timeindex=date_time_index)

        return self

    def read_xlsx(self, filename):
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
        for sheet in xlsx.sheet_names:
            table_index_header = cfg.get_list("table_index_header", sheet)
            self.input_data[sheet] = xlsx.parse(
                sheet,
                index_col=list(range(int(table_index_header[0]))),
                header=list(range(int(table_index_header[1]))),
            )
            if "series" not in sheet:
                self.input_data[sheet] = self.input_data[sheet].squeeze(
                    "columns"
                )
        self.check_input_data()
        self._add_meta_data()
        return self

    def read_csv(self, path):
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
        for file in os.listdir(path):
            if file[-4:] == ".csv":
                name = file[:-4]
                table_index_header = cfg.get_list("table_index_header", name)
                filename = os.path.join(path, file)
                self.input_data[name] = pd.read_csv(
                    filename,
                    index_col=list(range(int(table_index_header[0]))),
                    header=list(range(int(table_index_header[1]))),
                )
                if "series" not in name:
                    self.input_data[name] = self.input_data[name].squeeze(
                        "columns"
                    )
        self.check_input_data()
        self._add_meta_data()
        return self

    def _add_meta_data(self):
        if "info" in self.input_data:
            self.meta.update(self.input_data["info"].to_dict())
        self.meta.update(self.input_data["general"].to_dict())

    def check_input_data(self):
        """
        Check the input data for NaN values.
        If warning is True (default: False) a warning for all tables is raised
        that contain NaN values. This is useful if you suspect many NaN values
        in your data set, so you get a good overview over all the corrupt
        columns. Otherwise an exception is raised on the first occurrence of
        NaN values.

        Examples
        --------
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
        >>> sc = dflx.create_scenario(fn, "csv")
        >>> sc.input_data["electricity demand series"].iloc[15] = float("nan")
        >>> sc.input_data["volatile series"].iloc[11] = float("nan")
        >>> sc.check_input_data()  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: NaN values found in the following tables: electricity...
        """
        has_warning = []
        for sheet, table in self.input_data.items():
            msg = (
                "NaN values found in table:'{0}', column(s): {1}.\n"
                "Empty cells are not allowed in a scenario to avoid "
                "unwanted behaviour.\nRemove the whole column/row if "
                "a parameter is not needed (optional). Consider that 0, 'inf' "
                "or 1 might be neutral values to replace NaN values."
            )
            if isinstance(table, pd.DataFrame):
                # table.dropna(thresh=1, inplace=True, axis=0)
                # table.dropna(thresh=1, inplace=True, axis=1)
                if table.isnull().any().any():
                    columns = tuple(table.loc[:, table.isnull().any()].columns)
                    msg = msg.format(sheet, columns)
                    warnings.warn(msg, UserWarning)
                    has_warning.append(sheet)
                self.input_data[sheet] = table.dropna(
                    thresh=(len(table.columns))
                )
            else:
                if table.isnull().any():
                    value = table.loc[table.isnull()].index
                    msg = msg.format(sheet, value)
                    warnings.warn(msg, UserWarning)
                    has_warning.append(sheet)

        if isinstance(self.input_data["volatile plants"], pd.Series):
            self.input_data["volatile plants"] = pd.DataFrame(
                self.input_data["volatile plants"],
                columns=[self.input_data["volatile plants"].name],
            )
        if len(has_warning) > 0:
            msg = (
                "NaN values found in the following tables: {0}\n"
                "See the warning above for more information"
            )
            raise ValueError(msg.format(", ".join(has_warning)))

    def to_xlsx(self, filename):
        """
        Store the input data into an xlsx-file.

        filename : str
            Full path to the filename.

        Examples
        --------
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
        >>> sc = dflx.DeflexScenario()
        >>> # read scenario from xlsx-file
        >>> sc = sc.read_csv(fn)
        >>> # store scenario as csv-collection.
        >>> sc.to_xlsx(fn.replace("_csv", ".xlsx"))

        """
        # create path if it does not exist
        suffix = filename.split(".")[-1]
        if not suffix == "xlsx":
            filename = filename + ".xlsx"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        writer = pd.ExcelWriter(filename)
        for name, df in sorted(self.input_data.items()):
            df.to_excel(writer, name)
        writer.save()
        logging.info("Scenario saved as excel file to %s", filename)

    def to_csv(self, path):
        """
        Store the input data as a csv-collection.

        filename : str
            Full path to the filename.

        Examples
        --------
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat.xlsx")
        >>> sc = dflx.DeflexScenario()
        >>> # read scenario from xlsx-file
        >>> sc = sc.read_xlsx(fn)
        >>> # store scenario as csv collection.
        >>> sc.to_csv(fn.replace(".xlsx", "_csv"))

        """
        if os.path.isdir(path):
            shutil.rmtree(os.path.join(path))
        os.makedirs(path)

        for name, df in self.input_data.items():
            name += ".csv"
            filename = os.path.join(path, name)
            df.to_csv(filename)
        logging.info("Scenario saved as csv-collection to %s", path)

    def create_nodes(self):
        """This method is a placeholder for the child classes."""

    def compute(self, solver="cbc", with_duals=True, **kwargs):
        """
        Create a solph.Model from the input data and optimise it using an
        external solver. Afterwards the results are stored in the results
        attribute.

        Parameters
        ----------
        solver : str
            The name of the solver as used in the Pyomo package like cbc, glpk,
            gurobi, cplex... (default: cbc).
        with_duals : bool
            Receive the dual variables of all buses in the results (default:
            True).

        Examples
        --------
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
        >>> sc = dflx.create_scenario(fn, "csv")
        >>> sc.results is None
        True
        >>> sc.compute()  # doctest: +ELLIPSIS
        Welcome to the CBC MILP ...
        >>> sc.results.keys()
        ['Problem', 'Solver', 'Solution', 'Main', 'Param', 'Meta']
        """
        self.table2es()
        self.solve(self.create_model(), solver=solver, **kwargs)

    def add_nodes_to_es(self, nodes):
        """
        Add nodes to an existing solph.EnergySystem. If the EnergySystem does
        not exist an Error is raised. This method is included in the
        :py:meth:`~deflex.scenario.Scenario.compute()` method and is only
        needed for advanced usage.

        Parameters
        ----------
        nodes : dict
            Dictionary with a unique key and values of type oemof.network.Node.

        Returns
        -------
        self

        """
        self.es.add(*nodes.values())
        return self

    def table2es(self):
        """
        Create a populated solph.EnergySystem from the input data.

        The EnergySystem object will be stored in the
        :py:attr:`~deflex.scenario.DeflexScenario.es` attribute.

        This method is included in the
        :py:meth:`~deflex.scenario.Scenario.compute()`
        method and is only needed for advanced usage.

        Examples
        --------
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
        >>> sc = dflx.create_scenario(fn, "csv")
        >>> sc.es is None
        True
        >>> sc.table2es()
        >>> type(sc.es)
        <class 'oemof.solph.network.energy_system.EnergySystem'>

        """
        if self.es is None:
            logging.info("Initialise a solph energy system.")
            self.initialise_energy_system()
        logging.info("Creating nodes...")
        self.es.add(*self.create_nodes().values())
        logging.info("Done. Nodes added to the energy system.")

    def create_model(self):
        """
        This method is included in the
        :py:meth:`~deflex.scenario.Scenario.compute()` method and is only
        needed for advanced usage.

        Returns
        -------
        solph.Model

        Examples
        --------
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
        >>> sc = dflx.create_scenario(fn, "csv")
        >>> sc.table2es()
        >>> type(sc.create_model())
        <class 'oemof.solph.models.Model'>

        """
        logging.info("Creating the model this may take a while...")
        model = solph.Model(self.es)
        logging.info("...Done.")
        return model

    def compute_debug(self):
        """
        The plan is to make it easy to debug an energy system.

        1. Create an EnergySystem with just 5 time steps
        2. Reduce the input data (all series) to 5 time steps
        3. Plot the graph (try/except)
        4. Write an LP file (try/except)
        5. Solve and dump the results (try/except)

        model = solph.Model(self.es)

        filename = os.path.join(solph.helpers.extend_basic_path("lp_files"),
        "reegis.lp")

        logging.info("Store lp-file in %s.", filename)

        model.write(filename, io_options={"symbolic_solver_labels": True})

        """

    def dump(self, filename):
        """
        Store a solved scenario class into the binary pickle format.

        The file will be stored with the suffix `.dflx`. If the given filename
        does not contain the suffix, it will be added to the filename.

        It is possible to restore the dump but it is not possible to compute
        a restored dump. Unsolved scenarios should be stored in the xlsx or
        csv format.

        >>> import os
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
        >>> sc = dflx.create_scenario(fn, "csv")
        >>> sc.results is None
        True
        >>> sc.compute()  # doctest: +ELLIPSIS
        Welcome to the CBC MILP ...
        >>> fn_dump = fn.replace("_csv", ".dflx")
        >>> os.path.basename(fn_dump)
        'de02_no-heat.dflx'
        >>> sc.dump(fn_dump)
        >>> os.path.isfile(fn_dump)
        True
        >>> sc2 = dflx.restore_scenario(fn_dump)
        >>> type(sc2)
        <class 'deflex.scenario.DeflexScenario'>
        >>> sc2.results.keys()
        ['Problem', 'Solver', 'Solution', 'Main', 'Param', 'Meta']
        >>> os.remove(fn_dump)
        """
        suffix = filename.split(".")[-1]
        if not suffix == "dflx":
            filename = filename + ".dflx"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        f = open(filename, "wb")
        pickle.dump(self.meta, f)
        pickle.dump(self.__dict__, f)
        f.close()
        logging.info("Results dumped to %s.", filename)

    def solve(self, model, solver="cbc", with_duals=True, **solver_kwargs):
        """
        Solve the solph.Model. This method is included in the
        :py:meth:`~deflex.scenario.Scenario.compute()` method and is only
        needed for advanced usage.

        Parameters
        ----------
        model : oemof.solph.Model
        solver : str
        with_duals : bool

        Other Parameters
        ----------------
        tee : bool
            Set to `False` to suppress the solver output (default: True).
        logfile : str
            Define the path where to store the log file of the solver.

        Examples
        --------
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
        >>> sc = dflx.create_scenario(fn, "csv")
        >>> sc.table2es()
        >>> my_model = sc.create_model()
        >>> sc.solve(my_model, with_duals=False)  # doctest: +ELLIPSIS
        Welcome to the CBC MILP ...
        >>> sc.results.keys()
        ['Problem', 'Solver', 'Solution', 'Main', 'Param', 'Meta']

        """
        logging.info("Optimising using %s.", solver)

        solver_kwargs["tee"] = solver_kwargs.get("tee", True)

        self.meta["solph_version"] = solph.__version__
        self.meta["solver_name"] = solver
        self.meta["solver_start"] = datetime.datetime.now()

        if with_duals:
            model.receive_duals()

        model.solve(solver=solver, solve_kwargs=solver_kwargs)

        self.meta["solver_end"] = datetime.datetime.now()

        self.es.results["main"] = solph.processing.results(model)
        self.meta.update(solph.processing.meta_results(model))
        self.es.results["param"] = solph.processing.parameter_as_dict(self.es)
        self.es.results["meta"] = self.meta

        self.results = self.es.results

    def store_graph(self, filename, **kwargs):
        """
        Store the EnergySystem graph into a `.graphml` file.

        The kwargs are passed to the oemof.network function
        `create_nx_graph()
        <https://github.com/oemof/oemof.network/blob/dev/src/oemof/network/graph.py#L15>`_.

        Parameters
        ----------
        filename : str
            Full path of the graphml-file.

        Examples
        --------
        >>> import os
        >>> import deflex as dflx
        >>> fn = dflx.fetch_test_files("de02_no-heat_csv")
        >>> sc = dflx.create_scenario(fn, "csv")
        >>> sc.table2es()
        >>> fn_graph = fn.replace("_csv", ".graphml")
        >>> os.path.basename(fn_graph)
        'de02_no-heat.graphml'
        >>> sc.store_graph(fn_graph)
        >>> os.path.isfile(fn_graph)
        True
        >>> os.remove(fn_graph)

        """

        graph.create_nx_graph(self.es, filename=filename, **kwargs)


class DeflexScenario(Scenario):
    """
    The Deflex Scenario is the center of a deflex energy model. It can store
    the needed input data and the results after a successful optimisation.
    a inherits from the Scenario class and extends the
    Scenario class with valid nodes creation. Additionally one can define
    an extra_regions attribute to create an extra commodity source for these
    regions. This makes it possible to create a source balance for these
    regions.

    Parameters
    ----------
    meta : dict
        Meta information of the DeflexScenario (optional).
    input_data : dict
        A dictionary of tables in the deflex scenario style (optional).
    es : oemof.solph.EnergySystem class
        An Energy system (optional).
    results : dict
        A valid Deflex results dictionary (optional).

    """

    __doc__ += "\n".join(Scenario.__doc__.split("\n")[2:])

    def __init__(self, meta=None, input_data=None, es=None, results=None):
        super().__init__(
            meta=meta, input_data=input_data, es=es, results=results
        )

    def create_nodes(self):
        """
        Creates solph components and buses from the input data and store them
        in a dictionary with unique IDs as keys.

        Returns
        -------
        dict

        """
        # Create  a special dictionary that will raise an error if a key is
        # updated. This avoids the
        nodes = NodeDict()

        return create_solph_nodes_from_data(self.input_data, nodes)
