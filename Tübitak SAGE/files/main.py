import argparse

from src.variables import ImageData
from src.mtf_pipeline import MTFPipeline
from src.graph import Graph


PIXEL_PITCH_MM = 0.017
DEFAULT_MAT_KEY = "img_final"


def make_data(
    path,
    mat_key,
    hdf5_transpose,
):
    return ImageData(
        data_path=path,
        mat_key=mat_key,
        mat_hdf5_transpose=hdf5_transpose,
        pixel_pitch_mm=PIXEL_PITCH_MM,
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Half-moon sensor MTF_X + MTF_Y. "
            "The same original straight-edge algorithm is run "
            "independently on two physical MAT captures."
        )
    )

    parser.add_argument(
        "first_mat",
        help=(
            "First half-moon MAT capture. "
            "X/Y assignment is detected automatically from edge normal."
        ),
    )

    parser.add_argument(
        "second_mat",
        help=(
            "Second half-moon MAT capture, physically rotated orientation."
        ),
    )

    parser.add_argument(
        "--mat-key",
        default=DEFAULT_MAT_KEY,
        help="MAT variable name. Default: img_final",
    )

    parser.add_argument(
        "--no-hdf5-transpose",
        action="store_true",
        help="Disable transpose for MATLAB v7.3/HDF5 files.",
    )

    parser.add_argument(
        "--no-graphs",
        action="store_true",
        help="Run terminal analysis only.",
    )

    args = parser.parse_args()

    transpose = (
        not args.no_hdf5_transpose
    )

    data_a = make_data(
        args.first_mat,
        args.mat_key,
        transpose,
    )

    data_b = make_data(
        args.second_mat,
        args.mat_key,
        transpose,
    )

    pipeline = MTFPipeline()

    results = pipeline.run_xy(
        data_a,
        data_b,
    )

    x_data = results[
        "x"
    ][
        "data"
    ]

    y_data = results[
        "y"
    ][
        "data"
    ]

    if not args.no_graphs:
        graph = Graph()

        # Full diagnostic graph set for X.
        graph.show_all_for_axis(
            x_data,
            "MTF_X",
        )

        # Full diagnostic graph set for Y.
        graph.show_all_for_axis(
            y_data,
            "MTF_Y",
        )

        # Final comparison graphs.
        graph.plot_xy_comparison(
            x_data,
            y_data,
        )

        graph.plot_xy_summary_bar(
            x_data,
            y_data,
        )


if __name__ == "__main__":
    main()
