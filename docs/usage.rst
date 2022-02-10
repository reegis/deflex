===========
Usage guide
===========

THIS CHAPTER IS WORK IN PROGRESS...

.. contents::
    :depth: 2
    :local:
    :backlinks: top


.. _deflex_scenario:

DeflexScenario
--------------

The scenario class :py:class:`~deflex.scenario.DeflexScenario` is a central
element of deflex.

All input data is stored as a dictionary in the ``input_data`` attribute of the
``DeflexScenario`` class. The keys of the ``dictionary`` are names of the data
table and the values are ``pandas.DataFrame`` or ``pandas.Series`` with the
data.

.. image:: https://raw.githubusercontent.com/reegis/deflex/master/docs/images/deflex_scenario_class.svg


Load input data
~~~~~~~~~~~~~~~

At the moment, there are two methods to populate this attribute from files:

* read_csv() - read a directory with all needed csv files.
* read_xlsx() - read a spread sheet in the ``.xlsx``

To learn how to create a valid input data set see "REFERENCE".

.. code-block:: python

    from deflex import scenario
    sc = scenario.DeflexScenario()
    sc.read_xlsx("path/to/xlsx/file.xlsx")
    # OR
    sc.read_csv("path/to/csv/dir")


Solve the energy system
~~~~~~~~~~~~~~~~~~~~~~~

A valid input data set describes an energy system. To optimise the dispatch
of the energy system a external solver is needed. By default the CBC solver is
used but different solver are possible (see:
`solver <https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html#supported-solvers>`_).

The simplest way to solve a scenario is the ``compute()`` method.

.. code-block:: python

    sc.compute()

To use a different solver one can pass the ``solver`` parameter.

.. code-block:: python

    sc.compute(solver="glpk")


Store and restore the scenario
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``dump()`` method can be used to store the scenario. a solved scenario will
be stored with the results. The scenario is stored in a binary format and it is
not human readable.

.. code-block:: python

    sc.dump("path/to/store/results.dflx")

To restore the scenario use the ``restore_scenario`` function:

.. code-block:: python

    sc = scenario.restore_scenario("path/to/store/results.dflx")


Analyse the scenario
~~~~~~~~~~~~~~~~~~~~

Most analyses cannot be taken if the scenario is not solved. However, the merit
order can be shown only based on the input data:

.. code-block:: python

    from deflex import DeflexScenario
    from deflex import analyses
    sc = DeflexScenario()
    sc.read_xlsx("path/to/xlsx/file.xlsx")
    pp = analyses.merit_order_from_scenario(sc)
    ax = plt.figure(figsize=(15, 4)).add_subplot(1, 1, 1)
    ax.step(pp["capacity_cum"].values, pp["costs_total"].values, where="pre")
    ax.set_xlabel("Cumulative capacity [GW]")
    ax.set_ylabel("Marginal costs [EUR/MWh]")
    ax.set_ylim(0)
    ax.set_xlim(0, pp["capacity_cum"].max())
    plt.show()

With the `de02_co2-price_var-costs.xlsx` from the examples the code above will
produce the following plot:

.. image:: images/merit_order_example_plot_simple.svg

Filling the area between the line and the x-axis with colors according the fuel
of the power plant oen get the following plot:

.. image:: images/merit_order_example_plot_coloured.svg

IMPORTANT: This is just an example and not a source for the actual merit order
in Germany.


Parallel computing of scenarios
-------------------------------

For the typical work flow (creating a scenario, loading the input data,
computing the scenario and storing the results) the
:py:func:`~deflex.main.model_scenario` function can be used.

To collect all scenarios from a given directory the function
:py:func:`~deflex.main.search_input_scenarios` can be used. The function will
search for ``.xlsx`` files or paths that end on ``_csv`` and cannot
distinguish between a valid scenario and any ``.xlsx`` file or paths that
accidentally contain ``_csv``.

No matter how you collect a list of a scenario input data files the
:py:func:`~deflex.main.batch_model_scenario` function makes it easier to run
each scenario and get back the relevant information about the run. It is
possible to ignore exceptions so that the script will go on with the following
scenarios if one scenario fails.

If you have enough memory and cpu capacity on your computer/server you can
optimise your scenarios in parallel. Use the
:py:func:`~deflex.main.model_multi_scenarios` function for this task. You can
pass a list of scenario files to this function. A cpu fraction will limit the
number of processes as a fraction of the maximal available number of cpu cores.
Keep in mind that for large models the memory will be the limit not the cpu
capacity. If a memory error occurs the script will stop immediately. It is not
possible to catch a memory error. A log-file will log all failing and
successful runs.

.. include:: input_data.rst
