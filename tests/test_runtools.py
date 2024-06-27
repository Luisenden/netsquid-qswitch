import unittest
import numpy as np
from netsquid.nodes import Connection
from netsquid.components.models import FixedDelayModel
from netsquid_qswitch.runtools import Scenario, Simulation
from netsquid_qswitch.aux_functions import VARDOYAN_ATTEMPT_DURATION


class TestSimulation(unittest.TestCase):

    def test_run(self):

        self.run_simulation(delay=10,
                            number_of_leaves=2,
                            connect_size=2,
                            total_runtime_in_nanoseconds=9,
                            expected_number_of_produced_links=0)

        self.run_simulation(delay=10,
                            number_of_leaves=2,
                            connect_size=2,
                            total_runtime_in_nanoseconds=10 + 1e-9,
                            expected_number_of_produced_links=1)

        self.run_simulation(delay=10,
                            number_of_leaves=2,
                            connect_size=2,
                            total_runtime_in_nanoseconds=11,
                            expected_number_of_produced_links=1)

        self.run_simulation(delay=10,
                            number_of_leaves=2,
                            connect_size=2,
                            total_runtime_in_nanoseconds=20 + 1e-9,
                            expected_number_of_produced_links=2)

        self.run_simulation(delay=10,
                            number_of_leaves=2,
                            connect_size=2,
                            total_runtime_in_nanoseconds=21,
                            expected_number_of_produced_links=2)

    def run_simulation(self, delay, number_of_leaves, connect_size,
                       total_runtime_in_nanoseconds, expected_number_of_produced_links):
        scenario = Scenario(total_runtime_in_seconds=total_runtime_in_nanoseconds * 1e-9,
                            connect_size=connect_size,
                            server_node_name='leaf_node_0',
                            bright_state_population=[0.4]*number_of_leaves,
                            beta=0.1,
                            loss=1,
                            num_positions=1000,
                            buffer_size=np.inf,
                            T2=0,
                            decoherence_rate=0,
                            include_classical_comm=False)
        simulation = Simulation(scenario=scenario, distances=[2]*number_of_leaves,
                                repetition_times=[VARDOYAN_ATTEMPT_DURATION]*number_of_leaves, seed=42)

        self._convert_simulation_clocks_delay_model_to_fixed_delay(simulation=simulation, delay=delay)
        simulation.run()
        self.assertEqual(simulation.result.number_of_links_produced, expected_number_of_produced_links)

    def _convert_simulation_clocks_delay_model_to_fixed_delay(self, simulation, delay=0):
        for __, val in simulation._network.subcomponents.items():
            if isinstance(val, Connection):
                clock = val.subcomponents['clock']
                clock.add_property(name="start_delay", value=delay)
                clock.models["timing_model"] = FixedDelayModel(delay=delay)


if __name__ == "__main__":
    unittest.main()
