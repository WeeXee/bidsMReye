#!/usr/bin/env python
"""Main script."""
import argparse
import logging
import os
import sys
from glob import glob
from pathlib import Path

from rich.logging import RichHandler
from rich.traceback import install

from bidsmreye.combine import combine
from bidsmreye.generalize import generalize
from bidsmreye.prepare_data import prepare_data
from bidsmreye.utils import config

# let rich print the traceback
install(show_locals=True)

# log format
FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def main(argv=sys.argv) -> None:
    """Execute the main script."""
    parser = argparse.ArgumentParser(
        description="BIDS app using deepMReye to decode eye motion for fMRI time series data."
    )
    parser.add_argument(
        "bids_dir",
        help="""
        The directory with the input dataset formatted according to the BIDS standard.
        """,
    )
    parser.add_argument(
        "output_dir",
        help="""
        The directory where the output files will be stored.
        """,
    )
    parser.add_argument(
        "analysis_level",
        help="""Level of the analysis that will be performed.
        Multiple participant level analyses can be run independently (in parallel)
        using the same output_dir.
        """,
        choices=["participant"],
    )
    parser.add_argument(
        "--participant_label",
        help="""
        The label(s) of the participant(s) that should be analyzed.
        The label corresponds to sub-<participant_label> from the BIDS spec
        (so it does not include "sub-").
        If this parameter is not provided, all subjects will be analyzed.
        Multiple participants can be specified with a space separated list.
        """,
        nargs="+",
    )
    parser.add_argument(
        "--action",
        help="""
        What action to perform:
        - prepare: prepare data for analysis coregister to template,
                   normalize and extract data
        - combine: combine data labels and data from different runs into a single file
        - generalize: generalize from data to give predicted labels
        """,
        choices=["prepare", "combine", "generalize"],
    )
    parser.add_argument(
        "--task",
        help="""
        The label of the task that will be analyzed.
        The label corresponds to task-<task_label> from the BIDS spec
        so it does not include "task-").
        """,
    )
    parser.add_argument(
        "--space",
        help="""
        The label of the space that will be analyzed.
        The label corresponds to space-<space_label> from the BIDS spec
        (so it does not include "space-").
        """,
    )
    parser.add_argument(
        "--model",
        help="model to use",
        choices=["guided_fixations"],
    )
    parser.add_argument(
        "--verbosity",
        help="INFO, WARNING. Defaults to INFO",
        choices=["INFO", "WARNING"],
    )
    parser.add_argument(
        "--debug",
        help="true or false",
    )

    args = parser.parse_args(argv[1:])

    cfg = set_cfg(args)

    log_level = args.verbosity or "INFO"
    if cfg["debug"]:
        log_level = "DEBUG"

    logging.basicConfig(
        level=log_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

    log = logging.getLogger("rich")

    if cfg["debug"]:
        log.debug("DEBUG MODE")

    if cfg["model_weights_file"] != "":
        assert Path(cfg["model_weights_file"]).is_file()
        log.info(f"Using model: {cfg['model_weights_file']}")

    if args.analysis_level == "participant":

        if args.action == "prepare":
            log.info("PREPARING DATA")
            prepare_data(cfg)

        elif args.action == "combine":
            log.info("COMBINING DATA")
            combine(cfg)

        elif args.action == "generalize":
            log.info("GENERALIZING")
            generalize(cfg)

        else:
            log.error("Unknown action")
            sys.exit(1)


def set_cfg(args):
    """Set the config."""
    # TODO extract function
    cfg = config()

    # TODO extract function
    subjects_to_analyze = []
    # only for a subset of subjects
    if args.participant_label:
        subjects_to_analyze = args.participant_label
    # for all subjects
    else:
        subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
        subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

    cfg["participant"] = subjects_to_analyze

    if args.task:
        cfg["task"] = args.task
    if args.task:
        cfg["space"] = args.space

    cfg["input_folder"] = Path(args.bids_dir)
    cfg["output_folder"] = Path(args.output_dir).joinpath("bidsmreye")

    if args.model == "guided_fixations":
        cfg["model_weights_file"] = Path.cwd().joinpath(
            "models",
            "dataset1_guided_fixations.h5",
        )

    if args.debug == "True":
        cfg["debug"] = True

    return cfg


if __name__ == "__main__":
    main()
