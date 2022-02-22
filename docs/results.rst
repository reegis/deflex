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

:py:func:`deflex.calculate_key_values`

...work in progress.

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

 * :py:func:`~deflex.allocate_fuel_deflex` --
 * :py:func:`~deflex.allocate_fuel` --
 * :py:func:`~deflex.efficiency_method` --
 * :py:func:`~deflex.exergy_method` --
 * :py:func:`~deflex.finnish_method` --
 * :py:func:`~deflex.iea_method` --


Arrange parts of the results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 * :py:func:`~deflex.solver_results2series` --
 * :py:func:`~deflex.meta_results2series` --
 * :py:func:`~deflex.group_buses` --
 * :py:func:`~deflex.get_time_index` --
 * :py:func:`~deflex.nodes2table` --

Combine results and parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 * :py:func:`~deflex.fetch_converter_parameters` --
 * :py:func:`~deflex.fetch_attributes_of_commodity_sources` --
 * :py:func:`~deflex.get_combined_bus_balance` --
 * :py:func:`~deflex.get_converter_balance` --


TABLE of LABELS!!!!