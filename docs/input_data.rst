Input data
----------

 * The input data is the data that must be provided to Deflex for it to create a scenario. This data con be provided either as csv or as an xlsx format.
 * Since the input data is quite varied, it is divided into 12 different groups, in order to have it more organized and clear. Taking the xlsx format as example, the data is divided into 12 sheets plus a last one where the data sources are indicated.
 * It is not necessary to fill in all the input data to create a scenario. Some data is necessary, others are optional where more detailed scenarios can be created. An example of this is the heating sector, which expands the scenario covering this sector, but a scenario without it can also be created. In each group of input data it is indicated whether it is mandatory or not.
 * As a brief overview the data is divided into sources (which are subdivided into volatiles and commodities), demands (which are divided into power, heating and mobility), sotrages (electrical), and power lines.
 * The 12 different sheets are described below in the order in which the sheets are in the xlsx document.

General
~~~~~~~
*Partially mandatory*. This sheet requires general data about the scenario such as the year of the data, the time step of it, name and the number of regions in which the scenario is divided. The first three are mandatory data. There is also the possibility to set a CO2 price. Here must be indicated if the heating sector is considered or not (if so, then the heating data becomes mandatory). The cooperplate mode means that all capacities and efficiencies in the power lines are infinite and 1 respectively (again if this option is dissabled, then capacities and efficiencies must be provided in the transmission lines sheet). Variable costs and downtime factor are with respect to the power plants sheet, and data must be provided in case these are activated.

Commodity sources
~~~~~~~~~~~~~~~~~
*Mandatory*. As the name says, this sheet requires data from all the commodities (i.e. non volatile) the scenario uses. It is important to remark that commodities does not mean fossil fuels, althought all of them are commodities. Commodities mean the fuels with which energy generation can be controlled. For each fuel, its generation cost [€/MWh] and emission factor [t/MWh] must be provided.

Demand series
~~~~~~~~~~~~~
*Mandatory at least the electrical part*. This sheet requires the electrical and heating demand of the scenario. The demand must be provided in a time series form with the time step specified in the general sheet for each region in [MW]. This time series must be provided as a column form, therefore there will be as many columns as there are regions on the scenario. If the heating sector is included, then two colums of data are required for each region, one for electricity and one for heating.

Mobility
~~~~~~~~
*Not mandatory*. Until now, the mobility sector has been treated as a global concept in Deflex and not a regionalized one. The reason behind this is that the energy source of mobility is oil, which does not have transmission lines, nor does it need power plants. Thus, the demand is independent of the place in which it occurs, making it easier to deal with it on a global scale. On this sheet each energy carrier for mobility (diesel, petrol and electricity) is attributed an efficiency and an energy source. 

Mobility series
~~~~~~~~~~~~~~~
*Not mandatory*. Similarly to demand_series, this sheet requires the mobility time series demand [MW] for each time step on the rows and for each energy carrier on the columns. Same as before, here the demand is treated on a global scale. 

Decentralized heat
~~~~~~~~~~~~~~~~~~

.. ToDo: I thought I understood this section but now I think I don't understand it)

*Not mandatory*. This sheet requires all the sources with which heat is generated along with their conversion efficiency. Is this the 'commodities sources' of the heating sector?

Chp - heat plants
~~~~~~~~~~~~~~~~~
*Not mandatory*. This sheet requires CHP and heat plants (heat plant in the sense that they only produce heat) data divided by region and subdivided by fuel, which should be specified in the rows of the sheet. The first three columns refer to CHP data: heat and electrcitiy capacities [MW] must be provided along with the maximal heat amount produced in the whole observation period [MWh], which is limit_heat_chp. This last parameter has the function of setting a maximum energy generation level for both the CHP and the heat plants (limit_hp) so that both types of plants work in parallel. Otherwise, it could be the case that during the entire period only one type of plant works, which in reality does not happen. The next three columns refer to heat plants (hp, do not confuse with heat pump) data: the already mentioned limit_hp, capacitiy and efficiency of them. Finally, heat and electricity efficiency of the CHP must be entered.


Power plants
~~~~~~~~~~~~
*Mandatory*. Similarly to the CHP - heat plants sheet, here information about the power plants is required. Again, the data must be divided by region and subdivided by source. The capacity column represents the total capacitiy [MW] of all the plants operating with the same fuel in one region, while count represents the number of plants. Fuel and efficiency must be provided too. Same as with CHP - heat plants Limit_elec_pp is the maximum amount of energy that a plant can produce within the observation period. It is also possible to introduce variable costs for producing electricity (which are the costs of running the plant without fuel costs) and/or a downtime factor for each plant.

Volatiles plants
~~~~~~~~~~~~~~~~
*Mandatory*. In this context volatility means, all sources in which energy production cannot be controlled. Examples are solar, wind, hydro, geothermal (geothermal power plant, not confuse it with geothermal heating or ground source heat pumps). Same as the previous sheet, here data must be provided divided by region and subdivided by energy source. Again, the total capacity of the region [MW] and the numbers of sources (count) must be entered.

Volatiles series
~~~~~~~~~~~~~~~~
*Mandatory*. This sheet provides the amount of energy from volatile plants that is generated in each time step. Since this sheet is a time series, it has the same frame as the demands_series sheet: information on each column and time steps on each row. The columns are divided into each region, and then subdivided into each energy source. On each time step, the amount of energy generated with respect to the total capacitiy (volatile_plants) is indicated with a value between 0 and 1.

Storages
~~~~~~~~
*Not mandatory*. Here information about electrical storages is needed (at the moment there is only PHES but maybe it would make sense to add at least big battery storages (Huntorf 870 MWh and Jamgum 720 MWh))

Power lines
~~~~~~~~~~~
*Mandatory*. The last set of input data considers the transmission power lines between different regions of the scenario. Here all the connections between two regions must be entered with their respective name. Each line has a maximum transmission capacity, over which no more energy can be transmitted and an efficiency, which represent the transmission losses.

Data sources
~~~~~~~~~~~~
*Not mandatory but highly recomended*. Here the type data, the source name and the url from where they were obtained can be listed.
