r"""Perform simulations to obtain the mean fidelity as function of memory coherence time $T_2$.
Outputs the file 'data_T2_vs_fidelity.csv' and a plot of the results."""
import numpy as np
from netsquid_qswitch.runtools import Scenario, simulate_scenarios_and_aggregate_results_as_csv
from netsquid_qswitch.plot_csv_with_errorbars import get_plot_from_csv


def main(no_output=False):
    number_of_leaves = 3
    T2s = [10 ** (-7), 5 * 10 ** (-6), 10 ** (-5)]

    scenarios = [
        Scenario(total_runtime_in_seconds=100 * 10 ** (-6),
                 connect_size=2,
                 num_positions=100,
                 buffer_size=np.inf,
                 beta=0.1,
                 loss=1,
                 server_node_name=None,
                 decoherence_rate=0,
                 bright_state_population=[0.3]*number_of_leaves,
                 T2=T2,
                 include_classical_comm=False)
        for T2 in T2s]

    csv_filename = 'data_T2_vs_fidelity.csv'
    simulate_scenarios_and_aggregate_results_as_csv(scenarios=scenarios, distances=[2]*number_of_leaves,
                                                    repetition_times=[10**-3]*number_of_leaves,
                                                    number_of_runs=3, csv_filename=csv_filename)

    # PLOTTING
    plot, xvals = get_plot_from_csv(csv_filename=csv_filename,
                                    x_name="T2",
                                    y_name="mean_fidelity",
                                    y_err_name="std_fidelity",
                                    label="NetSquid simulations")

    if not no_output:
        plot.show()


if __name__ == "__main__":
    main(no_output=False)
