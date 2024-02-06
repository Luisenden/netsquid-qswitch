import unittest
from netsquid.components import Component
from netsquid.components.models import FixedDelayModel
from netsquid.nodes import Node
from netsquid.qubits import ketstates as ks
from netsquid_qswitch.network import setup_network, SWITCH_NODE_NAME, LEAF_NODE_BASENAME


class TestSetupPhysicalInfrastructure(unittest.TestCase):

    def test_setup_network(self):

        state = ks.b00
        distances_from_centre = [1, 2, 3]
        timing_models = \
            [FixedDelayModel(distance) for distance in distances_from_centre]

        network = setup_network(number_of_leaves=3,
                                distances_from_centre=distances_from_centre,
                                single_hop_state=state,
                                single_hop_timing_models=timing_models,
                                num_positions=5,
                                T2=3,
                                bright_state_population=[0.4]*3)

        self.assertIsInstance(network, Component)
        self.assertIsInstance(network.subcomponents[SWITCH_NODE_NAME], Node)
        for node_index in range(3):
            self.assertIsInstance(network.subcomponents[LEAF_NODE_BASENAME + str(node_index)], Node)


if __name__ == "__main__":
    unittest.main()
