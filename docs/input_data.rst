Input data
----------

The input data is stored in the
:py:attr:`~deflex.scenario.Scenario.input_data` attribute of the
:py:class:`~deflex.scenario.DeflexScenario`
class (s. :ref:`deflex_scenario`). It is a dictionary with the name of the
data set as key and the data table itself as value (pandas.DataFrame or
pandas.Series).

The input data is divided into four main topics: High-level-inputs, electricity
sector, heating sector (optional) and mobility sector (optional).

.. contents::
    :depth: 1
    :local:
    :backlinks: top


Overview
~~~~~~~~

A Deflex scenario can be divided into regions. Each region must have an
identifier number and be named after it as ``DEXX``, where ``XX`` is the
number. For refering the Deflex scenario as a whole (i.e. the sum of all
regions) use ``DE`` only.

At the current state the distribution of fossil fuels is neglected. Therefore,
in order to keep the computing time low it is recommended to define them
supra-regional using ``DE`` without a number. It is still possible to define
them regional for example to add a specific limit for each region.

In most cases it is also sufficient to model the fossil part of the mobility
and the decentralised heating sector supra-regional. It is assumed that a
gas boiler or a filling station is always supplied with enough fuel, so that
the only the annual values affect the model. This does not apply to electrical
heating systems or cars.

.. note::
    NaN-values are not allowed in any table. Some columns are optional and can
    be left out, but if a column is present there have to be values in every
    row. Neutral values can be ``0``, ``1`` or ``inf``.

High-level-input (mandatory)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. contents::
    :depth: 1
    :local:
    :backlinks: top

General
+++++++
This sheet requires basic data about the scenario in order to be able to
create it: year, number of time steps, CO2 price [€/t] and name of it.

Info
++++
On this sheet, additional information that characterizes the scenario can be
added. The idea behind Info is that the user can filter stored scenarios using
the :py:func:`~deflex.postprocessing.search_results` function.

You can create any key-value pair which is suitable for you group of scenarios.

e.g. key: ``scenario_type`` value: ``foo`` / ``bar`` / ``foobar``

Afterwards you can search for all scenarios where the ``scenario_type`` is
``foo`` using:

.. code-block:: python

    search_results(path=my_path, scenario_type=["foo"])

or with other keys and multiple values:

.. code-block:: python

    search_results(path=my_path, scenario_type=["foo", "bar"], my_key["v1"])

The second code line will return only files with (``foo`` or ``bar``) and
``v1``.

Commodity sources
+++++++++++++++++

In most spread sheet software it is possible to connect cells to increase
readability. These lines are interpreted correctly. In csv files the values
have to appear in every cell.

+------+-----------+---------------+------------------+--------------------+
|      | fuel type | costs [€/MWh] | emission [t/MWh] | annual limit [MWh] |
+------+-----------+---------------+------------------+--------------------+
|      | F1        | C1            | E1               | AL1                |
+  DE  +-----------+---------------+------------------+--------------------+
|      | F2        | C2            | E2               | AL2                |
+------+-----------+---------------+------------------+--------------------+
| DE01 | F1        | C1            | E1               | AL3                |
+------+-----------+---------------+------------------+--------------------+
| DE02 | F2        | C2            | E2               | AL4                |
+------+-----------+---------------+------------------+--------------------+
| ...  | ...       | ...           | ...              | ...                |
+------+-----------+---------------+------------------+--------------------+

As the name says, this sheet requires data from all the commodities (i.e. non
volatile) the scenario uses. Generation cost, emission factor and the annual
maximum generation limit (if there is one, otherwise just write *inf*) must be
provided. If the ``annual limit`` is ``inf`` in any line the column can be left
out.
The data can be provided either global under DE, regional under DEXX or as a
combination of both, where some commodities are global and some are regional.
Regionalised commodities are specially useful for commodities with an annual
limit, for example bioenergy. It is important to remark that commodities does
not mean fossil fuels, although all of them are commodities.

??Commodities mean the fuels with which energy generation can be controlled??

Data sources
++++++++++++
*Highly recomended*. Here the type data, the source name and the url from where
they were obtained can be listed. It is a free format and additional columns
can be added. This table helps to make your scenario as transparent as
possible.

Electricity sector (mandatory)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. contents::
    :depth: 1
    :local:
    :backlinks: top

Electricity demand series
+++++++++++++++++++++++++

``key:`` 'electricity demand series',
``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

This sheet requires the electricity demand of the scenario as a time series in
``[MW]``. One summarised demand series for each region is enough, but it is
possible to distinguish between different types. This will not have any effect
on the model results.

+-------------+----------+----------+-----------+----------+----------+-----+
|             |   DE01   |            DE02                 | DE03     | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
|             | all      | Indsutry | Buildings | Rest     | all      | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| Time step 1 |          |          |           |          |          | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| Time step 2 |          |          |           |          |          | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| ...         | ...      | ...      | ...       | ...      | ...      | ... |
+-------------+----------+----------+-----------+----------+----------+-----+

**INDEX**

time step: ``int``
    Number of time step. Has to be uniform in all series tables.

**COLUMNS**

unit: ``[MW]``

level 0: ``str``
    DEXX (e.g. DE01, DE20)

level 1: ``str``
    Specification of the series e.g. "all" for an overall series.


Power plants
++++++++++++

``key:`` 'power plants', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

The power plants will feed in the electricity bus of the region the are
located.

+-------+------+----------+------+------------+--------------------------+---------------+-----------------+---------------+
|       |      | capacity | fuel | efficiency | annual electricity limit | variable_cost | downtime_factor | source_region |
+-------+------+----------+------+------------+--------------------------+---------------+-----------------+---------------+
|       | N1   |          |      |            |                          |               |                 |               |
+       +------+----------+------+------------+--------------------------+---------------+-----------------+---------------+
| DE01  | N2   |          |      |            |                          |               |                 |               |
+       +------+----------+------+------------+--------------------------+---------------+-----------------+---------------+
|       | N3   |          |      |            |                          |               |                 |               |
+-------+------+----------+------+------------+--------------------------+---------------+-----------------+---------------+
| DE02  | N2   |          |      |            |                          |               |                 |               |
+       +------+----------+------+------------+--------------------------+---------------+-----------------+---------------+
|       | N3   |          |      |            |                          |               |                 |               |
+-------+------+----------+------+------------+--------------------------+---------------+-----------------+---------------+
| ...   | ...  | ...      | ...  | ...        | ...                      | ...           | ...             | ...           |
+-------+------+----------+------+------------+--------------------------+---------------+-----------------+---------------+

**INDEX**

level 0: ``str``
    DEXX (e.g. DE01, DE20)
level 1: ``str``
    arbitrary

**COLUMNS**

capacity: ``float``
    The installed capacity of the power plant [MW].

fuel: ``str``
    The used fuel of the power plant. The fuel name as to be equal to the fuel
    type of the commodity sources.

efficiency: ``float``
    The average overall efficiency of the power plant.

annual limit: ``float``
    The absolute maximum limit of produced electricity within the whole
    modeling period [MWh].

variable_costs: ``float``
    The variable costs per produced electricity unit [€/MWh].

downtime_factor: ``float``
    The time fraction of the modeling period in which the power plant cannot
    produce electricity. The installed capacity will be reduced by this factor.
    ``capacity * (1 - downtime_factor)``

source_region
    The source region of the fuel source. Typically this is the region of the
    index or ``DE`` if it is a global commodity source. The combination of fuel
    and region must exist in the commodity sources table.

Here information about the power plants is required. The data must be divided by region and subdivided by fuel. The capacity column represents the total capacitiy of all the plants operating with the same fuel in one region, while count represents the number of plants. Fuel and efficiency must be provided too along with the maximal amount of energy produced in the whole year, which is called *limit*. This parameter has the function of setting a maximum energy generation level for each power plant so that all plants work in parallel. Otherwise, it could be the case that during the entire period only one plant works, which in reality does not happen. It is also possible to introduce variable costs for each plant and/or a downtime factor for each plant, but these last three are not mandatory. Finally source_region indicates from which region does the fuel come. In case the fuel is regionally classified in *commodities*, usually the source_region will be that region. In case the fuel is globally classified in *commodities*, then the source_region will be DE.

Volatiles plants
++++++++++++++++

+------+------+---------------+
|      | Name | capacity [MW] |
+------+------+---------------+
| DE01 | N1   |               |
+------+------+---------------+
|      | N2   |               |
+------+------+---------------+
| DE02 | N1   |               |
+------+------+---------------+
| DE03 | N1   |               |
+------+------+---------------+
|      | N3   |               |
+------+------+---------------+
| ...  | ...  | ...           |
+------+------+---------------+

In this context volatility means, all sources in which power production cannot be controlled. Examples are solar, wind, hydro, geothermal (geothermal power plant, not confuse it with geothermal heating nor ground source heat pumps). Same as the previous sheet, here data must be provided divided by region and subdivided by energy source. Again, the capacity of the region is the sum of the capacitiy of all plants operating with the same energy source.

Volatiles series
++++++++++++++++

+-------------+------+-----+------+------+-----+-----+
|             |     DE01   | DE02 |    DE03    | ... |
+-------------+------+-----+------+------+-----+-----+
|             | N1   | N2  | N1   | N1   | N3  | ... |
+-------------+------+-----+------+------+-----+-----+
| Time step 1 |      |     |      |      |     | ... |
+-------------+------+-----+------+------+-----+-----+
| Time step 2 |      |     |      |      |     | ... |
+-------------+------+-----+------+------+-----+-----+
| ...         | ...  | ... | ...  | ...  | ... | ... |
+-------------+------+-----+------+------+-----+-----+

This sheet provides the amount of energy from volatile plants that is generated in each time step. On each time step, the amount of energy generated with respect to the total capacitiy (volatile_plants) is indicated with a value between 0 and 1. In each region there are as many columns as volatile energy sources in the previous sheet.

Electricity storages
++++++++++++++++++++

+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
|      | Storage type | max capacity [MWh] | Energy inflow [MW] | charge capacity [MW] | discharge capacity [MW] | charge eff | discharge eff | self-discharge |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
| DE01 | S1           |                    |                    |                      |                         |            |               |                |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
|      | S2           |                    |                    |                      |                         |            |               |                |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
| DE02 | S2           |                    |                    |                      |                         |            |               |                |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
| ...  | ...          | ...                | ...                | ...                  | ...                     | ...        | ...           | ...            |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+

Here information about electricity storages is needed. Since this is part of the power sector, all storages must be registered regionally. As there are different storage technologies (pumped hydro, batteries, compressed air, etc), the information can be entered in a general way where each name corresponds to a different storage type.

Power lines
+++++++++++

+-----------+---------------+------------+
|           | capacity [MW] | efficiency |
+-----------+---------------+------------+
| DE01-DE02 |               |            |
+-----------+---------------+------------+
| DE01-DE03 |               |            |
+-----------+---------------+------------+
| DE02-DE03 |               |            |
+-----------+---------------+------------+
| ...       | ...           | ...        |
+-----------+---------------+------------+

The last input data regarding the power sector, considers the transmission power lines between different regions of the scenario. Here all the connections between two regions must be entered with their respective name which indicates the regions that are connecting. Each line has a maximum transmission capacity, over which no more energy can be transmitted and an efficiency, which represent the transmission losses.

Heating sector (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. contents::
    :depth: 1
    :local:
    :backlinks: top

Heat demand series
++++++++++++++++++

+-------------+------------------+-----+------------------+-----+-----+-----+-----+-----+-----+
|             |       DE01             | DE02                         |     |       DE        |
+-------------+------------------+-----+------------------+-----+-----+-----+-----+-----+-----+
|             | district heating | N1  | district heating | N1  | N2  | ... | N3  | N4  | N5  |
+-------------+------------------+-----+------------------+-----+-----+-----+-----+-----+-----+
| Time step 1 |                  |     |                  |     |     |     |     |     |     |
+-------------+------------------+-----+------------------+-----+-----+-----+-----+-----+-----+
| Time step 2 |                  |     |                  |     |     |     |     |     |     |
+-------------+------------------+-----+------------------+-----+-----+-----+-----+-----+-----+
| ...         | ...              | ... | ...              | ... | ... | ... | ... | ... | ... |
+-------------+------------------+-----+------------------+-----+-----+-----+-----+-----+-----+

*Optional*

Continuing with the heating sector, this sheet requires the heat demand which, as mentioned at the beginning, can be entered regionally under DEXX or globally under DE. The only type of demand that must be entered regionally is the district heating. Again, as a recommendation, coal, gas, or oil demands should be treated as global since Deflex does not have infrastructure that allows a regionalization of these commodities. The demand must be entered under the same principle as *electrcitiy demand series*, using the number of time steps specified in *general*.

Decentralized heat
++++++++++++++++++

+------+------+------------+--------+---------------+
|      | Name | efficiency | source | source region |
+------+------+------------+--------+---------------+
| DE01 | N1   |            |        | DE01          |
+------+------+------------+--------+---------------+
| DE02 | N1   |            |        | DE02          |
|      +------+------------+--------+---------------+
|      | N2   |            |        | DE02          |
+------+------+------------+--------+---------------+
|      | ...  |            |        | ...           |
+------+------+------------+--------+---------------+
| DE   | N3   |            |        | DE            |
|      +------+------------+--------+---------------+
|      | N4   |            |        | DE            |
|      +------+------------+--------+---------------+
|      | N5   |            |        | DE            |
+------+------+------------+--------+---------------+

This sheet covers all the heating technologies that are used to generate decentralized heat. It is important not to confuse decentralized sources with global / regional. A decenttralized source can be treated regional (bioenergy, heat pump) or global (natural gas, oil, coal). In other words, here must be everything that is mentioned in *heat demands* except the district heating which is covered in the next sheet.

Chp - heat plants
+++++++++++++++++

+------+------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
|      | Name | limit heat chp | capacity heat chp | capacity elec chp | limit hp | capacity hp | efficiency hp | efficiency heat chp | efficiency elec chp | fuel | source region |
+------+------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
| DE01 | N1   |                |                   |                   |          |             |               |                     |                     |      | DE01          |
|      +------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
|      | N3   |                |                   |                   |          |             |               |                     |                     |      | DE            |
|      +------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
|      | N4   |                |                   |                   |          |             |               |                     |                     |      | DE            |
+------+------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
| DE02 | N1   |                |                   |                   |          |             |               |                     |                     |      | DE02          |
|      +------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
|      | N2   |                |                   |                   |          |             |               |                     |                     |      | DE02          |
|      +------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
|      | N3   |                |                   |                   |          |             |               |                     |                     |      | DE            |
|      +------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
|      | N4   |                |                   |                   |          |             |               |                     |                     |      | DE            |
|      +------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
|      | N5   |                |                   |                   |          |             |               |                     |                     |      | DE            |
+------+------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
| ...  | ...  | ...            | ...               | ...               | ...      | ...         | ...           | ...                 | ...                 | ...  | ...           |
+------+------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+


As said before, this sheet covers the district heating part of the heating sector. Under the same principle as *power plants* in the power sector, it requires CHP and heat plants (heat plant in the sense that they only produce heat) data divided by region and subdivided by fuel (Note that the fuel does not have to come explicitly from the DEXX region, it can also come from the global DE). As in the power plants sheet, there is the *limit_hp* (and *limit_heat_chp*, *limit_elec_chp* for CHP) value, which makes the plants to run in parallel.

Mobility sector (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. contents::
    :depth: 1
    :local:
    :backlinks: top

Mobility demand series
++++++++++++++++++++++

+-------------+-------------+-------------+-----+-----+
|             |     DE01    | DE02        | ... | DE  |
+-------------+-------------+-------------+-----+-----+
|             | electricity | electricity |     | N1  |
+-------------+-------------+-------------+-----+-----+
| Time step 1 |             |             |     |     |
+-------------+-------------+-------------+-----+-----+
| Time step 2 |             |             |     |     |
+-------------+-------------+-------------+-----+-----+
| ...         | ...         | ...         | ... | ... |
+-------------+-------------+-------------+-----+-----+

Finalizing with the mobility sector, this sheet requires the mobility time series demand [MW] for each time step. Same as the heating sector, here the demand can be entered regionally or globally. However, the reocmendation is to treat the demand globally, unless there is electricity demand (which by the way, can be removed from this sector and placed in the power sector) which must be treated regionally.

Mobility
++++++++

+------+-------------+------------+--------------------+---------------+
|      |     name    | efficiency | source             | source region |
+------+-------------+------------+--------------------+---------------+
| DE01 | electricity |            | electricity        | DE01          |
+------+-------------+------------+--------------------+---------------+
| DE02 | electricity |            | electricity        | DE02          |
+------+-------------+------------+--------------------+---------------+
| ...  |             |            |                    |               |
+------+-------------+------------+--------------------+---------------+
| DE   | N1          |            | oil/biofuel/H2/etc | DE            |
+------+-------------+------------+--------------------+---------------+

This sheet is the analog to *decentralized heat* but in the mobility sector. Since there is no analogue to heat plants in mobility, this sheet is the only one that covers the technologies of this sector. The previous means that everything that is defined in mobility demands has to be here.
