import argparse
import logging

import pandas as pd

import deflex
from deflex import use_logging


def main():
    """
    deflex-compute [-h] [--version] [--results [RESULTS]]
    [--dump [DUMP]] [--solver [SOLVER]] path


    Computing a deflex scenario. By default the name of the result file is
    derived from the name of the input file by adding '_results but it is
    possible to define a custom path. The results will be of the same
    file format as the input scenario. Optionally a dump-file can be stored.
    If no path is given the path is derived from the path of the input
    scenario. The suffix of the dump is '.dflx'. The dump can be processed
    using `deflex_result`.

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

    use_logging()

    deflex.scripts.model_scenario(**vars(args))


def result():
    long_description = (
        "Processing the results from a computed deflex dump file. The "
        "following functions are available:\n\n"
        "* calculate_key_values\n"
        "* dsafd\n"
        "* asdf\n"
        "\nSee the documentation for more details."
    )
    parser = argparse.ArgumentParser(
        prog="deflex-results",
        description=long_description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"deflex {deflex.__version__}"
    )
    parser.add_argument(
        "function", type=str, help="Post-processing function to use."
    )
    parser.add_argument("in_path", type=str, help="Input file or directory.")
    parser.add_argument("out_path", type=str, help="Output file or directory.")
    parser.add_argument(
        "--filetype",
        dest="filetype",
        const=None,
        default=None,
        nargs="?",
        help=(
            "The file_type of the output file xlsx or csv. By default the "
            "suffix of the output file is used, if possible."
        ),
    )
    args = parser.parse_args()

    use_logging()

    if args.function == "calculate_key_values":
        results = deflex.restore_results(args.in_path)
        df = deflex.calculate_key_values(results)
    elif args.function == "something":
        df = pd.DataFrame()
    else:
        msg = (
            f"The function {args.function}() is not available with "
            f"'deflex_results'."
        )
        raise NotImplementedError(msg)

    if args.filetype is None:
        args.filetype = args.out_path.split(".")[-1]

    if args.filetype == "xlsx":
        df.to_excel(args.out_path)
    elif args.filetype == "csv":
        logging.info(f"Results stored in {args.out_path}")
        df.to_csv(args.out_path)
    else:
        raise ValueError(f"File type '{args.filetype}' not valid.")


if __name__ == "__main__":
    pass
