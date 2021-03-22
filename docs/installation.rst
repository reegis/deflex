.. _installation_guide:

==================
Installation guide
==================

The deflex package is available on `PyPi <https://pypi.org/project/deflex/>`_.

Basic version
-------------

The basic version of deflex can read, solve and analyse a deflex scenario.
Some additional functions such as spatial operations or plots need some extra
packages (see below). To install the latest stable version use::

    pip install deflex

In case you have some old deflex scenario you can install the `old stable phd version`::

    pip install https://github.com/reegis/deflex/archive/phd.zip

To get the latest features you can install the `testing version`::

    pip install https://github.com/reegis/deflex/archive/master.zip


Installation of a solver (mandatory)
------------------------------------

To solve an energy system a linear solver has to be installed. For the
communication with the solver `Pyomo` is used. Have a look at the `Pyomo docs <https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html#supported-solvers>`_ to learn about which solvers are supported.

The default solver for deflex is the CBC solver. Go to the
`oemof.solph documentation
<https://oemof-solph.readthedocs.io/en/latest/readme.html#installing-a-solver>`_
to get help for the solver installation.


Additional requirements (optional)
----------------------------------

The basic installation can be used to compute scenarios (csv, xls, xlsx). For
some functions additional packages are needed. Some of these packages may need
OS specific packages. Please see the installation guide of each package if an
error occur.

1. To run the example with plots you need the following packages:
    * matplotlib (plotting)
    * pytz (time zones)
    * requests (download example files)

    ``pip install deflex[example]``

2. To use the maps of the polygons, transmission lines etc.:
    * pygeos (spatial operations)
    * geopandas (maps)

    ``pip install deflex[map]``

3. To develop deflex:
    * pytest
    * sphinx
    * sphinx_rtd_theme
    * pygeos
    * geopandas
    * requests

    ``pip install deflex[dev]``
