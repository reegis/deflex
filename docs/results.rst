Results
-------

All results are stored in the
:py:attr:`~deflex.scenario.scenario.Scenario.results` attribute of the
:py:class:`~deflex.scenario.scenario.Scenario` class. It is a dictionary with
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

Store results
~~~~~~~~~~~~~

The results can be dumped using `pickle` or stored as a collection of data
tables. A dump will preserve the full structure including the Python objects,
while the tables only include the result of the variables.

Store as tables
+++++++++++++++

The results will be written into a dictionary of pandas.DataFrame and can be
stored as an xlsx-file or as a collection of csv-files. This is typically used
to process the results in a spreadsheet tool (Excel, LibreOffice,...) or in
another language like R. At the moment it is not possible to restore the
results from such a spreadsheet or csv-collection and use the postprocessing
tools of deflex afterwards. Dump the results to be able to restore them.

Dump the results
++++++++++++++++

As a dump contains all information about the objects it is very sensitive for
version changes. You may not be able to open a dump with a different version of
Python, deflex or oemof.solph. Therefore, the information about the used
versions is stored in a nested dump. You will always be able to unpack the
first layer to get these information. These structure makes it possible to
filter files by the meta information stored in the first layer.

These meta information can be stored in the 'info' table of the scenario
definition. The values in this table are for information only and do not have
any effect on the scenario. So arbitrary key-value pairs can be defined.
For examples if there are scenarios for different countries a key `country`
could be defined with the values `France`, `Germany` etc. Afterwards it is
possible to filter the results by this keyword.

To find results file on your hard disc you can use the
:py:func:`~deflex.scenario_tools.scenario_io.search_dumped_scenarios` function. This function
provides a filter parameter which can be used to filter your own meta tags. The
:py:attr:`~deflex.scenario.Scenario.meta` attribute of the
:py:class:`~deflex.DeflexScenario` class can store these meta tags in a
dictionary with the tag-name as key and the value.

.. code-block:: python

    meta = {
        "regions": 17,
        "heat": True,
        "tag": "value",
        }

The filter for these tags will look as follows. The values in the filter have
to be strings regardless of the original type:

.. code-block:: python

    search_results(path=TEST_PATH, regions=["17", "21"], heat=["true"])

There is always an ``AND`` connection between all filters and an ``OR``
connectionso within a list. So The filter above will only return results with
17 ``or`` 21 regions ``and`` with the heat-tag set to true. The returning list
can be used as an input parameter to load the results and get a list of results
dictionaries.

.. code-block:: python

    my_result_files = search_results(path=my_path)
    my_results = restore_results(my_result_files)

If a single file name is passed to the
:py:func:`~deflex.postprocessing.restore_results` function a single result will
be returned, otherwise a list.

Get common values from results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common values are emissions, costs and energy of the flows. The function
:py:func:`~deflex.analyses.get_flow_results` returns a MultiIndex
DataFrame with the costs, emissions and the energy of all flows. The values
are absolute and specific. The specific values are divided by the power so
that the specific power gives you the status (on/off).

At the moment this works only with hourly time steps. The units are as flows:

 * absolute emissions -> tons
 * specific emissions -> tons/MWh
 * absolute costs -> EUR
 * specific costs -> EUR/MWh
 * absolute energy -> MWh
 * specific energy -> --

The resulting table of the function can be stored as a ``.csv`` or ``.xlsx``
file. The input is one results dictionary:

.. code-block:: python

   from deflex import postprocessing as pp
   from deflex.analyses import get_flow_results

   my_result_files = pp.search_results(path=my_path)
   my_results = pp.restore_results(my_result_files[0])
   flow_results = get_flow_results(my_result)
   flow_results.to_csv("/my/path/flow_results.csv")

The resulting table can be used to calculate other key values in your own
functions but you can also use some ready-made functions. Follow the link to
get information about each function:

 * :py:func:`~deflex.analyses.calculate_market_clearing_price`
 * :py:func:`~deflex.analyses.calculate_emissions_most_expensive_pp`

We are planing to add more calculations in the future. Please let us know if
you have any ideas and open an `issue <https://github.com/reegis/deflex>`_.
All these functions above are integrated in the
:py:func:`~deflex.analyses.get_key_values_from_results` function. This function
takes a list of results and returns one MultiIndex DataFrame. It contains all
the return values from the functions above for each scenario. The first column
level contains the value names and the second level the names of the scenario.
The value names are:

    * mcp
    * emissions_most_expensive_pp

The name of the scenario is taken from the ``name`` key of the meta attribute.
If this key is not available you have to set it for each scenario, otherwise
the function will fail. The resulting table can be stored as a ``.csv`` or
``.xlsx`` file.

.. code-block:: python

   from deflex import postprocessing as pp
   from deflex.analyses import get_flow_results

   my_result_files = pp.search_results(path=my_path)
   my_results = pp.restore_results(my_result_files)
   kv = get_key_values_from_results(my_results)
   kv.to_csv("/my/path/key_values.csv")

If you have many scenarios, the resulting table may become quite big.
Therefore, you can skip values you do not need in your resulting table. If you
do need only the emissions and not the market clearing price you can exclude
the ``mcp``.

.. code-block:: python

    kv = get_key_values_from_results(my_results, mcp=False)
