"""
Tool for producing a plot from a CSV-file as outputted by
:meth:`~netsquid_qswitch.runtools.simulate_scenarios_and_aggregate_results_as_csv`.

Example usage to plot buffer size on the horizontal axis
and the mean capacity (with error bars) on the vertical axis:

python3 plot_csv_with_errorbars.py --csv_filename mydatafile.csv
        --x_name buffer_size --y_name mean_capacity --y_err_name std_capacity

Note: the arguments `x_name`, `y_name` and `y_err_name` should be column names as found in the CSV file.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import argparse


def get_plot_from_csv(csv_filename, x_name, y_name, y_err_name=None, label=""):
    """
    Converts a CSV file as outputted by
    :meth:`~netsquid_qswitch.runtools.simulate_scenarios_and_aggregate_results_as_csv`.
    to a plot. Note: the arguments `x_name`, `y_name` and `y_err_name` should be
    column names as found in the CSV file.

    Parameters
    ----------
    csv_filename : str
    x_name : str
        Variable to be put on the horizontal axis.
    y_name : str
        Variable to be put on the vertical axis.
    y_err_name : str
        Variable denoting the error bars in vertical direction.
    label : str

    Returns
    -------
    tuple of matplotlib.pyplot, list of float
        Plot, values on its x axis
    """
    matplotlib.rcParams.update({'font.size': 30})
    df = pd.read_csv(csv_filename, header=0)
    fig, ax = plt.subplots()
    if y_err_name is None:
        yerr = [0 for __ in df[y_name]]
    else:
        yerr = df[y_err_name]
    ax.errorbar(x=df[x_name],
                y=df[y_name],
                yerr=yerr,
                fmt='o',
                label=label,
                markersize=15)
    ax.set_ylabel(y_name)
    ax.set_xlabel(x_name)
    xvalues = list(df[x_name])
    return plt, xvalues


if __name__ == "__main__":

    # parse arguments
    parser = argparse.ArgumentParser(description='Get plot from CSV file')
    parser.add_argument('--csv_filename', type=str, help='Name of the CSV file')
    parser.add_argument('--x_name', type=str,
                        help='Name of the variable to be put on the x-axis')
    parser.add_argument('--y_name', type=str,
                        help='Name of the variable to be put on the y-axis')
    parser.add_argument('--y_err_name', type=str, default=None,
                        help='Name of the error variable on the y-axis')

    args = parser.parse_args()

    # produce and show the plot
    plot, __ = get_plot_from_csv(csv_filename=args.csv_filename,
                                 x_name=args.x_name,
                                 y_name=args.y_name,
                                 y_err_name=args.y_err_name)
    plot.show()
