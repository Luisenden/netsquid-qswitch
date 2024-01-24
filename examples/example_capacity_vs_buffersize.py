r"""Perform simulations to obtain the impact as function of buffer size.
Outputs the file 'impacts_capacity_vs_buffer.pkl'. Results can be plotted with 'plot_impacts_capacity_vs_buffer.py'."""
import numpy as np
from netsquid_qswitch.runtools import Scenario, simulate_scenarios_and_aggregate_results_as_pickle


def main(no_output=False):
    np.random.seed(42)
    ratess = [[1.9 * 10 ** 6] * i for i in [5, 10]]  # 5 and 10 nodes
    buffer_sizess = [[[j]*i for i in [5, 10]] for j in [1, 100]]  # buffer sizes of 1 and 100 qubits
    scenarios = [Scenario(total_runtime_in_seconds=100 * 10 ** (-6), connect_size=3,
                          rates=rates, num_positions=1000,
                          buffer_size=buffer_sizess[j][i], decoherence_rate=0,
                          T2=10 ** (-5),
                          include_classical_comm=False) for j in range(2) for i, rates in enumerate(ratess)]

    filename = 'impacts_capacity_vs_buffer.pkl'
    simulate_scenarios_and_aggregate_results_as_pickle(scenarios=scenarios, number_of_runs=10, filename=filename)


if __name__ == "__main__":
    main(no_output=False)
