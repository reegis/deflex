=====
Usage
=====

THIS CHAPTER IS WORK IN PROGRESS...

.. contents::
    :depth: 2
    :local:
    :backlinks: top

DeflexScenario
++++++++++++++

The scenario class DeflexScenario is a central element of a deflexletzte

In deflex all input data is stored as a dictionary of pandas ``DataFrame`` in
the ``table_collection`` attribute of the ``DeflexScenario`` class.

[TODO: add reference to DeflexScenario]

At the moment, there are two methods to populate this attribute from a file:

* read_csv() - to read a directory with all needed csv files.
* read_excel() - to read a spread sheet.

[TODO: only xlsx is possible, so xlsx is better than excel because it works for
Libreoffice, too.]

...

