import unittest
import netsquid as ns
from netsquid_qswitch.memory_management import MemoryManager


class TestMemoryManager(unittest.TestCase):

    def setUp(self):
        ns.sim_reset()
        self.mm = MemoryManager(num_positions=10, node_name='dummy_node_name')

    def test_add_fresh_link(self):
        # add a link
        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name="A",
                               fresh_link_ID=23)

        # there should be an error if the same link is added twice
        with self.assertRaises(ValueError):
            self.mm.add_fresh_link(mem_pos=0,
                                   remote_node_name="B",
                                   fresh_link_ID=3)

        # there should also be an error if another link with the same remote
        # node and the same link ID is added...
        with self.assertRaises(ValueError):
            self.mm.add_fresh_link(mem_pos=1,
                                   remote_node_name="A",
                                   fresh_link_ID=23)

        # but no error is the same link ID but a different node...
        self.mm.add_fresh_link(mem_pos=1,
                               remote_node_name="B",
                               fresh_link_ID=23)

        # and no error either if the same node but a different link ID
        self.mm.add_fresh_link(mem_pos=2,
                               remote_node_name="A",
                               fresh_link_ID=24)

    def test_get_link(self):
        # add a link ...
        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name="G",
                               fresh_link_ID=23)

        # ... and check if we can retrieve that information
        link = self.mm.get_link(mem_pos=0)
        self.assertEqual(link.remote_node_name, "G")
        self.assertEqual(link.link_ID, 23)

        # there should be an error when retrieving information about
        # memory position 1 since there is no link at that position
        with self.assertRaises(ValueError):
            self.mm.get_link(mem_pos=1)

    def test_remove_link(self):
        self.mm.add_fresh_link(mem_pos=2,
                               remote_node_name="R",
                               fresh_link_ID=12)
        self.mm.add_fresh_link(mem_pos=5,
                               remote_node_name="R",
                               fresh_link_ID=13)
        self.mm.remove_link(mem_pos=2)

        with self.assertRaises(ValueError):
            self.mm.get_link(mem_pos=2)

        link = self.mm.get_link(mem_pos=5)
        self.assertEqual(link.remote_node_name, "R")
        self.assertEqual(link.link_ID, 13)

    def test_move_link(self):
        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name="A",
                               fresh_link_ID=10)
        self.mm.move_link(old_mem_pos=0, new_mem_pos=1)
        link = self.mm.get_link(mem_pos=1)
        self.assertEqual(link.remote_node_name, "A")
        self.assertEqual(link.link_ID, 10)
        with self.assertRaises(ValueError):
            self.mm.get_link(mem_pos=0)

    def test_get_free_mem_positions(self):
        [mem_pos] = self.mm.get_free_mem_positions(number_of_positions=1)
        self.assertEqual(mem_pos, 0)
        with self.assertRaises(ValueError):
            self.mm.get_link(mem_pos)

        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name="A",
                               fresh_link_ID=12)
        [mem_pos] = self.mm.get_free_mem_positions(number_of_positions=1)
        self.assertEqual(mem_pos, 1)
        with self.assertRaises(ValueError):
            self.mm.get_link(mem_pos)

    def test_can_connect(self):

        # if there are no links, no 'connect' operation
        # can be applied
        connectable_positions = \
            self.mm.get_connectable_positions(number_of_qubits=2)
        self.assertTrue(connectable_positions is None)

        # if there is only a single link, while 2 are needed, no 'connect'
        # can be applied either
        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name="A",
                               fresh_link_ID=0)
        connectable_positions = \
            self.mm.get_connectable_positions(number_of_qubits=2)
        self.assertTrue(connectable_positions is None)

        # if there are two links with the same node, then no 'connect'
        # can be applied
        self.mm.reset()
        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name="A",
                               fresh_link_ID=0)
        self.mm.add_fresh_link(mem_pos=1,
                               remote_node_name="A",
                               fresh_link_ID=1)
        connectable_positions = \
            self.mm.get_connectable_positions(number_of_qubits=2)
        self.assertTrue(connectable_positions is None)

        # if two links are available with different nodes, then a connect can
        # be applied
        self.mm.reset()
        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name="A",
                               fresh_link_ID=0)
        self.mm.add_fresh_link(mem_pos=1,
                               remote_node_name="B",
                               fresh_link_ID=1)
        connectable_positions = \
            self.mm.get_connectable_positions(number_of_qubits=2)
        self.assertEqual(set(connectable_positions), set([0, 1]))

        # if multiple links are available, then the Oldest Link Entanglement
        # First rule should be applied
        self.mm.reset()
        ns.sim_reset()
        self.mm.add_fresh_link(mem_pos=1,
                               remote_node_name="A",
                               fresh_link_ID=0)
        ns.sim_run(10)
        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name="A",
                               fresh_link_ID=1)
        ns.sim_run(20)
        self.mm.add_fresh_link(mem_pos=3,
                               remote_node_name="B",
                               fresh_link_ID=2)
        ns.sim_run(30)
        self.mm.add_fresh_link(mem_pos=2,
                               remote_node_name="B",
                               fresh_link_ID=3)
        ns.sim_run(40)
        connectable_positions = \
            self.mm.get_connectable_positions(number_of_qubits=2)
        self.assertEqual(connectable_positions, [1, 3])

        # adding links with another node should not matter, as long as
        # if that link was produced at a later time
        ns.sim_run(50)
        self.mm.add_fresh_link(mem_pos=4,
                               remote_node_name="C",
                               fresh_link_ID=3)
        connectable_positions = \
            self.mm.get_connectable_positions(number_of_qubits=2)
        self.assertEqual(connectable_positions, [1, 3])

    def test_apply_buffer(self):

        # case: add two links and set buffer to zero, so that both links will be removed
        ns.sim_reset()
        remote_node_name = "A"
        ns.sim_run(3)
        self.mm.add_fresh_link(mem_pos=0,
                               remote_node_name=remote_node_name,
                               fresh_link_ID=23)
        ns.sim_run(5)
        self.mm.add_fresh_link(mem_pos=1,
                               remote_node_name=remote_node_name,
                               fresh_link_ID=42)

        positions_to_discard = \
            self.mm.positions_to_discard_following_buffer_by_remote_node_name(
                remote_node_name=remote_node_name,
                buffer_size=0)
        self.assertEqual(len(positions_to_discard), 2)

        # case: add two links and set buffer to one, so that only the earliest will be removed
        self.mm.reset()
        ns.sim_reset()
        remote_node_name = "A"
        ns.sim_run(3)
        oldest_link = self.mm.add_fresh_link(mem_pos=0,
                                             remote_node_name=remote_node_name,
                                             fresh_link_ID=23)

        ns.sim_run(5)
        self.mm.add_fresh_link(mem_pos=1,
                               remote_node_name=remote_node_name,
                               fresh_link_ID=42)

        positions_to_discard = \
            self.mm.positions_to_discard_following_buffer_by_remote_node_name(
                remote_node_name=remote_node_name,
                buffer_size=1)
        position_of_oldest_link = \
            self.mm.get_position(remote_node_name=remote_node_name, link_ID=oldest_link.link_ID)
        self.assertEqual(positions_to_discard, [position_of_oldest_link])


if __name__ == "__main__":
    unittest.main()
