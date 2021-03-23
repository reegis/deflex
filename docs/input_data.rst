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

``key:`` 'commodity sources', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

In most spread sheet software it is possible to connect cells to increase
readability. These lines are interpreted correctly. In csv files the values
have to appear in every cell.

This sheet requires data fromm all the commodities used in the scenario. The data can be provided either supra-regional under DE, regional under DEXX or as a combination of both, where some commodities are global and some are regional. Regionalised commodities are specially useful for commodities with an annual limit, for example bioenergy. It is important to remark that commodities does not mean fossil fuels, although all of them are commodities.

+------+-----------+---------------+------------------+--------------------+
|      |           | costs         | emission         | annual limit       |
+------+-----------+---------------+------------------+--------------------+
|      | F1        |               |                  |                    |
+  DE  +-----------+---------------+------------------+--------------------+
|      | F2        |               |                  |                    |
+------+-----------+---------------+------------------+--------------------+
| DE01 | F1        |               |                  |                    |
+------+-----------+---------------+------------------+--------------------+
| DE02 | F2        |               |                  |                    |
+------+-----------+---------------+------------------+--------------------+
| ...  | ...       | ...           | ...              | ...                |
+------+-----------+---------------+------------------+--------------------+

**INDEX**

level 0: ``str``
    Region (e.g. DE01, DE02 or DE).
level 1: ``str``
    Fuel type.

**COLUMNS**

costs [€/MWh]: ``float``
    The fuel production cost.

emission [t/MWh]: ``float``
    The fuel emission factor in.
    
annual limit [MWh]: ``float``
    The annual maximum energy generation (if there is one, otherwise just write *inf*). If the ``annual limit`` is ``inf`` in any line the column can be left out.


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

This sheet requires the electricity demand of the scenario as a time series. One summarised demand series for each region is enough, but it is possible to distinguish between different types. This will not have any effect on the model results.

+-------------+----------+----------+-----------+----------+----------+-----+
|             |   DE01   |            DE02                 | DE03     | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
|             | all      | indsutry | buildings | rest     | all      | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| Time step 1 |          |          |           |          |          | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| Time step 2 |          |          |           |          |          | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| ...         | ...      | ...      | ...       | ...      | ...      | ... |
+-------------+----------+----------+-----------+----------+----------+-----+

**INDEX**

time step: ``int``
    Number of time step. Must be uniform in all series tables.

**COLUMNS**

unit: ``[MW]``

level 0: ``str``
    Region (e.g. DE01, DE02).

level 1: ``str``
    Specification of the series e.g. "all" for an overall series.


Power plants
++++++++++++

``key:`` 'power plants', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

The power plants will feed in the electricity bus of the region the are located. The data must be divided by region and subdivided by fuel. It is important indicate the logic behind *annual electricity limit*. This parameter has the function of setting a maximum energy generation level for each power plant so that all plants work in parallel. Otherwise, it could be the case that during the entire period only one plant works, which in reality does not happen.

+-------+------+----------+------+------+------------+--------------------------+---------------+-----------------+---------------+
|       |      | capacity |count | fuel | efficiency | annual electricity limit | variable_cost | downtime_factor | source_region |
+-------+------+----------+------+------+------------+--------------------------+---------------+-----------------+---------------+
|       | N1   |          |      |      |            |                          |               |                 |               |
+       +------+----------+------+------+------------+--------------------------+---------------+-----------------+---------------+
| DE01  | N2   |          |      |      |            |                          |               |                 |               |
+       +------+----------+------+------+------------+--------------------------+---------------+-----------------+---------------+
|       | N3   |          |      |      |            |                          |               |                 |               |
+-------+------+----------+------+------+------------+--------------------------+---------------+-----------------+---------------+
| DE02  | N2   |          |      |      |            |                          |               |                 |               |
+       +------+----------+------+------+------------+--------------------------+---------------+-----------------+---------------+
|       | N3   |          |      |      |            |                          |               |                 |               |
+-------+------+----------+------+------+------------+--------------------------+---------------+-----------------+---------------+
| ...   | ...  | ...      |...   |...   | ...        | ...                      | ...           | ...             | ...           |
+-------+------+----------+------+------+------------+--------------------------+---------------+-----------------+---------------+

**INDEX**

level 0: ``str``
    Region (e.g. DE01, DE02).
level 1: ``str``
    Name, arbitrary.

**COLUMNS**

capacity [MW]: ``float``
    The installed capacity of all power plants operating with the same fuel in the region.
    
count: ``int``
    The numer of power plants operating with the same fuel in the region.

fuel: ``str``
    The fuel used in the power plant. The fuel name must be equal to the fuel
    type of the commodity sources.

efficiency: ``float``
    The average overall efficiency of the power plant.

annual limit [MWh]: ``float``
    The absolute maximum limit of produced electricity within the whole
    modeling period in.

variable_costs [€/MWh]: ``float``
    The variable costs per produced electricity unit.

downtime_factor: ``float``
    The time fraction of the modeling period in which the power plant cannot
    produce electricity. The installed capacity will be reduced by this factor.
    ``capacity * (1 - downtime_factor)``

source_region
    The source region of the fuel source. Typically this is the region of the
    index or ``DE`` if it is a global commodity source. The combination of fuel
    and region must exist in the commodity sources table.


Volatiles plants
++++++++++++++++

``key:`` 'volatile plants', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

Examples of volatile plants are solar, wind, hydro, geothermal (geothermal power plant, not confuse it with geothermal heating nor ground source heat pumps). Same as the previous sheet, here data must be provided divided by region and subdivided by energy source. Again, the capacity of the region is the sum of the capacitiy of all plants operating with the same energy source.

+------+------+---------------+
|      |      | capacity      |
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

**INDEX**

level 0: ``str``
    Region (e.g. DE01, DE02).
level 1: ``str``
    Name, arbitrary.
    
**COLUMNS**

capacity [MW]: ``float``
    The installed capacity of all power plants operating in the region.


Volatile series
++++++++++++++++

``key:`` 'volatile series', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

This sheet provides the amount of energy from volatile plants that is generated in each time step. On each time step, the amount of energy generated with respect to the total capacitiy (*volatile_plants*) is indicated with a value between 0 and 1. In each region there are as many columns as volatile energy sources in the previous sheet.

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

**INDEX**

time step: ``int``
    Number of time step. Must be uniform in all series tables.

**COLUMNS**

unit: ``[0,1]``

level 0: ``str``
    Region (e.g. DE01, DE02).

level 1: ``str``
    Name of the energy source specified in the previous sheet.


Electricity storages
++++++++++++++++++++

``key:`` 'electricity storages', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

Here information about electricity storages is needed. As there are different storage technologies (pumped hydro, batteries, compressed air, etc) the information can be entered in a general way where each row corresponds to a different storage type for each region.

+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
|      |              |     capacity       | energy inflow      | charge capacity      | discharge capacity      | charge eff | discharge eff | self-discharge |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
| DE01 | S1           |                    |                    |                      |                         |            |               |                |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
|      | S2           |                    |                    |                      |                         |            |               |                |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
| DE02 | S2           |                    |                    |                      |                         |            |               |                |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+
| ...  | ...          | ...                | ...                | ...                  | ...                     | ...        | ...           | ...            |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+

**INDEX**

level 0: ``str``
    Region (e.g. DE01, DE02).
level 1: ``str``
    Name, arbitrary.
    
**COLUMNS**

capacity [MWh]: ``float``
    The maximum installed capacity of all storages with the same technology in the region.

energy inflow: ``float``
    ?
    
charge capacity [MW]: ``float``
    (Maximum?) rate at which the storage charges.
    
discharge capacity [MW]: ``float``
    (Maximum?) rate at which the storage discharges.

charge eff: ``float``
    Charging efficiency of the storage.
    
discharge eff: ``float``
    Discharging efficiency of the storage.
    
Self-discharge [MW]: ``float``
    Rate at which the storage self-discharges.
    
Power lines
+++++++++++

``key:`` 'power lines', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

The last input data regarding the power sector, considers the transmission power lines between different regions of the scenario. Here all the connections between two regions must be entered with their respective name which indicates the regions that are connecting.

+-----------+---------------+------------+
|           | capacity      | efficiency |
+-----------+---------------+------------+
| DE01-DE02 |               |            |
+-----------+---------------+------------+
| DE01-DE03 |               |            |
+-----------+---------------+------------+
| DE02-DE03 |               |            |
+-----------+---------------+------------+
| ...       | ...           | ...        |
+-----------+---------------+------------+

**INDEX**

Name: ``str``
    Name, arbitrary.


**COLUMNS**

capacity [MW]: ``float``
    The maximum transmission capacity.
    
efficiency:b``float``
    The transmission efficiency of the power line.

Heating sector (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. contents::
    :depth: 1
    :local:
    :backlinks: top

Heat demand series
++++++++++++++++++

``key:`` 'heat demand series', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

This sheet requires the heat demand which, as mentioned at the beginning, can be entered regionally under DEXX or supra-regional under DE. The only type of demand that must be entered regionally is the district heating. As recommendation, coal, gas, or oil demands should be treated supra-regional. This sheet has the same structure as *electricity demand series*.

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

**INDEX**

time step: ``int``
    Number of time step. Must be uniform in all series tables.

**COLUMNS**

unit: ``[MW]``

level 0: ``str``
    Region (e.g. DE01, DE02 or DE).

level 1: ``str``
    Specification of the series e.g. "district heating" for each region or "coal", "gas" for DE.


Decentralized heat
++++++++++++++++++

``key:`` 'decentralised heat', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

This sheet covers all heating technologies that are used to generate decentralized heat. A decentralized source can be treated regional (bioenergy, heat pump) or supra-regional (natural gas, oil, coal). All sources that are mentioned in *heat demands* must be here except district heating which is covered in the next sheet.

+------+------+------------+--------+---------------+
|      |      | efficiency | source | source region |
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

**INDEX**

level 0: ``str``
    Region (e.g. DE01, DE02 or DE).
level 1: ``str``
    Name, arbitrary.

**COLUMNS**

efficiency: ``float``
    The efficiency of the heating technology.
    
source: ``str``
    The source that the heating technology uses. Examples are coal, oil for commodities, but it could also be electrcitiy in case of a heat pump.

source region: ``str``
    The region where the source comes from.


Chp - heat plants
+++++++++++++++++

``key:`` 'chp-heat plants', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

This sheet covers the district heating part of the heating sector. Under the same frame as *power plants* in the power sector, it requires CHP and heat plants (heat plant in the sense that they only produce heat) data divided by region and subdivided by fuel. As in the power plants sheet, there is a *limit_hp* (and *limit_heat_chp*, *limit_elec_chp* for CHP) value, which allows the plants to run in parallel.

+------+------+----------------+-------------------+-------------------+----------+-------------+---------------+---------------------+---------------------+------+---------------+
|      |      | limit heat chp | capacity heat chp | capacity elec chp | limit hp | capacity hp | efficiency hp | efficiency heat chp | efficiency elec chp | fuel | source region |
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

**INDEX**

level 0: ``str``
    Region (e.g. DE01, DE02).
level 1: ``str``
    Name, arbitrary.

**COLUMNS**

limit heat chp [MWh]: ``float``
    The absolute maximum limit of heat produced by chp within the whole modeling period.
    
capacity heat chp [MW]: ``float``
    The installed heat capacity of all chp plants operating with the same fuel in the region.
    
capacity elect chp [MW]: ``float``
    The installed electricity capacity of all chp plants operating with the same fuel in the region.

limit hp [MWh]: ``float``
    The absolute maximum limit of heat produced by the heat plant within the whole modeling period.
    
capacity hp [MW]: ``float``
    The installed heat capacity of all heat plants operating with the same fuel in the region.
    
efficiency hp: ``float``
    The average overall efficiency of the heat plant.
    
efficiency heat chp: ``float``
    The average overall heat efficiency of the chp.
    
efficiency elect chp: ``float``
    The average overall electricity efficiency of the chp.

fuel: ``str``
    The fuel used in the plant. The fuel name must be equal to the fuel
    type of the commodity sources.

source_region
    The source region of the fuel source. Typically this is the region of the
    index or ``DE`` if it is a global commodity source.

Mobility sector (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. contents::
    :depth: 1
    :local:
    :backlinks: top

Mobility demand series
++++++++++++++++++++++
``key:`` 'mobility series', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

This sheet requires the mobility time series demand for each time step. Same as the heating sector, here the demand can be entered regionally or supra-regional. However, the reocmendation is to treat the demand supra-regional, unless there is electricity demand (which by the way, can be removed from this sector and placed in the power sector) which must be treated regionally.

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

**INDEX**

time step: ``int``
    Number of time step. Must be uniform in all series tables.

**COLUMNS**

unit: ``[MW]``

level 0: ``str``
    Region (e.g. DE01, DE02 or DE).

level 1: ``str``
    Specification of the series e.g. "electricity" for each region or "diesel", "petrol" for DE.



Mobility
++++++++
``key:`` 'mobility', ``value:`` `pandas.DataFrame() <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_

This sheet is the analog to *decentralized heat* but in the mobility sector. Since there is no analogue to heat plants in mobility, this sheet is the only one that covers the technologies of this sector. The previous means that everything that is defined in mobility demands has to be here.

+------+-------------+------------+--------------------+---------------+
|      |             | efficiency | source             | source region |
+------+-------------+------------+--------------------+---------------+
| DE01 | electricity |            | electricity        | DE01          |
+------+-------------+------------+--------------------+---------------+
| DE02 | electricity |            | electricity        | DE02          |
+------+-------------+------------+--------------------+---------------+
| ...  |             |            |                    |               |
+------+-------------+------------+--------------------+---------------+
| DE   | N1          |            | oil/biofuel/H2/etc.| DE            |
+------+-------------+------------+--------------------+---------------+

**INDEX**

level 0: ``str``
    Region (e.g. DE01, DE02 or DE).
level 1: ``str``
    Name, arbitrary.

**COLUMNS**

efficiency: ``float``
    The efficiency of the mobility technology.
    
source: ``str``
    The source that the technology uses.

source region: ``str``
    The region where the source comes from.

