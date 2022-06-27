Results
-------

All results are stored in the
:py:attr:`~deflex.DeflexScenario.results` attribute of the
:py:class:`~deflex.DeflexScenario` class. It is a dictionary with
the following keys:

 * main -- Results of all variables (result dictionary from oemof.solph)
 * param -- Input parameter
 * meta -- Meta information and tags of the scenario
 * problem -- Information about the linear problem such as `lower bound`,
   `upper bound` etc.
 * solver -- Solver results
 * solution -- Information about the found solution and the objective value

The ``deflex`` package provides some analyse functions as described below but
it is also possible to write your own post processing based on the oemof.solph
API. See the
`results chapter of the oemof.solph documentation
<https://oemof-solph.readthedocs.io/en/latest/usage.html#handling-results>`_
to learn how to handle the results.


Restore results
~~~~~~~~~~~~~~~

Most postprocessing functions need the results dictionary of the
``DeflexScenario`` as an input. So it is possible to restore only the results
dictionary. Nevertheless, also the whole ``DeflexScenario`` object can be
restored.

 * :py:func:`~deflex.restore_scenario` -- restore a full scenario
 * :py:func:`~deflex.restore_results` -- restore only the results dictionary.

Both function need the full file name (including the path) to the dumped
scenario as input parameter. If you have many dumped files onn your hard disc
you can use a search function to find and filter the files.

 * :py:func:`~deflex.search_dumped_scenarios` -- search dump files on your hard disc.

The output of the search function can be directly used in the restore
functions from above.

Postprocessing
~~~~~~~~~~~~~~

There are different types of postprocessing functions available. Some can be
used to verify the overall behaviour of the model. This can be used for
debugging but also for plausibility checks. Some can be used to calculated
additional key values from the results or to prepare the results to calculate
further values. Furthermore, it is possible to get the result from all
model variables in the ``xlsx`` or ``csv`` format.

For most postprocessing calculations cycles can cause problems because
assumptions are needed on how to deal with the cycles and it is difficult to
implement all possible assumptions in the functions. Therefore it might be
easier to use the basic preparation functions and write your own calculations.
See below on how to identify different kind of cycles.

Custom postprocessing
~~~~~~~~~~~~~~~~~~~~~

For a custom post processing it is possible to filter, group and prepare the
results to ones own needs. Use dictionary and list comprehensions to find the
needed flows and groups. The label and the class of the nodes can be used to
filter the nodes.

The keys of the ``results["main"]`` dictionary are tuples.

 * FLows: (<from_node>, <to_node>)
 * Components (<component>, None)
 * Buses (<bus>, None)

A node can be a component or a bus. The values of the tuples are the objects
or None.

Get the keys of all buses:

.. code-block:: python

    from oemof.solph import Bus
    bus_keys = [k for k in results["Main"].keys()
                if isinstance(k[0], Bus) and k[1] is None]


Get a list of buses:

.. code-block:: python

    from oemof.solph import Bus
    buses = [k[0] for k in results["Main"].keys()
             if isinstance(k[0], Bus) and k[1] is None]


Get a table of all flows from `pv` sources:

Long version:

.. code-block:: python

    import pandas as pd
    pv_keys = [
        k
        for k in results["Main"].keys()
        if k[0].label.tag == "volatile" and k[0].label.subtag == "solar"
    ]
    pv = {}
    for pv_key in pv_keys:
        pv[dflx.label2str(pv_key[0].label)] = results["Main"][pv_key][
            "sequences"
        ]["flow"]
    print(pd.DataFrame(pv))

Short version:

.. code-block:: python

    import pandas as pd
    pv = {
        dflx.label2str(k[0].label): v["sequences"]["flow"]
        for k, v in results["Main"].items()
        if k[0].label.tag == "volatile" and k[0].label.subtag == "solar"
    }
    print(pd.DataFrame(pv))

For more information about the results handling also see the
`results chapter of the oemof.solph documentation
<https://oemof-solph.readthedocs.io/en/latest/usage.html#handling-results>`_.

The following table gives an overview over the used classes and the naming of
the label of the deflex components and buses. Each label is a nametuple with
the fields `cat`, `tag`, `subtag` and `region`.

.. csv-table:: Classes and labels of deflex nodes
   :header: "", "class", "cat", "tag", "subtag", "region"

    **commodity bus**,Bus,commodity,all,<fuel>,<region>
    **electricity bus**,Bus,electricity,all,all,<region>
    **district heating bus**,Bus,heat,district,all,<region>
    **decentralised heat bus**,Bus,heat,decentralised,<fuel>,<region>
    **mobility bus**,Bus,mobility,all,<name>,<region>
    **shortage source**,Source,shortage,<cat of bus>,<subtag of bus>,<region>
    **commodity source**,Source,source,commodity,<fuel>,<region>
    **volatile source**,Source,source,volatile,<name>,<region>
    **power line**,Transformer,line,electricity,<from region>,<to region>
    **mobility system**,Transformer,mobility system,<name>,<fuel>,<region>
    **chp plant**,Transformer,chp plant,<name>,<fuel>,<region>
    **decentralised heat system**,Transformer,decentralised heat,<name>,<fuel>,<region>
    **heat plant**,Transformer,heat plant,<name>,<fuel>,<region>
    **power plant**,Transformer,power plant,<name>,<fuel>,<region>
    **other converter**,Transformer,other converter,<name>,<fuel>,<region>
    **excess sink**,Sink,excess,<cat of bus>,<subtag of bus>,<region>
    **electricity demand**,Sink,electricity demand,electricity,<name>,<region>
    **district heat demand**,Sink,heat demand,district,all,<region>
    **decentralised heat demand**,Sink,heat demand,decentralised,<fuel>,<region>
    **mobility demand**,Sink,mobility demand,mobility,<name>,<region>
    **other demand**,Sink,other demand,other,<fuel>,<region>
    **storages**,GenericStorage,storage,<medium>,<name>,<region>

Export all results
~~~~~~~~~~~~~~~~~~

To export the results from all variables into the ``xlsx`` or ``csv`` format,
the results can be stored in a collection of pandas.DataFrame. This collection
can be stored into a file. An example for this workflow can be found in the
documentation of the function:

 * :py:func:`~deflex.get_all_results` -- get all results as dictionary
 * :py:func:`~deflex.dict2file` -- store the dictionary into a file

Get common values from results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following values will be returned on an hourly base:

     * marginal costs [EUR/MWh]
     * highest emission [tons/MWh]
     * lowest emission [tons/MWh]
     * marginal costs power plant [-]
     * emission of marginal costs power plant [tons/MWh]

 * :py:func:`deflex.calculate_key_values` -- get key values on an hourly base

At the moment this works only with hourly time steps. This function is still
work in progress and may return more key values in the future. Please write an
issue on `github <https://github.com/reegis/deflex>`_ for a discussion about
further values.

Analyse flow cycles
~~~~~~~~~~~~~~~~~~~

As a directed graph is used to define an energy system. Cycles are defined as
a group of successive directed flows, where the first and the last node or bus
are the same. Small cycles are all storages. As this is a trivial solution of
a cycle analysis storages can be excluded. Another kind of cycles are the
combination of electrolysis and hydrogen power plants. Power lines will also
cause cycles. Pure power line cycles can also be excluded but this will not
exclude a cycle cause by an electrolysis in one region and a hydrogen power
plant in another even though a power line is included in this cycle.

A cycle may not be a problem if it is not used as a cycle in the system. So it
is also possible to analyse the usage of the cycle:

 1. cycle -- a cycle that can be used within the model
 2. used cycle -- a cycle in which all involved flows are used at least once.
 3. suspicious cycle -- a cycle in which all involved flows are used within one
    time step.

The following functions are available

 * :py:func:`~deflex.Cycles` -- initialise a Cycle object
 * :py:func:`~deflex.Cycles.cycles` -- all cycles in one table per cycle
 * :py:func:`~deflex.Cycles.used_cycles` -- all used cycles in one table per
   cycle
 * :py:func:`~deflex.Cycles.suspicious_cycles` -- all suspicious cycles in one
   table per cycle
 * :py:func:`~deflex.Cycles.get_suspicious_time_steps` -- get the time steps in
   which all flows are active
 * :py:func:`~deflex.Cycles.print` -- print an overview of all existing cycles
 * :py:func:`~deflex.Cycles.details` -- print a more detailed overview of all
   existing cycles

Analyse the energy system graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to convert the graph of the EnergySystem class into an nxgraph
of networkx. So, it is possible to use all methods and functions of networkx
associate with a directed graph (DiGraph). Furthermore, deflex provides some
function to associate colors with types of nodes or with the total weight of an
edge (flow). This can be used if the graph is exported to a ``graphml`` file.
Such a file can be opened in e.g. yEd where the colors can be used to display
the nodes and edges in the associated colors.

 * :py:func:`~deflex.DeflexGraph` -- initialise a `DeflexGraph` object
 * :py:func:`~deflex.DeflexGraph.nxgraph` -- get an `DiGraph` of networkx
 * :py:func:`~deflex.DeflexGraph.write` -- export the graph to a `graphml` file
 * :py:func:`~deflex.DeflexGraph.color_edges_by_weight` -- associate a color
   from a color map according to the total weight
 * :py:func:`~deflex.DeflexGraph.color_nodes_by_type` -- associate a color by
   the type of the node
 * :py:func:`~deflex.DeflexGraph.color_nodes_by_substring` -- associate a color
   by a substring of the label of the node
 * :py:func:`~deflex.DeflexGraph.group_nodes_by_type` -- group all nodes of the
   graph by their type

Get dual variables
~~~~~~~~~~~~~~~~~~

The dual variable is available for all buses in the energy system.

:py:func:`~deflex.fetch_dual_results` -- Get the resulta of the dual variables
of all buses in one table


CHP allocation
~~~~~~~~~~~~~~

These tool are mostly not connected to deflex but could be used in any context.
The functions just implement typical allocation methods in Python code:

 * :py:func:`~deflex.allocate_fuel_deflex` -- allocate the fuel with default values from a config file
 * :py:func:`~deflex.allocate_fuel` -- allocate the fuel with all values
   defined by the user
 * :py:func:`~deflex.efficiency_method` -- efficiency method
 * :py:func:`~deflex.exergy_method` -- carnot or exergy method
 * :py:func:`~deflex.finnish_method` -- alternative_generation or finnish
   method
 * :py:func:`~deflex.iea_method` -- IEA method


Arrange parts of the results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This parts can be used for plots and identification of the model

 * :py:func:`~deflex.solver_results2series` -- get the results returned from
   the external solver
 * :py:func:`~deflex.meta_results2series` -- get some general and meta results
 * :py:func:`~deflex.group_buses` -- group all buses by label
 * :py:func:`~deflex.get_time_index` -- get the used time index
 * :py:func:`~deflex.nodes2table` -- get an overview about all nodes and their total in- and outflows

Combine results and parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following functions can be used for further calculations. See the
examples for more information.

 * :py:func:`~deflex.fetch_converter_parameters` -- get all values related to
   the converter
 * :py:func:`~deflex.fetch_attributes_of_commodity_sources` -- get the values
   of the commodity sources
 * :py:func:`~deflex.get_combined_bus_balance` -- combine buses in a
   multiregion model
 * :py:func:`~deflex.get_converter_balance` -- the energy balance around
   converter to calculate emissions and costs


TABLE of LABELS!!!!
