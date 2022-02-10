import argparse

from oemof.tools import logger

import deflex


def main():
    """
    deflex-compute [-h] [--version] [--results [RESULTS]]
    [--dump [DUMP]] [--solver [SOLVER]] path


    Computing a deflex scenario. By default the name of the result file is
    derived from the name of the input file by adding '_results but it is
    possible to define a custom path. The results will be of the same
    file format as the input scenario. Optionally a dump-file can be stored.
    If no path is given the path is derived from the path of the input
    scenario. The suffix of the dump is '.dflx'.

    **Positional Arguments**

    ::

       path      Input file or directory.

    **Optional Arguments**

    -h, --help            show this help message and exit
    --version             show program's version number and exit
    --results <RESULTS>   The name of the results file or directory or False
                          to get no result file
    --dump <DUMP>         The name of the dump file. Leave empty for the
                          default file name
    --solver <SOLVER>     Solver to use for computing (default cbc)

    """
    long_description = (
        "Computing a deflex scenario. By default the name of the result file "
        "is derived from the name of the input file by adding '_results but "
        "it is possible to define a custom path. The results will be of the "
        "same file format as the input scenario.\n\n"
        "Optionally a dump-file can be stored. If no path is given the path "
        "is derived from the path of the input scenario. The suffix of the "
        "dump is '.dflx'."
    )
    parser = argparse.ArgumentParser(
        prog="deflex-compute", description=long_description
    )
    parser.add_argument(
        "--version", action="version", version=f"deflex {deflex.__version__}"
    )
    parser.add_argument("path", type=str, help="Input file or directory.")
    parser.add_argument(
        "--results",
        dest="results",
        const=True,
        default=True,
        nargs="?",
        help=(
            "The name of the results file or directory or False to get no "
            "result file."
        ),
    )
    parser.add_argument(
        "--dump",
        dest="dump",
        const=True,
        default=None,
        nargs="?",
        help=(
            "The name of the dump file. Leave empty for the default file name."
        ),
    )
    parser.add_argument(
        "--solver",
        dest="solver",
        const="cbc",
        default="cbc",
        nargs="?",
        help="Solver to use for computing (default: cbc)",
    )

    args = parser.parse_args()

    logger.define_logging()

    deflex.scripts.model_scenario(**vars(args))


if __name__ == "__main__":
    pass
