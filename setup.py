#! /usr/bin/env python

from setuptools import setup, find_packages
import os
import deflex


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="deflex",
    version=deflex.__version__,
    author="Uwe Krien",
    author_email="krien@uni-bremen.de",
    description=(
        "A multi-sectoral model of Germany with flexible multi regions."
    ),
    namespace_package=["deflex"],
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    packages=find_packages(),
    package_dir={"deflex": "deflex"},
    url="https://github.com/reegis/deflex",
    license="MIT",
    extras_require={"dev": ["nose", "sphinx", "sphinx_rtd_theme", "requests"]},
    install_requires=[
        "oemof >= 0.3.0",
        "pandas >= 0.17.0",
        "reegis > v0.1.1",
        "demandlib",
        "workalendar",
        "networkx",
        "numpy",
        "rtree",
        "xlrd",
        "xlwt",
        "dill",
        "matplotlib",
    ],
    package_data={
        "deflex": [
            os.path.join("data", "static", "*.csv"),
            os.path.join("data", "static", "*.txt"),
            os.path.join("data", "geometries", "*.csv"),
            os.path.join("data", "geometries", "*.geojson"),
            "*.ini",
        ]
    },
)
