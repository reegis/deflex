============
Installation
============

The following line will install the basic version. Some functions depend on further packages, see below to install additional requirements::

    pip install deflex

To run older scenarios you can install the old stable phd version::

    pip install https://github.com/reegis/deflex/archive/phd.zip

To get the latest version install the master branch::

    pip install https://github.com/reegis/deflex/archive/master.zip

Additional requirements
-----------------------

The basic installation can be used to compute scenarios (csv, xls, xlsx). For
some functions additional packages are needed.

1. To run the example with all plots you need the following packages:
    * pygeos (spatial operations)
    * geopandas (maps)
    * descartes (plot maps with matplotlib)
    * lmfit (linear fit)
    * matplotlib (plotting)
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
