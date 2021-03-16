Input data
----------

 * The input data is the data that must be provided to Deflex for it to create a scenario. This data con be provided either as csv or as an xlsx format.
 * Since the input data is quite varied, it is divided into 15 different groups, in order to have it more organized and clear. Taking the xlsx format as example, the data is divided into 15 sheets.
 * It is not necessary to fill in all the input data to create a scenario, there is mandatory and optional data, where more detailed scenarios can be created. For exmaple, the power sector is mandatory while heating and mobility sectors are optional. In each group of input data it is indicated whether it is mandatory or not.
 * As a brief overview the data is divided into sources (which are subdivided into volatiles and commodities), demands (which are divided into power, heating and mobility), electrcity sotrages, and power lines.
 * A Deflex scenario can be divided into regions. Each region must have an identifier number and be named after it as DEXX, where XX is the number. For refering the Deflex scenario as a whole (i.e. the sum of all regions) use DE only.
 * It is important to mention how the three sectors are treated in Deflex. From one side the power sector is treated regionally, which means, each region must contain their sources (power plants and volatiles), electricity storages and electricity demands. Besides that, there must be power lines connecting different regions. Heat and mobility sectors can be treated regionally, globally or as a combination of both. Here a way to treat these two sectors is proposed, but in the end it is up to each user. It is recommended to treat the mobility sector globally, which means, that the demand of the scenario is treated as one single input under DE. The reason behind this is that the energy source of mobility is mainly oil, which does not have an infractrusture in Deflex as the power sector does (power plants, transmission lines). Thus, for Deflex the mobility demand is independent of the place in which it occurs, making it easier to deal with it on a global scale. However, for future scenarios, where electricity plays an important role in mobility, it is necessary to regionalize at least the electricity demand within mobility. For the heating sector, it is advisable to treat one part as global and the other as regional. The reason for this is due to the nature of this sector, which on the one hand has decentralized sources (gas biolers in each house for example) and on the other hand has heat plants that supply heat through district heating to multiple points. Because of that, the decentralized sources can be linked to a single global demand, as the mobilite sector is, and the heat plants can be linked to regional demands, as the power sector is. Logically to do this, separate input data must be given on how much demand is covered by heat plants/district heating and how much demand is covered with decentralized technologies.
 * The 15 different sheets are described below in the order in which the sheets are in the xlsx document. Each of them has a table at the beginning where the framework of the sheet is indicated. After general, info and commodities, the power sector data is required, followed by the heating sector data and finally the mobility sector data.

General
~~~~~~~
*Mandatory*.

This sheet requires basic data about the scenario in order to be able to create it: year, number of time steps, CO2 price [€/t] and name of it.

Info
~~~~~~~
*Optional*

On this sheet, additional information that characterizes the scenario can be added. The idea behind Info is that the user can filter different scenarios under different characteristics. Therefore, more keys can be written depending on the needs of each user. Examples are the number of regions, the costs source used, or if the copperplate mode is used or not (cooperplate mode means that all capacities and efficiencies in the power lines are infinite and 1 respectively)


Commodity sources
~~~~~~~~~~~~~~~~~

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

*Mandatory*.

As the name says, this sheet requires data from all the commodities (i.e. non volatile) the scenario uses. Generation cost, emission factor and the annual maximum generation limit (if there is one, otherwise just write *inf*) must be provided. The data can be provided either global under DE, regional under DEXX or as a combination of both, where some commodities are global and some are regional. Regionalized commodities are specially useful for commodities with an annual limit, for example bioenergy. It is important to remark that commodities does not mean fossil fuels, althought all of them are commodities. Commodities mean the fuels with which energy generation can be controlled.


Electricity demand series
~~~~~~~~~~~~~

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

*Mandatory*.

This sheet requires the electricity demand of the scenario. The demand must be provided in a time series form, with the time step specified *general*, for each region in [MW] as the table shows. Electrcity demand can be entered as a whole for each region as DE01 shows or it can be divided into different sectors as DE 02 shows. 

Power plants
~~~~~~~~~~~~

+------+------+---------------+-------+------+------------+-------------+-----------------------+-----------------+---------------+
|      | Name | capacity [MW] | count | fuel | efficiency | limit [MWh] | variable_cost [€/MWh] | downtime_factor | source_region |
+------+------+---------------+-------+------+------------+-------------+-----------------------+-----------------+---------------+
| DE01 | N1   |               |       |      |            |             |                       |                 |               |
+------+------+---------------+-------+------+------------+-------------+-----------------------+-----------------+---------------+
|      | N2   |               |       |      |            |             |                       |                 |               |
+------+------+---------------+-------+------+------------+-------------+-----------------------+-----------------+---------------+
|      | N3   |               |       |      |            |             |                       |                 |               |
+------+------+---------------+-------+------+------------+-------------+-----------------------+-----------------+---------------+
| DE02 | N2   |               |       |      |            |             |                       |                 |               |
+------+------+---------------+-------+------+------------+-------------+-----------------------+-----------------+---------------+
|      | N3   |               |       |      |            |             |                       |                 |               |
+------+------+---------------+-------+------+------------+-------------+-----------------------+-----------------+---------------+
| ...  | ...  | ...           | ...   | ...  | ...        | ...         | ...                   | ...             | ...           |
+------+------+---------------+-------+------+------------+-------------+-----------------------+-----------------+---------------+

*Mandatory*

Here information about the power plants is required. The data must be divided by region and subdivided by fuel. The capacity column represents the total capacitiy of all the plants operating with the same fuel in one region, while count represents the number of plants. Fuel and efficiency must be provided too along with the maximal amount of energy produced in the whole year, which is called *limit*. This parameter has the function of setting a maximum energy generation level for each power plant so that all plants work in parallel. Otherwise, it could be the case that during the entire period only one plant works, which in reality does not happen. It is also possible to introduce variable costs for each plant and/or a downtime factor for each plant, but these last three are not mandatory. Finally source_region indicates from which region does the fuel come. In case the fuel is regionally classified in *commodities*, usually the source_region will be that region. In case the fuel is globally classified in *commodities*, then the source_region will be DE.

Volatiles plants
~~~~~~~~~~~~~~~~

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

*Mandatory*.

In this context volatility means, all sources in which power production cannot be controlled. Examples are solar, wind, hydro, geothermal (geothermal power plant, not confuse it with geothermal heating nor ground source heat pumps). Same as the previous sheet, here data must be provided divided by region and subdivided by energy source. Again, the capacity of the region is the sum of the capacitiy of all plants operating with the same energy source.

Volatiles series
~~~~~~~~~~~~~~~~

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

*Mandatory*.

This sheet provides the amount of energy from volatile plants that is generated in each time step. On each time step, the amount of energy generated with respect to the total capacitiy (volatile_plants) is indicated with a value between 0 and 1. In each region there are as many columns as volatile energy sources in the previous sheet.

Electricity storages
~~~~~~~~

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

*Not mandatory*.

Here information about electricity storages is needed. Since this is part of the power sector, all storages must be registered regionally. As there are different storage technologies (pumped hydro, batteries, compressed air, etc), the information can be entered in a general way where each name corresponds to a different storage type.

Power lines
~~~~~~~~~~~

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

*Mandatory*

The last input data regarding the power sector, considers the transmission power lines between different regions of the scenario. Here all the connections between two regions must be entered with their respective name which indicates the regions that are connecting. Each line has a maximum transmission capacity, over which no more energy can be transmitted and an efficiency, which represent the transmission losses.

Heat demand series
~~~~~~~~

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
~~~~~~~~~~~~~~~~~~
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


*Optional*

This sheet covers all the heating technologies that are used to generate decentralized heat. It is important not to confuse decentralized sources with global / regional. A decenttralized source can be treated regional (bioenergy, heat pump) or global (natural gas, oil, coal). In other words, here must be everything that is mentioned in *heat demands* except the district heating which is covered in the next sheet.

Chp - heat plants
~~~~~~~~~~~~~~~~~

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

*Optional*

As said before, this sheet covers the district heating part of the heating sector. Under the same principle as *power plants* in the power sector, it requires CHP and heat plants (heat plant in the sense that they only produce heat) data divided by region and subdivided by fuel (Note that the fuel does not have to come explicitly from the DEXX region, it can also come from the global DE). As in the power plants sheet, there is the *limit_hp* (and *limit_heat_chp*, *limit_elec_chp* for CHP) value, which makes the plants to run in parallel.



Mobility demand series
~~~~~~~~~~~~~~~

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

*Optional*

Finalizing with the mobility sector, this sheet requires the mobility time series demand [MW] for each time step. Same as the heating sector, here the demand can be entered regionally or globally. However, the reocmendation is to treat the demand globally, unless there is electricity demand (which by the way, can be removed from this sector and placed in the power sector) which must be treated regionally.

Mobility
~~~~~~~~

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

*Optional*

This sheet is the analog to *decentralized heat* but in the mobility sector. Since there is no analogue to heat plants in mobility, this sheet is the only one that covers the technologies of this sector. The previous means that everything that is defined in mobility demands has to be here.


Data sources
~~~~~~~~~~~~
*Not mandatory but highly recomended*. Here the type data, the source name and the url from where they were obtained can be listed.


