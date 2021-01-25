# -*- coding: utf-8 -*-

"""
Reegis config reader.

Based on Steffen (https://github.com/steffenGit)

SPDX-FileCopyrightText: 2016-2019 Uwe Krien <krien@uni-bremen.de>

SPDX-License-Identifier: MIT
"""
__copyright__ = "Uwe Krien <krien@uni-bremen.de>"
__license__ = "MIT"

__all__ = [
    "has_option",
    "has_section",
    "get",
    "get_list",
    "get_dict",
    "get_dict_list",
    "tmp_set",
    "init",
]


import configparser as cp
import os
import sys

cfg = cp.RawConfigParser()
cfg.optionxform = str
_loaded = False
FILES = []

# Path of the package that imports this package.
try:
    IMPORTER = os.path.dirname(sys.modules["__main__"].__file__)
except AttributeError:
    IMPORTER = None


def get_ini_filenames(additional_paths=None, use_importer=True, local=True):
    """Returns a list of ini files to use."""
    paths = []
    files = []

    paths.append(os.path.join(os.path.dirname(__file__)))
    if additional_paths is not None:
        paths.extend(additional_paths)
    if IMPORTER is not None and use_importer is True:
        paths.append(IMPORTER)
    local_reegis = os.path.join(os.path.expanduser("~"), ".deflex")
    if os.path.isdir(local_reegis) and local is True:
        paths.append(local_reegis)

    for p in paths:
        if p == "":  # Empty path string must be ignored
            continue
        for f in os.listdir(p):
            if f[-4:] == ".ini":
                files.append(os.path.join(p, f))
    return files


def init(files=None, paths=None, **kwargs):
    """Read config file(s).

    Parameters
    ----------
    files : list or None
        Absolute path to config file (incl. filename)
    paths : list
        List of paths where it is searched for .ini files.
    """
    if files is None:
        files = get_ini_filenames(paths, **kwargs)
    global FILES
    FILES = files
    cfg.read(files, encoding="utf-8")
    global _loaded
    _loaded = True


def has_option(section, option):
    """Returns True if the given option exists in the given section."""
    return cfg.has_option(section, option)


def has_section(section):
    """Returns True if the given section exists."""
    return cfg.has_section(section)


def get(section, key):
    """Returns the value of a given key in a given section."""
    if not _loaded:
        init()
    try:
        return cfg.getint(section, key)
    except ValueError:
        try:
            return cfg.getfloat(section, key)
        except ValueError:
            try:
                return cfg.getboolean(section, key)
            except ValueError:
                value = cfg.get(section, key)
                if value == "None":
                    value = None
                return value


def get_list(section, parameter, sep=",", string=False):
    """Returns the values (separated by sep) of a given key in a given
    section as a list.
    """
    try:
        my_list = get(section, parameter).split(sep)
        my_list = [x.strip() for x in my_list]

    except AttributeError:
        if string is True:
            my_list = list((cfg.get(section, parameter),))
        else:
            my_list = list((get(section, parameter),))
    return my_list


def get_dict(section):
    """Returns the values of a section as dictionary"""
    if not _loaded:
        init()
    dc = {}
    for key, value in cfg.items(section):
        dc[key] = get(section, key)
    return dc


def get_dict_list(section, string=False):
    """
    Returns the values of a section as dictionary. The values will be
    interpreted as list.
    """
    if not _loaded:
        init()
    dc = {}
    for key, value in cfg.items(section):
        dc[key] = get_list(section, key, string=string)
    return dc


def tmp_set(section, key, value):
    """
    Set/Overwrite a value temporarily for the actual section.
    """
    if not _loaded:
        init()
    return cfg.set(section, key, value)


if __name__ == "__main__":
    pass
