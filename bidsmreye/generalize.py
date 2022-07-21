"""foo."""
import os

from deepmreye import analyse
from deepmreye import train
from deepmreye.util import data_generator
from deepmreye.util import model_opts
from rich import print

from bidsmreye.bidsutils import check_layout
from bidsmreye.bidsutils import get_dataset_layout
from bidsmreye.utils import list_subjects
from bidsmreye.utils import return_regex


def generalize(cfg):
    """_summary_."""
    output_dataset_path = cfg["output_folder"]

    print(f"\nindexing {output_dataset_path}\n")

    layout_out = get_dataset_layout(output_dataset_path)
    check_layout(layout_out)

    subjects = list_subjects(layout_out, cfg)
    if cfg["debug"]:
        subjects = [subjects[0]]

    print(f"processing subjects: {subjects}\n")

    all_data = []

    for subject_label in subjects:

        data = layout_out.get(
            return_type="filename",
            subject=return_regex(subject_label),
            suffix="^bidsmreye$",
            task=return_regex(cfg["task"]),
            space=return_regex(cfg["space"]),
            extension=".npz",
            regex_search=True,
        )

        for file in data:
            print(f"adding file: {os.path.basename(file)}")
            all_data.append(file)

    print("\n")

    generators = data_generator.create_generators(all_data, all_data)
    generators = (*generators, all_data, all_data)

    print("\n")

    # Get untrained model and load with trained weights
    opts = model_opts.get_opts()
    model_weights = cfg["model_weights_file"]
    (model, model_inference) = train.train_model(
        dataset="example_data", generators=generators, opts=opts, return_untrained=True
    )
    model_inference.load_weights(model_weights)

    (evaluation, scores) = train.evaluate_model(
        dataset="group",
        model=model_inference,
        generators=generators,
        save=True,
        model_path=f"{layout_out.root}/",
        model_description="",
        verbose=3,
        percentile_cut=80,
    )

    fig = analyse.visualise_predictions_slider(
        evaluation,
        scores,
        color="rgb(0, 150, 175)",
        bg_color="rgb(255,255,255)",
        ylim=[-11, 11],
    )
    fig.show()
