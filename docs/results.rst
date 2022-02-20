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

There are many functions...

Get common values from results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common values are emissions, costs and energy of the flows. The function
..... returns a MultiIndex
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
