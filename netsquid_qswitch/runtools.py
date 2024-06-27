"""Tools for simulating the quantum switch as central node in a star network.

All tools in this file build towards the method
:meth:`~netsquid_qswitch.runtools.simulate_scenarios_and_aggregate_results_as_csv`.

Example usage of this method for performing multiple simulation scenarios where
the buffer size of the switch is varied:

>>> buffer_sizes = [1, 3, 5]
>>> number_of_leaves = 5
>>> scenarios = [
>>>     Scenario(total_runtime_in_seconds=100 * 10 ** (-6),
>>>              connect_size=2,
>>>              num_positions=1000,
>>>              buffer_size=buffer_size,
>>>              decoherence_rate=0,
>>>              T2=0,
>>>              include_classical_comm=False)
>>>     for buffer_size in buffer_sizes]
>>>
>>> simulate_scenarios_and_aggregate_results_as_csv(
>>>     scenarios=scenarios,
>>>     number_of_runs=30,
>>>     csv_filename='data_buffer_size_vs_capacity.csv')
"""

from collections import namedtuple
import re
import numpy as np
import pandas as pd
import netsquid as ns
from netsquid.nodes import Connection, Node
from netsquid.components import ClassicalFibre
from netsquid.qubits import ketstates as ks
from netsquid_qswitch.aux_functions import distance_to_rate
from netsquid_qswitch.network import ExponentialDelayModel, setup_network
from netsquid_qswitch.protocols import DATA_PROTOCOL_NAME, SWITCH_NODE_NAME, LEAF_NODE_BASENAME, setup_protocols


Scenario = namedtuple('Scenario',
                      ['total_runtime_in_seconds',
                       'connect_size',
                       'server_node_name',
                       'num_positions',
                       'buffer_size',
                       'bright_state_population',
                       'T2',
                       'beta',
                       'loss',
                       'decoherence_rate',
                       'include_classical_comm'])


class SimulationResult:

    def __init__(self, fidelities, nodes_involved, total_runtime_in_seconds):
        self._fidelities = fidelities
        self._nodes_involved = nodes_involved
        self._total_runtime_in_seconds = total_runtime_in_seconds

    @property
    def fidelities(self):
        return self._fidelities

    @property
    def nodes_involved(self):
        return self._nodes_involved

    @property
    def mean_fidelity(self):
        return np.mean(self._fidelities)

    @property
    def total_runtime_in_seconds(self):
        return self._total_runtime_in_seconds

    @property
    def capacity(self):
        return self.number_of_links_produced / self._total_runtime_in_seconds

    @property
    def number_of_links_produced(self):
        return len(self.fidelities)


class Simulation:
    """
    Parameters
    ----------
    scenario: :obj:`~netsquid_qswitch.quantum_switch.Scenario`
    distances: list of float or "default"
        The distances between users and switch. If set to "default",
        then the distances are computed from the rates as specified
        in `scenario`
    """

    def __init__(self, scenario, distances, repetition_times, seed):

        self._has_run = False
        ns.set_qstate_formalism(ns.QFormalism.DM)
        self._seed = seed

        self._scenario = scenario
        self._set_distances(distances=distances)
        self._set_repetition_times(repetition_times=repetition_times)

        self._network = self._get_network()

        self._protocol = self._get_protocol()

        self._set_port_forwarding()

    def _set_port_forwarding(self):

        self._switch_node = self._network.subcomponents[SWITCH_NODE_NAME]
        self._leaf_nodes = [comp for name, comp in self._network.subcomponents.items()
                            if isinstance(comp, Node) and LEAF_NODE_BASENAME in name]
        self._leaf_nodes.sort(key=lambda node: int(re.search('_([0-9]+)', node.name).group(1)))

        port_names = ["port_qconn2qproc_{}".format(ix)
                      for ix in range(len(self._connections))]

        for leaf_ix, (leaf_node, qconnection) in enumerate(zip(self._leaf_nodes, self._connections)):
            # tie the quantum connection with ports to the quantum processors
            # of the two nodes on the end of the connection

            # get the port objects
            switch_port_name, leaf_port_name = \
                self._switch_node.connect_to(leaf_node, qconnection, local_port_name=port_names[leaf_ix])
            switch_port = self._switch_node.ports[switch_port_name]
            leaf_port = leaf_node.ports[leaf_port_name]

            # set forwarding of quantum messages from connection to
            # the qprocessor
            switch_port.forward_input(self._switch_node.qmemory.ports["qin{}".format(leaf_ix)])
            leaf_port.forward_input(leaf_node.qmemory.ports["qin0"])

    def _set_distances(self, distances):
        self._distances = distances

    def _set_repetition_times(self, repetition_times):
        if isinstance(repetition_times, int):
            self._repetition_times = repetition_times * len(self._distances)
        else:
            self._repetition_times = repetition_times

    def _get_network(self):
        number_of_leaves = len(self._distances)

        rates = [alpha*distance_to_rate(distance=distance, loss_coefficient=self._scenario.beta,
                                        loss_parameter=self._scenario.loss, attempt_duration=T)
                 for alpha, T, distance in zip(self._scenario.bright_state_population,
                                               self._repetition_times, self._distances)]
        timing_models = \
            [ExponentialDelayModel(rate) for rate in rates]

        network = setup_network(
            number_of_leaves=number_of_leaves,
            distances_from_centre=self._distances,
            single_hop_state=ks.b00,
            single_hop_timing_models=timing_models,
            bright_state_population=self._scenario.bright_state_population,
            num_positions=self._scenario.num_positions,
            T2=self._scenario.T2 * 10 ** 9)  # T2 should also be given in seconds

        self._connections = [conn
                             for __, conn in network.subcomponents.items()
                             if isinstance(conn, Connection)]
        self._connections.sort(key=lambda conn: int(re.search('qchann([0-9]+)', conn.name).group(1)))
        cchannels = []

        for connection in self._connections:
            for __, component in connection.subcomponents.items():
                if isinstance(component, ClassicalFibre):
                    cchannels.append(component)

        return network

    def _get_protocol(self):
        if self._scenario.include_classical_comm:
            raise NotImplementedError
        else:
            max_channel_delay = 0
        max_channel_delay *= 10 ** (-9)  # in seconds
        protocol = setup_protocols(network=self._network,
                                   connect_size=self._scenario.connect_size,
                                   num_positions=self._scenario.num_positions,
                                   buffer_size=self._scenario.buffer_size,
                                   server_node_name=self._scenario.server_node_name,
                                   max_channel_delay=max_channel_delay,
                                   decoherence_rate=self._scenario.decoherence_rate * 10 ** (-9))
        return protocol

    def _start_all_clocks(self):
        for __, val in self._network.subcomponents.items():
            if isinstance(val, Connection):
                clock = val.subcomponents['clock']
                clock.start()

    def reset(self):
        self._has_run = False
        self._network.reset()
        for __, subcomponent in self._network.subcomponents.items():
            subcomponent.reset()
        for __, protocol in self._protocol.subprotocols.items():
            protocol.reset()

    @property
    def has_run(self):
        return self._has_run

    def run(self):
        if self.has_run:
            raise Exception('Simulation has run already')
        ns.sim_reset()
        self.reset()
        ns.set_random_state(self._seed)
        self._start_all_clocks()
        ns.sim_run(self._scenario.total_runtime_in_seconds * 1e9)
        self._has_run = True

    @property
    def result(self):
        """
        SimulationResult
        """
        if not self.has_run:
            raise Exception('Simulation has not run yet')
        fidelities = self._protocol.subprotocols[DATA_PROTOCOL_NAME].fidelities
        nodes_involved = self._protocol.subprotocols[DATA_PROTOCOL_NAME].nodes_involved
        return SimulationResult(fidelities=fidelities, nodes_involved=nodes_involved,
                                total_runtime_in_seconds=self._scenario.total_runtime_in_seconds)


class SimulationMultiple:

    def __init__(self, simulation, number_of_runs=1):
        self._simulation = simulation
        self._number_of_runs = number_of_runs
        self.reset()

    def run(self):
        for __ in range(self._number_of_runs):
            self._simulation.reset()
            self._simulation._seed += 1
            self._simulation.run()
            self._results.append(self._simulation.result)

    def reset(self):
        self._results = []

    @property
    def results(self):
        return self._results


def _convert_scenario_to_dict(scenario):
    return {
        "total_runtime_in_seconds": scenario.total_runtime_in_seconds,
        "connect_size": scenario.connect_size,
        "num_positions": scenario.num_positions,
        "buffer_size": scenario.buffer_size,
        "T2": scenario.T2,
        "decoherence_rate": scenario.decoherence_rate,
        "include_classical_comm": scenario.include_classical_comm,
        }


def _convert_simulation_result_to_dict(simulation_result):
    return {
        "mean_fidelity": simulation_result.mean_fidelity,
        "capacity": simulation_result.capacity,
        }


def _convert_simulation_to_data_dict(simulation):
    return _convert_scenario_to_dict(simulation._scenario) + \
        _convert_simulation_result_to_dict(simulation.result)


def convert_simulation_to_dataframe(simulation):
    df = pd.DataFrame()
    data = _convert_simulation_to_data_dict(simulation)
    df = df.append(data, ignore_index=True)
    return df


def convert_simulation_multiple_to_dataframe(simulation_multiple):
    df = pd.DataFrame()
    scenario_dict = _convert_scenario_to_dict(simulation_multiple._simulation._scenario)
    for result in simulation_multiple.results:
        data = scenario_dict
        data.update(_convert_simulation_result_to_dict(result))
        df = df.append(data, ignore_index=True)
    return df


def convert_simulation_multiple_to_csv(simulation_multiple, csv_filename="data.csv"):
    df = convert_simulation_multiple_to_dataframe(simulation_multiple)
    df.to_csv(path_or_buf=csv_filename)


def simulate_scenarios_and_write_all_results_to_csv(scenarios, distances, repetition_times,
                                                    number_of_runs=1, csv_filename="data.csv"):
    df = pd.DataFrame()
    for scenario in scenarios:
        simulation = Simulation(scenario=scenario, distances=distances, repetition_times=repetition_times, seed=42)
        sm = SimulationMultiple(simulation=simulation, number_of_runs=number_of_runs)
        sm.run()
        data = convert_simulation_multiple_to_dataframe(sm)
        df = df.append(data, ignore_index=True)
    df.to_csv(path_or_buf=csv_filename)


def simulate_scenarios_and_aggregate_results_as_csv(scenarios, distances, repetition_times,
                                                    number_of_runs=1, csv_filename="data.csv"):
    df = pd.DataFrame()
    for scenario in scenarios:
        simulation = Simulation(scenario=scenario, distances=distances, repetition_times=repetition_times, seed=42)
        sm = SimulationMultiple(simulation=simulation, number_of_runs=number_of_runs)
        sm.run()

        data = _convert_scenario_to_dict(scenario=scenario)

        mean_fidelities = [result.mean_fidelity for result in sm.results]
        capacities = [result.capacity for result in sm.results]
        data["mean_fidelity"] = np.mean(mean_fidelities)
        data["mean_capacity"] = np.mean(capacities)
        data["std_fidelity"] = np.std(mean_fidelities) / np.sqrt(len(capacities))
        data["std_capacity"] = np.std(capacities) / np.sqrt(len(capacities))

        df = df.append(data, ignore_index=True)
    df.to_csv(path_or_buf=csv_filename)


def simulate_scenarios_and_aggregate_results_as_pickle(scenarios, distances, repetition_times,
                                                       number_of_runs=1, filename="data.pkl"):
    df = pd.DataFrame()
    for i, scenario in enumerate(scenarios):
        simulation = Simulation(scenario=scenario, distances=distances, repetition_times=repetition_times)
        sm = SimulationMultiple(simulation=simulation, number_of_runs=number_of_runs)
        sm.run()

        data = _convert_scenario_to_dict(scenario=scenario)
        states_per_node = []
        for result in sm.results:
            nodes_involved_per_run = [x for nodes in result.nodes_involved for x in nodes]
            nodes_involved_per_run = pd.Series(nodes_involved_per_run).value_counts()/scenario.total_runtime_in_seconds
            states_per_node.append(nodes_involved_per_run)
        states_per_node = pd.DataFrame.from_records(states_per_node)
        states_per_node = states_per_node.reindex(sorted(states_per_node.columns,
                                                         key=lambda x: int(re.search('_([0-9]+)', x).group(1))), axis=1)

        mean_states_per_node = states_per_node.mean(axis=0).to_dict()
        mean_fidelities = [result.mean_fidelity for result in sm.results]
        capacities = [result.capacity for result in sm.results]

        data["mean_fidelity"] = np.mean(mean_fidelities)
        data["mean_capacity"] = np.mean(capacities)
        data["nnodes"] = len(scenario.buffer_size)

        data = {**data, **mean_states_per_node}
        print(f'scenario {i}/{len(scenarios)} done')
        df = df.append(data, ignore_index=True)
    df.to_pickle(path=filename)
