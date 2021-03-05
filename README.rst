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

.. |commits-since| image:: https://img.shields.io/github/commits-since/reegis/deflex/v0.2.0.svg
    :alt: Commits since latest release
    :target: https://github.com/reegis/deflex/compare/v0.2.0...master

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

The following README gives you a brief overview about deflex. Read the full
`documentation <https://deflex.readthedocs.io/en/latest/>`_ for all
information.

* Multi sectoral energy system of Germany/Europe
* Dispatch optimisation
* Start with basic scenarios
* Highly configurable and adaptable

Installation
------------

To run `deflex` you have to install the Python package and a solver:

* deflex is available on `PyPi <https://pypi.org/project/deflex/>`_ and can be
  installed using ``pip install deflex``.
* an LP-solver is needed such as CBC (default), GLPK, Gurobi*, Cplex*
* for some extra functions additional packages and are needed

\* Proprietary solver


Use example
-----------

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


Documentation
-------------

The `full documentation of deflex <https://deflex.readthedocs.io/en/latest/>`_
is available on readthedocs.

Go to the `download page <http://readthedocs.org/projects/deflex/downloads/>`_
to download different versions and formats (pdf, html, epub) of the
documentation.

License
-------

Copyright (c) 2019 Uwe Krien

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
