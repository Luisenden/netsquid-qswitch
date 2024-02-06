"""Perform simulations to obtain the mean capacity as function of buffer size.
Outputs the file 'data_buffer_size_vs_capacity.csv' and a plot of the results."""
from netsquid_qswitch.plot_csv_with_errorbars import get_plot_from_csv
from netsquid_qswitch.aux_functions import analytical_capacity_with_ghz_dimension_2
from netsquid_qswitch.runtools import Scenario, simulate_scenarios_and_aggregate_results_as_csv


def main(no_output=False):

    buffer_sizes = [1, 3, 5]
    number_of_leaves = 5

    scenarios = [
        Scenario(total_runtime_in_seconds=100 * 10 ** (-6),
                 connect_size=2,
                 num_positions=100,
                 buffer_size=buffer_size,
                 decoherence_rate=0,
                 beta=0.1,
                 loss=1,
                 server_node_name=None,
                 bright_state_population=[0.3]*number_of_leaves,
                 T2=0,
                 include_classical_comm=False)
        for buffer_size in buffer_sizes]

    csv_filename = 'data_buffer_size_vs_capacity.csv'

    simulate_scenarios_and_aggregate_results_as_csv(scenarios=scenarios, distances=[2]*number_of_leaves,
                                                    repetition_times=[10**-3]*number_of_leaves, number_of_runs=30,
                                                    csv_filename=csv_filename)

    # PLOTTING

    # numerical results
    plot, xvals = get_plot_from_csv(csv_filename=csv_filename,
                                    x_name="buffer_size",
                                    y_name="mean_capacity",
                                    y_err_name="std_capacity",
                                    label="NetSquid simulations")

    # analytical results
    decoherence_rate = 0
    rate = 1 * 10 ** 6
    number_of_leaves = 5
    yvals = [analytical_capacity_with_ghz_dimension_2(
                mus=[rate] * number_of_leaves,
                B=int(buffer_size),
                alpha=decoherence_rate,
                q=1)
             for buffer_size in xvals]
    plot.plot(xvals, yvals, label="analytical (Vardoyan et al.)")
    plot.legend()

    if not no_output:
        plot.show()


if __name__ == "__main__":
    main(no_output=False)
