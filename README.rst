========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |requires|
        | |coveralls| |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/deflex/badge/?style=flat
    :target: https://readthedocs.org/projects/deflex
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.org/reegis/deflex.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/reegis/deflex

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/reegis/deflex/v0.2.0b0.svg
    :alt: Commits since latest release
    :target: https://github.com/reegis/deflex/compare/v0.2.0b0...master



.. end-badges

.. image:: https://travis-ci.org/reegis/deflex.svg?branch=master
    :target: https://travis-ci.org/reegis/deflex

.. image:: https://coveralls.io/repos/github/reegis/deflex/badge.svg?branch=master
    :target: https://coveralls.io/github/reegis/deflex?branch=master

.. image:: https://img.shields.io/lgtm/grade/python/g/reegis/deflex.svg?logo=lgtm&logoWidth=18
    :target: https://lgtm.com/projects/g/reegis/deflex/context:python

.. image:: https://img.shields.io/lgtm/alerts/g/reegis/deflex.svg?logo=lgtm&logoWidth=18
    :target: https://lgtm.com/projects/g/reegis/deflex/alerts/

.. image:: https://img.shields.io/badge/automatic%20code%20style-black-blueviolet
    :target: https://black.readthedocs.io/en/stable/

.. image:: https://img.shields.io/badge/licence-MIT-blue
    :target: https://spdx.org/licenses/MIT.html

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3572594.svg
   :target: https://doi.org/10.5281/zenodo.3572594

deflex - flexible multi-regional energy system model forheat, power and mobility

* Free software: MIT license

Installation
============

::

    pip install deflex

You can also install the in-development version with::

    pip install https://github.com/reegis/deflex/archive/master.zip

Basic usage
===========

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
