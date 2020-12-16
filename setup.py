#! /usr/bin/env python

from setuptools import setup, find_packages
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


github = "@https://github.com/"
setup(
    name="deflex",
    version="v0.0.1",
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
    extras_require={
        "dev": ["pytest", "sphinx", "sphinx_rtd_theme", "requests"],
        "plot": ["pygraphviz"],
        "dummy": ["oemof"],
    },
    install_requires=[
        "oemof.solph > 0.4",
        "pandas > 1.0",
        "requests"
        "networkx > 2.0",
        "numpy >= 1.19.4",
        "rtree >= 0.9.4",
        "xlrd >= 1.2.0",
        "xlwt >= 1.3.0",
        "dill >= 0.3.3",
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
