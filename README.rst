.. start-badges

| |workflow_pytests| |workflow_checks| |coveralls| |docs| |packaging|
| |lgt_general| |lgt_alerts| |codacy| |requires|

\

| |version| |wheel| |supported-versions| |supported-implementations|
| |commits-since| |licence| |code_Style| |zenodo|


.. |docs| image:: https://readthedocs.org/projects/deflex/badge/?style=flat
    :target: https://readthedocs.org/projects/deflex
    :alt: Documentation Status

.. |workflow_pytests| image:: https://github.com/reegis/deflex/workflows/tox%20pytests/badge.svg?branch=master
    :target: https://github.com/reegis/deflex/actions?query=workflow%3A%22tox+pytests%22

.. |workflow_checks| image:: https://github.com/reegis/deflex/workflows/tox%20checks/badge.svg?branch=master
    :target: https://github.com/reegis/deflex/actions?query=workflow%3A%22tox+checks%22

.. |packaging| image:: https://github.com/reegis/deflex/workflows/packaging/badge.svg?branch=master
    :target: https://github.com/reegis/deflex/actions?query=workflow%3Apackaging

.. |requires| image:: https://requires.io/github/reegis/deflex/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/reegis/deflex/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/github/reegis/deflex/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://coveralls.io/github/reegis/deflex?branch=master

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/reegis/deflex/v0.3.0.svg
    :alt: Commits since latest release
    :target: https://github.com/reegis/deflex/compare/v0.3.0...master

.. |lgt_general| image:: https://img.shields.io/lgtm/grade/python/g/reegis/deflex.svg?logo=lgtm&logoWidth=18
    :target: https://lgtm.com/projects/g/reegis/deflex/context:python

.. |lgt_alerts| image:: https://img.shields.io/lgtm/alerts/g/reegis/deflex.svg?logo=lgtm&logoWidth=18
    :target: https://lgtm.com/projects/g/reegis/deflex/alerts/

.. |code_style| image:: https://img.shields.io/badge/automatic%20code%20style-black-blueviolet
    :target: https://black.readthedocs.io/en/stable/

.. |codacy| image:: https://api.codacy.com/project/badge/Grade/b91ed03ffa8e407ab3e69a10c5115efa
   :target: https://app.codacy.com/gh/reegis/deflex?utm_source=github.com&utm_medium=referral&utm_content=reegis/deflex&utm_campaign=Badge_Grade

.. |licence| image:: https://img.shields.io/badge/licence-MIT-blue
    :target: https://spdx.org/licenses/MIT.html

.. |zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3572594.svg
   :target: https://doi.org/10.5281/zenodo.3572594


------------------------------------------------

.. end-badges

\

.. image:: https://raw.githubusercontent.com/reegis/deflex/master/docs/images/logo_deflex_big.svg
    :target: https://github.com/reegis/deflex
    :width: 600pt

=================================================================================
deflex - flexible multi-regional energy system model for heat, power and mobility
=================================================================================

++++++ multi sectoral energy system of Germany/Europe ++++++ dispatch
optimisation ++++++ highly configurable and adaptable ++++++ multiple analyses
functions +++++

The following README gives you a brief overview about deflex. Read the full
`documentation <https://deflex.readthedocs.io/en/latest/>`_ for all
information.

.. contents::
    :depth: 1
    :local:
    :backlinks: top

Installation
------------

To run `deflex` you have to install the Python package and a solver:

* deflex is available on `PyPi <https://pypi.org/project/deflex/>`_ and can be
  installed using ``pip install deflex``.
* an LP-solver is needed such as CBC (default), GLPK, Gurobi*, Cplex*
* for some extra functions additional packages and are needed

\* Proprietary solver


Examples
--------

1. Run ``pip install deflex[example]`` to get all dependencies.
2. Create a local directory (e.g. /home/user/deflex_examples).
3. Browse the `examples <https://osf.io/9krgp/files/>`_ for deflex v0.4.x or
   download all examples as `zip file <https://files.de-1.osf.io/v1/resources/9krgp/providers/osfstorage/620b67ed11da1c0120f56939/?zip=>`_ and copy/extract them to your local directory.
4. Read the comments of each example, execute it and modify it to your needs.
   Do not forget to set a local path in the examples if needed.
5. In parallel you should read the ``usage guide`` of the documentation to get
   the full picture.

Improve deflex
--------------

We are warmly welcoming all who want to contribute to the deflex library. This
includes the following actions:

* Write bug reports or comments
* Improve the documentation (including typos, grammar)
* Add features improve the code (open an issue first)


Citing deflex
-------------

Go to the `Zenodo page of deflex <https://doi.org/10.5281/zenodo.3572594>`_ to find the DOI of your version. To cite all deflex versions use:

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3572594.svg
   :target: https://doi.org/10.5281/zenodo.3572594

Gallery
-------

The following figures will give you a brief impression about deflex.

.. image:: https://raw.githubusercontent.com/reegis/deflex/master/docs/images/model_regions.svg

**Figure 1:** Use one of the include regions sets or create your own one. You
can also include other European countries.

-------------------------------------------------------------------------------

.. image:: https://raw.githubusercontent.com/reegis/deflex/master/docs/images/spreadsheet_examples.png
  :width: 950pt

**Figure 2:** The input data can be organised in spreadsheets or csv files.

-------------------------------------------------------------------------------

.. image:: https://raw.githubusercontent.com/reegis/deflex/master/docs/images/mcp.svg

**Figure 3:** The resulting system costs of deflex have been compared with the
day-ahead prices from the Entso-e downloaded from `Open Power System Data
<https://open-power-system-data.org/>`_. The plot shows three different periods
of the year.

-------------------------------------------------------------------------------

.. image:: https://raw.githubusercontent.com/reegis/deflex/master/docs/images/emissions.svg

**Figure 4:** It is also possible to get a time series of the average emissions. Furthermore,
it shows the emissions of the most expensive power plant which would be
replaced by an additional feed-in.

-------------------------------------------------------------------------------

.. image:: https://raw.githubusercontent.com/reegis/deflex/master/docs/images/transmission.svg

**Figure 5:** The following plot shows fraction of the time on which the utilisation of the
power lines between the regions is more than 90% of its maximum capacity:

Documentation
-------------

The `full documentation of deflex <https://deflex.readthedocs.io/en/latest/>`_
is available on readthedocs.

Go to the `download page <http://readthedocs.org/projects/deflex/downloads/>`_
to download different versions and formats (pdf, html, epub) of the
documentation.

License
-------

Copyright (c) 2016-2021 Uwe Krien

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
