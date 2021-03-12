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
*Mandatory*. This sheet requires basic data about the scenario in order to be able to create it: year, number of time steps, CO2 price [€/t] and name of it.

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

*Mandatory*. As the name says, this sheet requires data from all the commodities (i.e. non volatile) the scenario uses. It is important to remark that commodities does not mean fossil fuels, althought all of them are commodities. Commodities mean the fuels with which energy generation can be controlled. For each fuel, its generation cost and emission factor must be provided.

Electricity demand series
~~~~~~~~~~~~~

+-------------+----------+----------+-----------+----------+----------+-----+
|             |   DE01   |            DE02                 | DE03     | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
|             | all      | Indsutry | Buildings | Rest     | all      | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| Time step 1 | 01all 01 | 02ind 01 | 02bui 01  | 02res 01 | 03all 01 | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| Time step 2 | 01all 02 | 02ind 02 | 02bui 02  | 02res 02 | 03all 02 | ... |
+-------------+----------+----------+-----------+----------+----------+-----+
| ...         | ...      | ...      | ...       | ...      | ...      | ... |
+-------------+----------+----------+-----------+----------+----------+-----+

*Mandatory*. This sheet requires the electrical and heating demand of the scenario. The demand must be provided in a time series form with the time step specified in the general sheet for each region in [MW]. This time series must be provided as a column form, therefore there will be as many columns as there are regions on the scenario. If the heating sector is included, then two colums of data are required for each region, one for electricity and one for heating.

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

*Mandatory*. Similarly to the CHP - heat plants sheet, here information about the power plants is required. Again, the data must be divided by region and subdivided by source. The capacity column represents the total capacitiy [MW] of all the plants operating with the same fuel in one region, while count represents the number of plants. Fuel and efficiency must be provided too. Same as with CHP - heat plants Limit_elec_pp is the maximum amount of energy that a plant can produce within the observation period. It is also possible to introduce variable costs for producing electricity (which are the costs of running the plant without fuel costs) and/or a downtime factor for each plant.

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

*Mandatory*. In this context volatility means, all sources in which power production cannot be controlled. Examples are solar, wind, hydro, geothermal (geothermal power plant, not confuse it with geothermal heating or ground source heat pumps). Same as the previous sheet, here data must be provided divided by region and subdivided by energy source. Again, the total capacity of the region and the numbers of sources (count) must be entered.

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
*Mandatory*. This sheet provides the amount of energy from volatile plants that is generated in each time step. Since this sheet is a time series, it has the same frame as the demands_series sheet. On each time step, the amount of energy generated with respect to the total capacitiy (volatile_plants) is indicated with a value between 0 and 1. In each region there are as many columns as volatile energy sources in the previous sheet.

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
| ...  | ...          | ...                | ...                | ...                  | ...                     | ...        |               |                |
+------+--------------+--------------------+--------------------+----------------------+-------------------------+------------+---------------+----------------+

*Not mandatory*. Here information about electrical storages is needed (at the moment there is only PHES but maybe it would make sense to add at least big battery storages (Huntorf 870 MWh and Jamgum 720 MWh))

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

*Mandatory*. The last set of input data considers the transmission power lines between different regions of the scenario. Here all the connections between two regions must be entered with their respective name. Each line has a maximum transmission capacity, over which no more energy can be transmitted and an efficiency, which represent the transmission losses.

Heat demand series
~~~~~~~~

Decentralized heat
~~~~~~~~~~~~~~~~~~
+--------+----------------+------------+--------+
|        |      Name      | efficiency | source |
+--------+----------------+------------+--------+
|        | N1             | E1         | S1     |
+        +----------------+------------+--------+
|        | N2             | E2         | S2     |
+ Global +----------------+------------+--------+
|        | N3              | E3         | S3     |
+        +----------------+------------+--------+
|        | ...            | ...        | ...    |
+--------+----------------+------------+--------+


*Not mandatory*. This sheet covers the part of the heating sector treated as a global. It requires all the sources with which the decentralized heat is generated along with their conversion efficiency.

Chp - heat plants
~~~~~~~~~~~~~~~~~

+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+
|          | Name | limit_heat_chp [MWh] | capacity_heat_chp [MW] | capacity_elec_chp [MW] | limit_hp [MWh] | capacity_hp [MW] | eff_hp | eff_heat_chp | eff_elec_chp | Fuel |
+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+
| Region 1 | N1   |                      |                        |                        |                |                  |        |              |              |      |
+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+
|          | N2   |                      |                        |                        |                |                  |        |              |              |      |
+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+
|          | N3   |                      |                        |                        |                |                  |        |              |              |      |
+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+
| Region 2 | N1   |                      |                        |                        |                |                  |        |              |              |      |
+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+
|          | N2   |                      |                        |                        |                |                  |        |              |              |      |
+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+
|          | N3   |                      |                        |                        |                |                  |        |              |              |      |
+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+
| ...      | ...  | ...                  | ...                    | ...                    | ...            | ...              | ...    | ...          | ...          |      |
+----------+------+----------------------+------------------------+------------------------+----------------+------------------+--------+--------------+--------------+------+

*Not mandatory*. This sheet covers the regionalized part of the heating sector. It requires CHP and heat plants (heat plant in the sense that they only produce heat) data divided by region and subdivided by fuel. The first three columns refer to CHP data: heat and electrcitiy capacities must be provided along with the maximal heat amount produced in the whole observation period, which is limit_heat_chp. This last parameter has the function of setting a maximum energy generation level for both the CHP and the heat plants (limit_hp) so that both types of plants work in parallel. Otherwise, it could be the case that during the entire period only one type of plant works, which in reality does not happen. The next three columns refer to heat plants (hp, do not confuse with heat pump) data: the already mentioned limit_hp, capacitiy and efficiency of them. Finally, heat and electricity efficiency of the CHP must be entered. It is important to emphasize that the data includes the sum of the plants in each region. This means that for example, capacity is the sum of the capacity of all plants in the region that operate with the same fuel.

Mobility demand series
~~~~~~~~~~~~~~~
*Not mandatory*. Similarly to demand_series, this sheet requires the mobility time series demand [MW] for each time step on the rows and for each energy carrier on the columns. Same as before, here the demand is treated on a global scale. 

Mobility
~~~~~~~~

+----------+----------------+------------+--------+---------------+
|          |      Name      | efficiency | source | source_region |
+----------+----------------+------------+--------+---------------+
|          | N1             | E1         | S1     | Global        |
+  Global  +----------------+------------+--------+---------------+
|          | N2             | E2         | S2     | Global        |
+----------+----------------+------------+--------+---------------+
| Region 1 | N1             | E1         | S1     | R1            |
+----------+----------------+------------+--------+---------------+
| ...      | ...            | ...        | ...    | ...           |
+----------+----------------+------------+--------+---------------+

*Not mandatory*. As said before, until now, the mobility sector has been treated as a global concept in Deflex and not a regionalized one. On this sheet each energy carrier for mobility (diesel, petrol and electricity) is attributed an efficiency, an energy source and the region where this source comes from (for now the only possible region is global, but there is the possibility of regionalizing the sector). 



Data sources
~~~~~~~~~~~~
*Not mandatory but highly recomended*. Here the type data, the source name and the url from where they were obtained can be listed.


