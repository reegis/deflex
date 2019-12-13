.. deflex documentation master file

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

Introduction
=============

The deflex library provides a simple heat and power model of Germany. Some
basic scenarios with all data are included.

Documentation
~~~~~~~~~~~~~

The `documentation of deflex <https://deflex.readthedocs.io/en/latest/>`_ is powered by readthedocs.

Go to the `download page <http://readthedocs.org/projects/deflex/downloads/>`_ to download different versions and formats (pdf, html, epub) of the documentation.


Installation
============

On a Linux Debian system you can use the following command to solve all
requirements beforehand.

.. code-block::

    sudo apt-get install python3-dev proj-bin libproj-dev libgeos-dev python3-tk libspatialindex-dev virtualenv

If you have a working Python 3 environment, use pypi to install the latest deflex version:

::

    pip install deflex

The deflex library is designed for Python 3 and tested on Python >= 3.6. We highly recommend to use virtual environments.
Please see the `installation page <http://oemof.readthedocs.io/en/stable/installation_and_setup.html>`_ of the oemof documentation for complete instructions on how to install python and a virtual environment on your operating system.


Basic usage
===========

Create a basic scenario as xls-file or collection of csv-files using the following lines.

.. NOTE::

    The first run of the following lines may take some hours, because all
    needed data will be downloaded, processed and stored locally. On the next
    run the stored files will be used.

    Use the logger to see the state of the script.

.. code-block:: python

    import logging
    from deflex import basic_scenario
    logging.getLogger()
    logger.setLevel(logging.INFO)
    basic_scenario.create_basic_scenario(2014, 'de21')

Use the following lines to optimise an existing basic scenario:

.. code-block:: python

    import logging
    from deflex import main
    logging.getLogger()
    logger.setLevel(logging.INFO)
    main.main(2014, 'de21')

To optimise a user scenario one has to pass the path to the scenario file(s).

.. code-block:: python

    import logging
    from deflex import main
    logging.getLogger()
    logger.setLevel(logging.INFO)
    main.model_scenario(xls_file='/my/path/to/scenario.xls',
                        name='my_scenario', rmap='deXX', year=2025)

It is faster to use csv-files!

.. code-block:: python

    import logging
    from deflex import main
    logging.getLogger()
    logger.setLevel(logging.INFO)
    main.model_scenario(csv_path='/my/path/to/my_csv_files',
                        name='my_scenario', rmap='deXX', year=2025)





Contributing
==============

We are warmly welcoming all who want to contribute to the deflex library.


Citing deflex
========================

Go to the `Zenodo page of deflex <https://doi.org/10.5281/zenodo.3572594>`_ to find the DOI of your version. To cite all deflex versions use:

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3572594.svg
   :target: https://doi.org/10.5281/zenodo.3572594

License
============

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