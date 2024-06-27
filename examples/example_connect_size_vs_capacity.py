"""Perform simulations to obtain the mean capacity as function of the 'connect' size, i.e.
the number of qubits of the final GHZ-state that the user nodes will share.
Outputs the file 'data_connect_size_vs_capacity.csv' and a plot of the results."""
import numpy as np
from netsquid_qswitch.runtools import Scenario, simulate_scenarios_and_aggregate_results_as_csv
from netsquid_qswitch.plot_csv_with_errorbars import get_plot_from_csv
from netsquid_qswitch.aux_functions import analytical_capacity_in_homogeneous_noiseless_case


def main(no_output=False):

    connect_sizes = [2, 3, 4]
    number_of_leaves = 5
    scenarios = [
        Scenario(total_runtime_in_seconds=100 * 10 ** (-6),
                 connect_size=connect_size,
                 num_positions=100,
                 buffer_size=np.inf,
                 decoherence_rate=0,
                 beta=0.1,
                 loss=1,
                 server_node_name=None,
                 bright_state_population=[0.3]*number_of_leaves,
                 T2=0,
                 include_classical_comm=False)
        for connect_size in connect_sizes]

    csv_filename = "data_connect_size_vs_capacity.csv"

    simulate_scenarios_and_aggregate_results_as_csv(scenarios=scenarios, distances=[2]*number_of_leaves,
                                                    repetition_times=[10**-3]*number_of_leaves,
                                                    number_of_runs=10, csv_filename=csv_filename)

    # PLOTTING

    # numerical results
    plot, xvals = get_plot_from_csv(csv_filename=csv_filename,
                                    x_name="connect_size",
                                    y_name="mean_capacity",
                                    y_err_name="std_capacity",
                                    label="NetSquid simulations")

    # analytical results
    number_of_leaves = 5
    rate = 1 * 10 ** 6
    yvals = [
        analytical_capacity_in_homogeneous_noiseless_case(
            k=number_of_leaves,
            mu=rate,
            n=connect_size,
            q=1) for connect_size in xvals]
    plot.plot(xvals, yvals, label="analytical (Vardoyan et al.)")

    if not no_output:
        plot.show()


if __name__ == "__main__":
    main(no_output=False)
