"""Work with the scenario data.

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

import calendar
import datetime
import logging
import os
import pprint as pp
import shutil
import sys
import warnings

import dill as pickle
import pandas as pd
from oemof import solph
from oemof.network import graph

from deflex import config as cfg
from deflex.nodes import create_solph_nodes_from_data

if sys.getrecursionlimit() < 3000:
    sys.setrecursionlimit(3000)


class NodeDict(dict):
    """Something."""

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
    """Scenario class."""

    def __init__(self, **kwargs):
        self.meta = kwargs.get("meta", {})
        self.input_data = kwargs.get("input_data", {})
        self.es = kwargs.get("es", None)
        self.results = kwargs.get("results", None)
        self.debug = kwargs.get("debug", None)

    def initialise_energy_system(self):
        """

        Returns
        -------

        """
        year = self.input_data["general"]["year"]
        time_steps = self.input_data["general"]["number of time steps"]
        # increment = self.input_data["general"]["time increment"]

        # Check leap year
        if calendar.isleap(year) and time_steps != 8784:
            msg = "{0} is a leap year but the number of time steps is {1}."
            warnings.warn(msg.format(year, time_steps), UserWarning)

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

    def load_xlsx(self, filename):
        """Load scenario from an excel-file."""
        suffix = filename.split(".")[-1]
        if not suffix == "xlsx":
            filename = filename + ".xlsx"
        xlsx = pd.ExcelFile(filename)
        for sheet in xlsx.sheet_names:
            table_index_header = cfg.get_list("table_index_header", sheet)
            table = xlsx.parse(
                sheet,
                index_col=list(range(int(table_index_header[0]))),
                header=list(range(int(table_index_header[1]))),
            )
            table.dropna(thresh=1, inplace=True)
            if table.isnull().any().any():
                columns = tuple(table.loc[:, table.isnull().any()].columns)
                msg = (
                    "NaN values found in table:'{0}', columns: {1}.\n"
                    "Empty cells are not allowed in a scenario to avoid "
                    "unwanted behaviour.\nRemove the whole column/row if a "
                    "parameter is not needed. "
                    "Consider that 0, 'inf' or 1 might be neutral values."
                ).format(sheet, columns)
                raise ValueError(msg)
            self.input_data[sheet] = table.dropna(thresh=(len(table.columns)))

        self.input_data["general"] = self.input_data["general"]["value"]
        self.meta.update(self.input_data["general"].to_dict())

        return self

    def load_csv(self, path):
        """Load scenario from a csv-collection."""
        for file in os.listdir(path):
            if file[-4:] == ".csv":
                name = file[:-4]
                table_index_header = cfg.get_list("table_index_header", name)
                filename = os.path.join(path, file)
                self.input_data[name] = pd.read_csv(
                    filename,
                    index_col=list(range(int(table_index_header[0]))),
                    header=list(range(int(table_index_header[1]))),
                    squeeze=True,
                )
        self.meta.update(self.input_data["general"].to_dict())
        return self

    def to_xlsx(self, filename):
        """Dump scenario into an excel-file."""
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
        """Dump scenario into a csv-collection."""
        if os.path.isdir(path):
            shutil.rmtree(os.path.join(path))
        os.makedirs(path)

        for name, df in self.input_data.items():
            name = name.replace(" ", "_") + ".csv"
            filename = os.path.join(path, name)
            df.to_csv(filename)
        logging.info("Scenario saved as csv-collection to %s", path)

    def check_table(self, table_name):
        """

        Parameters
        ----------
        table_name

        Returns
        -------

        """
        if self.input_data[table_name].isnull().values.any():
            c = []
            for column in self.input_data[table_name].columns:
                if self.input_data[table_name][column].isnull().any():
                    c.append(column)
            msg = "Nan Values in the {0} table (columns: {1})."
            raise ValueError(msg.format(table_name, c))
        return self

    def create_nodes(self):
        """

        Returns
        -------
        dict

        """

    def compute(self, **kwargs):
        """

        Returns
        -------

        """
        self.table2es()
        logging.info("Creating the linear model...")
        model = solph.Model(self.es)
        logging.info("Done. Optimise the model.")
        self.solve(model, **kwargs)

    def add_nodes(self, nodes):
        """

        Parameters
        ----------
        nodes : dict
            Dictionary with a unique key and values of type oemof.network.Node.

        Returns
        -------
        self

        """
        if self.es is None:
            self.initialise_energy_system()
        self.es.add(*nodes.values())
        return self

    def table2es(self):
        """

        Returns
        -------

        """
        if self.es is None:
            logging.info("Initialise a solph energy system.")
            self.initialise_energy_system()
        logging.info("Creating nodes...")
        self.es.add(*self.create_nodes().values())
        logging.info("Done. Nodes added to the energy system.")
        return self

    def create_model(self):
        """

        Returns
        -------

        """
        model = solph.Model(self.es)
        return model

    def dump(self, filename, meta=None):
        """

        Parameters
        ----------
        filename : str
        meta : str

        Returns
        -------

        """
        suffix = filename.split(".")[-1]
        if not suffix == "dflx":
            filename = filename + ".dflx"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        f = open(filename, "wb")
        if meta is None:
            if "Meta" in self.results or "meta" in self.results:
                meta = self.results["meta"]
        pickle.dump(meta, f)
        pickle.dump(self.__dict__, f)
        f.close()
        logging.info("Results dumped to %s.", filename)

    def solve(
        self, model, with_duals=False, tee=True, logfile=None, solver=None
    ):
        """

        Parameters
        ----------
        model
        with_duals
        tee
        logfile
        solver

        Returns
        -------

        """
        logging.info("Optimising using %s.", solver)

        self.meta["solph_version"] = solph.__version__
        self.meta["solver"] = solver
        self.meta["solver_start"] = datetime.datetime.now()

        if with_duals:
            model.receive_duals()

        if self.debug:
            filename = os.path.join(
                solph.helpers.extend_basic_path("lp_files"), "reegis.lp"
            )
            logging.info("Store lp-file in %s.", filename)
            model.write(filename, io_options={"symbolic_solver_labels": True})
            # ToDo: Try to plot a graph

        model.solve(
            solver=solver, solve_kwargs={"tee": tee, "logfile": logfile}
        )

        self.meta["solver_end"] = datetime.datetime.now()

        self.es.results["main"] = solph.processing.results(model)
        self.es.results["meta"] = solph.processing.meta_results(model)
        self.es.results["param"] = solph.processing.parameter_as_dict(self.es)
        self.es.results["meta"].update(self.meta)

        self.results = self.es.results

    def plot_nodes(self, filename=None, **kwargs):
        """

        Parameters
        ----------
        filename
        kwargs

        Returns
        -------

        """

        if "remove_nodes_with_substrings" in kwargs:
            rm_nodes = kwargs.pop("remove_nodes_with_substrings")
        else:
            rm_nodes = None

        g = graph.create_nx_graph(
            self.es, filename=filename, remove_nodes_with_substrings=rm_nodes
        )
        return g


class DeflexScenario(Scenario):
    """Something"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.extra_regions = kwargs.get("extra_regions", list())

    def create_nodes(self):
        """

        Returns
        -------

        """
        # Create  a special dictionary that will raise an error if a key is
        # updated. This avoids the
        nodes = NodeDict()

        return create_solph_nodes_from_data(
            self.input_data, nodes, extra_regions=self.extra_regions
        )


def restore_scenario(filename, scenario_class):
    """

    Parameters
    ----------
    filename
    scenario_class

    Returns
    -------

    """

    if filename.split(".")[-1] != "dflx":
        msg = (
            "The suffix of a valid deflex scenario has to be '.dflx'.\n"
            "Cannot open {0}.".format(filename)
        )
        raise IOError(msg)
    f = open(filename, "rb")
    meta = pickle.load(f)
    logging.info("Meta information:\n" + pp.pformat(meta))
    sc = scenario_class()
    sc.__dict__ = pickle.load(f)
    f.close()
    logging.info("Results restored from %s.", filename)
    return sc


def convert_esys2dflx(path):
    """
    Convert .esys files with deflex results into .dflx files.

    Parameters
    ----------
    path : str
        Directory which contains solved and dumped deflex scenarios from
        deflex >= 0.2.

    Returns
    -------

    """
    for fn in os.listdir(path):
        if ".esys" in fn:
            filename = os.path.join(path, fn)
            sc = DeflexScenario()
            sc.es = solph.EnergySystem()
            f = open(filename, "rb")
            meta = pickle.load(f)
            logging.info("Meta information:\n" + pp.pformat(meta))
            sc.es.__dict__ = pickle.load(f)
            f.close()
            sc.results = sc.es.results
            logging.info("Results restored from %s.", filename)
            sc.name = os.path.basename(filename).split(".")[0]
            sc.debug = False
            sc.input_data = sc.results["meta"]["scenario"].pop("scenario")
            sc.dump(os.path.join(os.path.dirname(filename), sc.name))
