# -*- coding: utf-8 -*-

"""
General deflex analyses.

SPDX-FileCopyrightText: Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

from collections import namedtuple

from deflex import config as cfg


def allocate_fuel_deflex(method, eta_e, eta_th):
    """
    Allocate the fuel input of chp plants to the two output flows.

    In contrast to :py:func:`allocate_fuel` default parameter
    from the config file (deflex.ini) are used.

    To change the default parameters create a deflex.ini file in $HOME/.deflex
    and add the following section:

    [chp]
    eta_c = 0.555
    eta_e_ref = 0.5
    eta_th_ref = 0.9

    This will overwrite the default values from deflex and use them as user
    default values. Lines with values that are not needed in the chosen method
    can be removed.

    The following methods are available:

    * Alternative Generation or Finnish method -> :py:func:`finnish_method`
    * Exergy method or Carnot method -> :py:func:`exergy_method`
    * IEA method -> :py:func:`iea_method`
    * Efficiency method -> :py:func:`efficiency_method`

    Parameters
    ----------
    method : str
        The method to allocate the output flows of chp plants:
        alternative_generation, carnot, efficiency, electricity, exergy,
        finnish, heat, iea
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.

    eta_th : numeric
        The efficiency of the heat output in the chp plant.

    Returns
    -------
    The fuel factors of the output flows (heat/electricity): namedtuple

    Examples
    --------
    >>> a = allocate_fuel_deflex("efficiency", eta_e=0.3, eta_th=0.5)
    >>> round(a.electricity, 2)
    2.08
    >>> round(a.heat, 2)
    0.75
    >>> a = allocate_fuel_deflex("electricity", eta_e=0.3, eta_th=0.5)
    >>> round(a.electricity, 2)
    3.33
    >>> a.heat
    0.0
    >>> a = allocate_fuel_deflex("exergy", eta_e=0.3, eta_th=0.5)
    >>> round(a.electricity, 2)
    1.73
    >>> round(a.heat, 2)
    0.96
    >>> a = allocate_fuel_deflex("finnish", eta_e=0.3, eta_th=0.5)
    >>> round(a.electricity, 2)
    1.73
    >>> round(a.heat, 2)
    0.96
    >>> a = allocate_fuel_deflex("heat", eta_e=0.3, eta_th=0.5)
    >>> a.electricity
    0.0
    >>> a.heat
    2.0
    >>> a = allocate_fuel_deflex("iea", eta_e=0.3, eta_th=0.5)
    >>> round(a.electricity, 2)
    1.25
    >>> round(a.heat, 2)
    1.25
    """
    kw = cfg.get_dict("chp")
    kw["eta_e"] = eta_e
    kw["eta_th"] = eta_th
    return allocate_fuel(method, **kw)


def allocate_fuel(method, eta_e, eta_th, **kwargs):
    r"""
    Allocate the fuel input of chp plants to the two output flows: heat and
    electricity.

    Use :py:func:`allocate_fuel_deflex` if you want to use the default values
    of the config file or if you want to define your own default values.

    The following methods are available:

     * Alternative Generation or Finnish method -> :py:func:`finnish_method`
     * Exergy method or Carnot method -> :py:func:`exergy_method`
     * IEA method -> :py:func:`iea_method`
     * Efficiency method -> :py:func:`efficiency_method`

     The sum of the allocation factors of both flows is always one:
     :math:`\alpha_{th} + \alpha_{el} = 1`

     The fuel factor is the allocation factor devided by the efficiency:

      .. math::
        f_{fuel, el}=\frac{\alpha_{el}}{\eta_{el}}\qquad
        f_{fuel, th}=\frac{\alpha_{th}}{\eta_{th}}

    :math:`f_{fuel, el/th}` :Fuel factor of the electricity/heat flow

    :math:`\alpha_{el/th}` : Allocation factor of the electricity/heat flow

    :math:`\eta_{el/th}` : Efficiency of the electricity/heat output in the
    chp plant


    Parameters
    ----------
    method : str
        The method to allocate the output flows of chp plants:
        alternative_generation, carnot, efficiency, electricity, exergy,
        finnish, heat, iea
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory for all functions.

    eta_th : numeric
        The efficiency of the heat output in the chp plant.Mandatory for all
        functions.


    Other Parameters
    ----------------
    eta_c : numeric
        The Carnot factor of the heating system. Mandatory in
        the following functions: exergy

    eta_e_ref : numeric
        The efficiency of the best power plant available on the market and
        economically viable in the year of construction of the CHP plant.
        Mandatory in the following functions: alternative_generation

    eta_th_ref : numeric
        The efficiency of the best heat plant available on the market and
        economically viable in the year of construction of the CHP plant.
        Mandatory in the following functions: alternative_generation


    Returns
    -------
    The fuel factors of the output flows (heat/electricity): namedtuple

    Examples
    --------
    >>> a = allocate_fuel("efficiency", eta_e=0.3, eta_th=0.5)
    >>> round(a.electricity, 2)
    2.08
    >>> round(a.heat, 2)
    0.75
    >>> a = allocate_fuel("electricity", eta_e=0.3, eta_th=0.5)
    >>> round(a.electricity, 2)
    3.33
    >>> a.heat
    0.0
    >>> a = allocate_fuel("exergy", eta_e=0.3, eta_th=0.5, eta_c=0.555)
    >>> round(a.electricity, 2)
    1.73
    >>> round(a.heat, 2)
    0.96
    >>> a = allocate_fuel("finnish", eta_e=0.3, eta_th=0.5, eta_e_ref=0.5,
    ...                   eta_th_ref=0.9)
    >>> round(a.electricity, 2)
    1.73
    >>> round(a.heat, 2)
    0.96
    >>> a = allocate_fuel("heat", eta_e=0.3, eta_th=0.5)
    >>> a.electricity
    0.0
    >>> a.heat
    2.0
    >>> a = allocate_fuel("iea", eta_e=0.3, eta_th=0.5)
    >>> round(a.electricity, 2)
    1.25
    >>> round(a.heat, 2)
    1.25

    """
    kwargs["eta_e"] = eta_e
    kwargs["eta_th"] = eta_th
    fuel_factors = namedtuple("fuel_factors", ["heat", "electricity"])
    name = "{0} (method: {1})".format(allocate_fuel.__name__, method)

    if method == "alternative_generation" or method == "finnish":
        mandatory = ["eta_e", "eta_th", "eta_e_ref", "eta_th_ref"]
        kwargs = _check_input(name, *mandatory, **kwargs)
        f_elec = finnish_method(**kwargs)
    elif method == "efficiency":
        mandatory = ["eta_e", "eta_th"]
        kwargs = _check_input(name, *mandatory, **kwargs)
        f_elec = efficiency_method(**kwargs)
    elif method == "exergy" or method == "carnot":
        mandatory = ["eta_e", "eta_th", "eta_c"]
        kwargs = _check_input(name, *mandatory, **kwargs)
        f_elec = exergy_method(**kwargs)
    elif method == "iea":
        mandatory = ["eta_e", "eta_th"]
        kwargs = _check_input(name, *mandatory, **kwargs)
        f_elec = iea_method(**kwargs)
    elif method == "electricity":
        f_elec = 1
    elif method == "heat":
        f_elec = 0
    else:
        msg = (
            "Method '{0}' is not implemented to calculate the allocation "
            "factor of chp product flows."
        ).format(method)
        raise NotImplementedError(msg)

    return fuel_factors(heat=(1 - f_elec) / eta_th, electricity=f_elec / eta_e)


def _check_input(name, *mandatory_parameters, **kwargs):
    """Check for mandatory parameters."""
    missing = []
    for arg in mandatory_parameters:
        if kwargs.get(arg, None) is None:
            missing.append(arg)
    if len(missing) > 0:
        msg = (
            "The following parameters are missing or None for {0}: {1}".format(
                name, ", ".join(missing)
            )
        )
        raise ValueError(msg)
    return {
        k: float(v) for k, v in kwargs.items() if k in mandatory_parameters
    }


def iea_method(eta_e, eta_th):
    r"""
    IEA Method (International Energy Association - a method to allocate the
    fuel input of chp plants to the two output flows: heat and electricity

    The allocation factor :math:`\alpha_{el}` of the electricity output is
    calculated as follows:
      .. math::
        \alpha_{el}=\frac{\eta_{el}}{\eta_{el}+\eta_{th}}

    :math:`\alpha_{el}` : Allocation factor of the electricity flow

    :math:`\eta_{el}` : Efficiency of the electricity output in the chp plant

    :math:`\eta_{th}` : Efficiency of the thermal output in the chp plant

    Parameters
    ----------
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory in the following functions: alternative_generation,
        exergy, iea, efficiency

    eta_th : numeric
        The efficiency of the heat output in the chp plant. Mandatory in
        the following functions: alternative_generation, exergy, iea,
        efficiency

    Returns
    -------
    Allocation factor for the electricity flow : numeric

    Examples
    --------
    >>> round(iea_method(0.3, 0.5), 3)
    0.375

    """
    return eta_e * 1 / (eta_e + eta_th)


def efficiency_method(eta_e, eta_th):
    r"""
    Efficiency Method - a method to allocate the fuel
    input of chp plants to the two output flows: heat and electricity

    The allocation factor :math:`\alpha_{el}` of the electricity output is
    calculated as follows:
      .. math::
        \alpha_{el}=\frac{\eta_{th}}{\eta_{el}+\eta_{th}}

    :math:`\alpha_{el}` : Allocation factor of the electricity flow

    :math:`\eta_{el}` : Efficiency of the electricity output in the chp plant

    :math:`\eta_{th}` : Efficiency of the thermal output in the chp plant

    Parameters
    ----------
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory in the following functions: alternative_generation,
        exergy, iea, efficiency

    eta_th : numeric
        The efficiency of the heat output in the chp plant. Mandatory in
        the following functions: alternative_generation, exergy, iea,
        efficiency

    Returns
    -------
    Allocation factor for the electricity flow : numeric

    Examples
    --------
    >>> round(efficiency_method(0.3, 0.5), 3)
    0.625

    """
    return eta_th / (eta_e + eta_th)


def finnish_method(eta_e, eta_th, eta_e_ref, eta_th_ref):
    r"""
    Alternative Generation or Finnish Method - a method to allocate the fuel
    input of chp plants to the two output flows: heat and electricity

    The allocation factor :math:`\alpha_{el}` of the electricity output is
    calculated as follows:
      .. math::
        \alpha_{el} = \frac{\eta_{el,ref}}{\eta_{el}} \cdot \left(
        \frac{\eta_{el}}{\eta_{el,ref}}+ \frac{\eta_{th}}{ \eta_{th,ref}}
        \right)

    :math:`\alpha_{el}` : Allocation factor of the electricity flow

    :math:`\eta_{el}` : Efficiency of the electricity output in the chp plant

    :math:`\eta_{th}` : Efficiency of the thermal output in the chp plant

    :math:`\eta_{el,ref}` : Efficiency of the reference power plant

    :math:`\eta_{th,ref}` : Efficiency of the reference heat plant


    Parameters
    ----------
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory in the following functions: alternative_generation,
        exergy, iea, efficiency

    eta_th : numeric
        The efficiency of the heat output in the chp plant. Mandatory in
        the following functions: alternative_generation, exergy, iea,
        efficiency

    eta_e_ref : numeric
        The efficiency of the best power plant available on the market and
        economically viable in the year of construction of the CHP plant.
        Mandatory in the following functions: alternative_generation

    eta_th_ref : numeric
        The efficiency of the best heat plant available on the market and
        economically viable in the year of construction of the CHP plant.
        Mandatory in the following functions: alternative_generation

    Returns
    -------
    Allocation factor for the electricity flow : numeric

    Examples
    --------
    >>> round(finnish_method(0.3, 0.5, 0.5, 0.9), 3)
    0.519

    """
    return (eta_e / eta_e_ref) / (eta_e / eta_e_ref + eta_th / eta_th_ref)


def exergy_method(eta_e, eta_th, eta_c):
    r"""
    Exergy Method or Carnot Method- a method to allocate the fuel
    input of chp plants to the two output flows: heat and electricity

      The allocation factor :math:`\alpha_{el}` of the electricity output is
    calculated as follows:
      .. math::
        \alpha_{el}=\frac{\eta_{el}}{\eta_{el}+\eta_{c}\cdot\eta_{th}}

    :math:`\alpha_{el}` : Allocation factor of the electricity flow

    :math:`\eta_{el}` : Efficiency of the electricity output in the chp plant

    :math:`\eta_{th}` : Efficiency of the thermal output in the chp plant

    :math:`\eta_{c}` : Carnot factor of the thermal energy


    Parameters
    ----------
    eta_e : numeric
        The efficiency of the electricity production in the chp plant.
        Mandatory in the following functions: alternative_generation,
        exergy, iea, efficiency

    eta_th : numeric
        The efficiency of the heat output in the chp plant. Mandatory in
        the following functions: alternative_generation, exergy, iea,
        efficiency

    eta_c : numeric
        The Carnot factor of the heating system. Mandatory in
        the following functions: exergy

    Returns
    -------
    Allocation factor for the electricity flow : numeric

    Examples
    --------
    >>> round(exergy_method(0.3, 0.5, 0.3), 3)
    0.667

    """
    return eta_e / (eta_e + eta_c * eta_th)
