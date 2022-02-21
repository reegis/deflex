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

Export all results
++++++++++++++++++

To export the results from all variables into the ``xlsx`` or ``csv`` format,
the results can be stored in a collection of pandas.DataFrame. This collection
can be stored into a file. An example for this workflow can be found in the
documentation of the function:

 * :py:func:`~deflex.get_all_results` -- get all results as dictionary
 * :py:func:`~deflex.dict2file` -- store the dictionary into a file

Get common values from results
++++++++++++++++++++++++++++++

...work in progress.
