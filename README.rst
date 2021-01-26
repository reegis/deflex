========
deflex
========

.. image:: https://api.codacy.com/project/badge/Grade/b91ed03ffa8e407ab3e69a10c5115efa
   :alt: Codacy Badge
   :target: https://app.codacy.com/gh/reegis/deflex?utm_source=github.com&utm_medium=referral&utm_content=reegis/deflex&utm_campaign=Badge_Grade

**flexible multi-regional energy system model for heat, power and mobility**


.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |requires| |lgt_general|
        | |lgt_alerts| |coveralls| |codecov|
    * - package
      - | |version| |wheel| |supported-versions|
        | |supported-implementations| |commits-since| |licence| |code_Style| |zenodo|
.. |docs| image:: https://readthedocs.org/projects/deflex/badge/?style=flat
    :target: https://readthedocs.org/projects/deflex
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.com/reegis/deflex.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.com/reegis/deflex

.. |requires| image:: https://requires.io/github/reegis/deflex/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/reegis/deflex/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/reegis/deflex/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/reegis/deflex

.. |codecov| image:: https://codecov.io/gh/reegis/deflex/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/reegis/deflex

.. |version| image:: https://img.shields.io/pypi/v/deflex.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/deflex

.. |wheel| image:: https://img.shields.io/pypi/wheel/deflex.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/deflex

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/deflex.svg
    :alt: Supported versions
    :target: https://pypi.org/project/deflex

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/deflex.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/deflex

.. |commits-since| image:: https://img.shields.io/github/commits-since/reegis/deflex/v0.2.0.svg
    :alt: Commits since latest release
    :target: https://github.com/reegis/deflex/compare/v0.2.0...master

.. |lgt_general| image:: https://img.shields.io/lgtm/grade/python/g/reegis/deflex.svg?logo=lgtm&logoWidth=18
    :target: https://lgtm.com/projects/g/reegis/deflex/context:python

.. |lgt_alerts| image:: https://img.shields.io/lgtm/alerts/g/reegis/deflex.svg?logo=lgtm&logoWidth=18
    :target: https://lgtm.com/projects/g/reegis/deflex/alerts/

.. |code_style| image:: https://img.shields.io/badge/automatic%20code%20style-black-blueviolet
    :target: https://black.readthedocs.io/en/stable/

.. |licence| image:: https://img.shields.io/badge/licence-MIT-blue
    :target: https://spdx.org/licenses/MIT.html

.. |zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3572594.svg
   :target: https://doi.org/10.5281/zenodo.3572594


Installation
============

The following line will install the basic version. Some functions depend on further packages, see below to install additional requirements::

    pip install deflex

To run older scenarios you can install the old stable phd version::

    pip install https://github.com/reegis/deflex/archive/phd.zip


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


Basic usage
===========

.. code-block:: python

    scenario = "/path/to/my/scenario.xls"
    main.model_scenario(scenario)


Use example
===========

1. Run ``pip install deflex[example]``
2. Create a local directory (e.g. /home/user/deflex_examples).
3. Download the
   `example <https://raw.githubusercontent.com/reegis/deflex/master/examples/examples.py>`_
   to this new directory.
4. Now execute the example file. The script will download some example
   scenarios with results and show some exemplary plots.
5. A directory "deflex_examples" will be created in you home directory. Use
   ``print(os.path.expanduser("~"))`` to find out where your home directory is
   located. If you want to change it replace the base path in the example:

.. code-block:: diff

    - BASEPATH = os.path.join(os.path.expanduser("~"), "deflex_examples")
    + BASEPATH = "/your/favoured/path/"

Documentation
=============


https://deflex.readthedocs.io/

The `documentation of deflex <https://deflex.readthedocs.io/en/latest/>`_ is powered by readthedocs.

Go to the `download page <http://readthedocs.org/projects/deflex/downloads/>`_ to download different versions and formats (pdf, html, epub) of the documentation.



Contributing
==============

We are warmly welcoming all who want to contribute to the deflex library.


Citing deflex
========================

Go to the `Zenodo page of deflex <https://doi.org/10.5281/zenodo.3572594>`_ to find the DOI of your version. To cite all deflex versions use:

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3572594.svg
   :target: https://doi.org/10.5281/zenodo.3572594

Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
