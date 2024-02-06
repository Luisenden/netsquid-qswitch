import unittest
import numpy as np
import netsquid as ns
from netsquid.nodes import Node
from netsquid.components.qprocessor import QuantumProcessor
from netsquid.components import PhysicalInstruction
import netsquid.qubits.qubitapi as qapi
from netsquid.components.instructions import (INSTR_SWAP, INSTR_CNOT, INSTR_H, INSTR_MEASURE)
from netsquid_qswitch.protocols import StarNodeProtocol, SwitchProtocol
from netsquid_qswitch.memory_management import MemoryManager
import netsquid_qswitch.quantum_programs as switch_qprog


class TestStarNodeProtocol(unittest.TestCase):

    def setUp(self):
        self.node = Node("TestNode")
        self.num_positions = 5
        self.name = "test_of_StarNodeProtocol"

    def test_perform_move(self):

        # make sure the node can perform the 'move' operation
        # by adding it to the physical instructions that the
        # node's quantumprocessor holds
        phys_instructions = [PhysicalInstruction(INSTR_SWAP, duration=0, q_nosie_model=None)]
        self.qprocessor = QuantumProcessor(name='qprocessor',
                                           num_positions=self.num_positions,
                                           fallback_to_nonphysical=False,
                                           phys_instructions=phys_instructions)
        self.node.add_subcomponent(self.qprocessor)

        self.memorymanager = MemoryManager(num_positions=self.num_positions,
                                           decoherence_rate=10,
                                           node_name='dummy_node_name')
        self.protocol = StarNodeProtocol(node=self.node,
                                         name='starnodeprotocol',
                                         memorymanager=self.memorymanager)

        # initate a fresh qubit at position 3,
        # including a note in the memorymanagement
        [qubit] = qapi.create_qubits(1)
        self.qprocessor.put(qubits=[qubit], positions=[3])
        self.memorymanager.add_fresh_link(mem_pos=3,
                                          remote_node_name='remote_node',
                                          fresh_link_ID=42)

        # a protocol that performs that '_perform_move' operation of
        # StarNodeProtocol to move the qubit from position 3 to position 4
        class MoveQubitFromPosition3To4Protocol(ns.protocols.Protocol):

            def __init__(self, name, protocol):
                super().__init__(name=name)
                self.protocol = protocol
                self.has_performed_move = False

            def run(self):
                # make StarNodeProtocol move the qubit from position 3 to 4
                yield self.protocol._perform_move(old_position=3, new_position=4)
                self.has_performed_move = True

        # initialize the protocol and run it
        p = MoveQubitFromPosition3To4Protocol(name='hi', protocol=self.protocol)
        p.start()
        ns.sim_run()
# perform checks:
        # - that the code has run
        self.assertTrue(p.has_performed_move)

        # - that the memory management is correctly updated: there is
        #   now a qubit at position 4 instead of 3
        qubit_position = self.memorymanager.get_position(remote_node_name='remote_node', link_ID=42)
        self.assertEqual(qubit_position, 4)
        self.assertEqual(3, self.memorymanager.get_free_mem_positions(possible_mem_pos=[3], number_of_positions=1)[0])

        # - that the quantum processor is correctly updated: there is
        #   now a qubit at position 4 instead of 3
        self.assertTrue(self.qprocessor.pop(4) is not None)
        self.assertEqual(self.qprocessor.pop(3), [None])

    def test_perform_connect(self):

        # make sure the node can perform the 'connect' operation
        # by adding it to the physical instructions that the
        # node's quantumprocessor holds
        phys_instructions = [
            PhysicalInstruction(INSTR_CNOT, duration=0, q_nosie_model=None),
            PhysicalInstruction(INSTR_H, duration=0, q_nosie_model=None),
            PhysicalInstruction(INSTR_MEASURE, duration=0, q_nosie_model=None),
            ]
        self.qprocessor = QuantumProcessor(name='qprocessor',
                                           num_positions=self.num_positions,
                                           fallback_to_nonphysical=False,
                                           phys_instructions=phys_instructions)
        self.node.add_subcomponent(self.qprocessor)

        self.memorymanager = MemoryManager(num_positions=self.num_positions,
                                           decoherence_rate=10,
                                           node_name='dummy_node_name')
        self.protocol = StarNodeProtocol(node=self.node,
                                         name='starnodeprotocol',
                                         memorymanager=self.memorymanager)

        # initate a fresh qubit at position 1 and 2
        # including a note in the memorymanagement
        qubits = qapi.create_qubits(2)
        self.qprocessor.put(qubits=qubits, positions=[1, 2])
        for position, link_id in [(1, 42), (2, 43)]:
            self.memorymanager.add_fresh_link(mem_pos=position,
                                              remote_node_name='remote_node',
                                              fresh_link_ID=link_id)

        self.protocol._connect_program = \
            switch_qprog.create_quantum_circuit_for_connect(connect_size=2)

        # a protocol that performs that '_perform_connect' operation of
        # StarNodeProtocol to perform a GHZ-basis measurement on
        # the qubits from positions 1 and 2
        class GHZMeasurePosition1And2Protocol(ns.protocols.Protocol):

            def __init__(self, name, protocol):
                super().__init__(name=name)
                self.protocol = protocol
                self.has_performed_move = False

            def run(self):
                # make StarNodeProtocol perform GHZ basis measurement
                # on positions 1 and 2
                yield self.protocol._perform_connect(positions=[1, 2])
                self.has_performed_move = True

        # initialize the protocol and run it
        p = GHZMeasurePosition1And2Protocol(name='hi', protocol=self.protocol)
        p.start()
        ns.sim_run()

        # perform checks:
        # - that the code has run
        self.assertTrue(p.has_performed_move)

        # - that the memory management is correctly updated: there is
        #   no qubit at position 1 or 2
        for link_id in [42, 43]:
            with self.assertRaises(Exception):
                self.memorymanager.get_position(remote_node_name='remote_node',
                                                link_ID=link_id)
        for pos in [3, 4]:
            self.assertEqual(
                pos,
                self.memorymanager.get_free_mem_positions(possible_mem_pos=[pos], number_of_positions=1)[0])

    def test_get_necessary_moves(self):

        self.qprocessor = QuantumProcessor(name='qprocessor',
                                           num_positions=self.num_positions)
        self.node.add_subcomponent(self.qprocessor)
        self.memorymanager = MemoryManager(num_positions=self.num_positions,
                                           decoherence_rate=10,
                                           node_name='dummy_node_name')
        self.protocol = StarNodeProtocol(node=self.node,
                                         name='starnodeprotocol',
                                         memorymanager=self.memorymanager)

        self.protocol._reserved_positions = [1, 4]
        self.protocol._not_reserved_positions = [2, 3]

        # no positions are in use, so no move needed
        move_positions = \
            self.protocol._get_necessary_move_positions()
        self.assertEqual(move_positions, [])

        # position 1 is in use
        self.memorymanager.add_fresh_link(mem_pos=1,
                                          remote_node_name='abc',
                                          fresh_link_ID=42)
        move_positions = \
            self.protocol._get_necessary_move_positions()
        self.assertEqual(move_positions, [(1, 2)])


class TestSwitchProtocol(unittest.TestCase):

    def setUp(self):
        self.num_positions = 10

    def _setup_network(self, connect_size, number_of_leaves, buffer_size):

        qprocessor = QuantumProcessor(name='qprocessor',
                                      num_positions=self.num_positions)

        node = Node("TestNode")
        node.add_subcomponent(qprocessor)
        leaf_names = ["leaf_{}".format(ix) for ix in range(number_of_leaves)]
        leaf_nodes = [Node(leaf_name) for leaf_name in leaf_names]
        protocol = SwitchProtocol(node=node, name='test_switch',
                                  leaf_nodes=leaf_nodes,
                                  connect_size=connect_size,
                                  buffer_size=buffer_size)
        return protocol, leaf_nodes

    def test_reserved_positions_and_not_reserved_positions(self):
        number_of_leaves = 3
        protocol, leaf_nodes = \
            self._setup_network(connect_size=2, number_of_leaves=number_of_leaves, buffer_size=np.inf)

        expected_reserved_positions = [0, 1, 2]
        expected_not_reserved_positions = [3, 4, 5, 6, 7, 8, 9]

        self.assertEqual(protocol.reserved_positions, expected_reserved_positions)
        self.assertEqual(protocol.not_reserved_positions, expected_not_reserved_positions)

    class MockProtocol(SwitchProtocol):

        number_of_noticed_new_link_arrivals = 0

        def _add_new_link_to_memory_manager(self, leaf_index):
            self.number_of_noticed_new_link_arrivals += 1
            super()._add_new_link_to_memory_manager(leaf_index)

    def _setup_network_with_mock_protocol(self, connect_size, number_of_leaves):

        phys_instructions = [
            PhysicalInstruction(INSTR_SWAP, duration=0, q_nosie_model=None),
            PhysicalInstruction(INSTR_CNOT, duration=0, q_nosie_model=None),
            PhysicalInstruction(INSTR_H, duration=0, q_nosie_model=None),
            PhysicalInstruction(INSTR_MEASURE, duration=0, q_nosie_model=None),
            ]
        qprocessor = QuantumProcessor(name='qprocessor',
                                      num_positions=self.num_positions,
                                      phys_instructions=phys_instructions)

        node = Node("TestNode")
        node.add_subcomponent(qprocessor)
        leaf_names = ["leaf_{}".format(ix) for ix in range(number_of_leaves)]
        leaf_nodes = [Node(leaf_name) for leaf_name in leaf_names]

        protocol = self.MockProtocol(node=node, name='test_switch',
                                     leaf_nodes=leaf_nodes,
                                     connect_size=connect_size,
                                     buffer_size=np.inf)
        return protocol, leaf_nodes

    def test_not_triggered_by_qubit_arrival_on_other_node_single(self):

        ns.sim_reset()
        number_of_leaves = 3
        protocol, leaf_nodes = \
            self._setup_network_with_mock_protocol(connect_size=2,
                                                   number_of_leaves=number_of_leaves
                                                   )
        protocol.reset()

        irrelevant_protocol, _ = \
            self._setup_network(connect_size=2, number_of_leaves=number_of_leaves, buffer_size=np.inf)

        # ensure that the port of another protocol triggers
        qubit = ns.qubits.qubit.Qubit(name='qubit')
        port = irrelevant_protocol.node.qmemory.ports['qin0']
        port.tx_input(qubit)

        ns.sim_run()

        # check that the SwitchProtocol has not triggered
        self.assertEqual(protocol.number_of_noticed_new_link_arrivals, 0)

    def test_not_triggered_by_qubit_arrival_on_other_node_twice(self):

        ns.sim_reset()
        number_of_leaves = 3
        protocol, leaf_nodes = \
            self._setup_network_with_mock_protocol(connect_size=2,
                                                   number_of_leaves=number_of_leaves
                                                   )
        protocol.reset()

        irrelevant_protocol, _ = \
            self._setup_network(connect_size=2, number_of_leaves=number_of_leaves, buffer_size=np.inf)

        # ensure that the port of another protocol triggers...

        # ...once
        qubit = ns.qubits.qubit.Qubit(name='qubit0')
        port = irrelevant_protocol.node.qmemory.ports['qin0']
        port.tx_input(qubit)

        # ...twice
        qubit = ns.qubits.qubit.Qubit(name='qubit1')
        port = irrelevant_protocol.node.qmemory.ports['qin1']
        port.tx_input(qubit)

        ns.sim_run()

        # check that the SwitchProtocol has not triggered
        self.assertEqual(protocol.number_of_noticed_new_link_arrivals, 0)

    # def test_triggered_by_qubit_arrival_once(self):

    #     ns.sim_reset()
    #     number_of_leaves = 3
    #     protocol, leaf_nodes = \
    #         self._setup_network_with_mock_protocol(connect_size=2,
    #                                                number_of_leaves=number_of_leaves
    #                                                )
    #     protocol.reset()

    #     # ensure that the port of the SwitchProtocol triggers
    #     qubit = ns.qubits.qubit.Qubit(name='qubit')
    #     port = protocol.node.qmemory.ports['qin0']
    #     port.tx_input(qubit)

    #     ns.sim_run()

    #     # check that the SwitchProtocol has not triggered
    #     self.assertEqual(protocol.number_of_noticed_new_link_arrivals, 1)

    # def test_triggered_by_qubit_arrival_twice_simultaneously(self):
    #     for is_simultaneously in [True, False]:
    #         ns.sim_reset()
    #         number_of_leaves = 3
    #         protocol, leaf_nodes = \
    #             self._setup_network_with_mock_protocol(connect_size=2,
    #                                                    number_of_leaves=number_of_leaves
    #                                                    )
    #         protocol.reset()

    #         # ensure that the port of the SwitchProtocol triggers...
    #         # ...once
    #         [qubit] = ns.qubits.qubitapi.create_qubits(1)
    #         port = protocol.node.qmemory.ports['qin0']
    #         port.tx_input(qubit)

    #         if not is_simultaneously:
    #             ns.sim_run(100)

    #         # ...twice
    #         [qubit] = ns.qubits.qubitapi.create_qubits(1)
    #         port = protocol.node.qmemory.ports['qin1']
    #         port.tx_input(qubit)
    #         ns.sim_run(2e7)

    #         # check that the SwitchProtocol has not triggered
    #         self.assertEqual(protocol.number_of_noticed_new_link_arrivals, 2)


if __name__ == "__main__":
    unittest.main()
