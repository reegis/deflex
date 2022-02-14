.. currentmodule:: deflex

Reference
=========

Scenario
++++++++

Scenario class
--------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.Scenario
    deflex.DeflexScenario

Read/Write a scenario
---------------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.DeflexScenario.read_xlsx
    deflex.DeflexScenario.read_csv
    deflex.DeflexScenario.to_xlsx
    deflex.DeflexScenario.to_csv
    deflex.DeflexScenario.dump
    deflex.DeflexScenario.store_graph

Compute scenario
----------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.DeflexScenario.compute

Advanced scenario methods
-------------------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.DeflexScenario.check_input_data
    deflex.DeflexScenario.table2es
    deflex.DeflexScenario.create_model
    deflex.DeflexScenario.create_nodes
    deflex.DeflexScenario.solve

Scripts
+++++++

Python scripts
-------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.model_scenario
    deflex.batch_model_scenario
    deflex.model_multi_scenarios

Console scripts
---------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.console_scripts.main


Postprocessing
++++++++++++++

Analyse and draw graph
----------------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.postprocessing.graph.Edge
    deflex.DeflexGraph
    deflex.DeflexGraph.nxgraph
    deflex.DeflexGraph.write
    deflex.DeflexGraph.color_edges_by_weight
    deflex.DeflexGraph.color_nodes_by_type
    deflex.DeflexGraph.color_nodes_by_substring
    deflex.DeflexGraph.group_nodes_by_type

Analyse cycles
--------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.Cycles
    deflex.Cycles.cycles
    deflex.Cycles.used_cycles
    deflex.Cycles.suspicious_cycles
    deflex.Cycles.get_suspicious_time_steps
    deflex.Cycles.print
    deflex.Cycles.details

Basic results processing
------------------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.get_all_results
    deflex.nodes2table
    deflex.solver_results2series
    deflex.fetch_dual_results
    deflex.meta_results2series
    deflex.get_time_index
    deflex.calculate_key_values


Advanced results processing
---------------------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.group_buses
    deflex.get_resource_parameters
    deflex.fetch_converter_parameters
    deflex.fetch_attributes_of_commodity_sources
    deflex.get_combined_bus_balance
    deflex.get_converter_balance


Tools for Electricity models
----------------------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.merit_order_from_scenario
    deflex.merit_order_from_results


Geometry examples for plotting
------------------------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.deflex_geo
    deflex.divide_off_and_onshore

General tools
-------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.dict2file
    deflex.use_logging

CHP allocation tools
--------------------

.. autosummary::
   :toctree: reference/
   :recursive:

    deflex.allocate_fuel_deflex
    deflex.allocate_fuel
    deflex.efficiency_method
    deflex.exergy_method
    deflex.finnish_method
    deflex.iea_method
