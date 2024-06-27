"""Protocols for both the center node (switch node) and the leaf nodes in a star-shaped network."""
import abc
import netsquid as ns
from netsquid.components import Port
from netsquid.nodes import Node
from netsquid.protocols import NodeProtocol, Protocol
from netsquid.components.instructions import INSTR_MEASURE
from netsquid_qswitch.memory_management import LinkIDCreator, MemoryManager, LinkGroup
import netsquid_qswitch.quantum_programs as switch_qprog
from netsquid_qswitch.aux_functions import get_ghz_state
from netsquid_qswitch.network import SWITCH_NODE_NAME, LEAF_NODE_BASENAME

# naming conventions
SWITCH_PROTOCOL_NAME = "switch_protocol"
LEAF_PROTOCOL_BASENAME = "leaf_protocol_"
DATA_PROTOCOL_NAME = 'data_protocol'


class StarNodeProtocol(abc.ABC, NodeProtocol):
    """
    Base class for a protocol for any node
    in the star topology network.

    Parameters
    ----------
    node
    name: str

    Note
    ----
    The input parameter `node` should hold a QuantumMemory, accessible as
    `node.qmemory`.
    """
    def __init__(self, node, name, memorymanager="default"):
        super().__init__(node=node, name=name)
        self._set_memorymanager(memorymanager=memorymanager, node_name=node.name)
        self._link_ID_creator = LinkIDCreator()
        self._move_program = switch_qprog.MoveProgram()
        self._measure_program = switch_qprog.MeasureProgram(INSTR_MEASURE)
        self._outcomes = []
        self._set_reserved_positions()
        self._set_not_reserved_positions()

    def _set_reserved_positions(self):
        self._reserved_positions = []

    def _set_not_reserved_positions(self):
        self._not_reserved_positions = \
            list(set(range(self.node.qmemory.num_positions)) - set(self._reserved_positions))

    @property
    def reserved_positions(self):
        """List of indices of memory positions that are reserved,
        e.g. because a quantum channel is connected to it.
        """
        return self._reserved_positions

    @property
    def not_reserved_positions(self):
        """List of indices of memory positions that are not reserved,
        i.e. they are safe to use as target of a 'move' operation.
        """
        return self._not_reserved_positions

    def _set_memorymanager(self, node_name, memorymanager="default"):
        if memorymanager == "default":
            self._memorymanager = \
                MemoryManager(node_name, num_positions=self.node.qmemory.num_positions,
                              decoherence_rate=0)
        else:
            if not isinstance(memorymanager, MemoryManager):
                raise TypeError("Memorymanager of StarNodeProtocol should be" +
                                "of type MemoryManager")
            self._memorymanager = memorymanager

    @property
    def memorymanager(self):
        return self._memorymanager

    @property
    def link_ID_creator(self):
        return self._link_ID_creator

    def reset(self):
        super().reset()
        self._memorymanager.reset()
        self._link_ID_creator.reset()
        self._outcomes = []

    def _perform_move(self, old_position, new_position):
        """
        Parameters
        ----------
        old_position : int
        new_position : int

        Returns
        -------
        EventCondition
        """
        qubit_mapping = [old_position, new_position]
        self._memorymanager.move_link(old_position, new_position)
        self.node.qmemory.execute_program(self._move_program,
                                          qubit_mapping=qubit_mapping)
        return ns.EventExpression(
            source=self.node.qmemory,
            event_type=self.node.qmemory.evtype_program_done)

    def _perform_connect(self, positions):
        """
        Parameters
        ----------
        positions : list of int

        Returns
        -------
        list of EventCondition
        """
        if len(positions) != self._connect_program.default_num_qubits:
            raise Exception
        for mem_pos in positions:
            self._memorymanager.remove_link(mem_pos)
        self.node.qmemory.execute_program(self._connect_program,
                                          qubit_mapping=positions)
        return ns.EventExpression(
            source=self.node.qmemory,
            event_type=self.node.qmemory.evtype_program_done)

    def _add_fresh_link(self, remote_node_name, mem_pos):
        """
        Parameters
        ----------
        remote_node_name : str
        mem_pos : int
        """
        fresh_link_ID = \
            self._link_ID_creator.get_fresh_link_ID(remote_node_name)
        self._memorymanager.add_fresh_link(mem_pos=mem_pos,
                                           remote_node_name=remote_node_name,
                                           fresh_link_ID=fresh_link_ID)

    def _get_necessary_move_positions(self):
        """Determine local swaps on all qubits which are on positions
        that should be freed for new incoming qubits

        Returns
        -------
        list of (int, int)
            List of (position-before-move, intended-position-after-move)
        """
        moving_positions = [mem_pos for mem_pos in self._reserved_positions
                            if mem_pos in self._memorymanager.positions_in_use]
        ret = []
        possible_target_positions = self._not_reserved_positions
        free_positions = \
            self._memorymanager.get_free_mem_positions(possible_mem_pos=possible_target_positions,
                                                       number_of_positions=len(moving_positions))
        for old_pos, new_pos in zip(moving_positions, free_positions):
            ret.append((old_pos, new_pos))
        return ret

    def _get_necessary_moves(self):
        """Perform local swaps on all qubits which are on positions
        that should be freed for new incoming qubits

        Parameters
        ----------
        reserved_positions : list of int
        possible_target_positions : list of int

        Returns
        -------
        list of EventCondition
        """
        move_positions = self._get_necessary_move_positions()
        return (self._perform_move(old_pos, new_pos) for (old_pos, new_pos)
                in move_positions)

    @property
    def outcomes(self):
        """ list of int """
        return self._outcomes

    def _perform_necessary_moves_and_wait_until_finished(self):
        necessary_moves = self._get_necessary_moves()
        for move in necessary_moves:
            yield move

    def _measure_and_wait_until_finished(self, pos):
        self.node.qmemory.execute_program(self._measure_program,
                                          qubit_mapping=[pos])
        yield ns.EventExpression(source=self.node.qmemory,
                                 event_type=self.node.qmemory.evtype_program_done)
        self._memorymanager.remove_link(mem_pos=pos)
        outcome = self._measure_program.output[self._measure_program.OUTCOME_KEY]
        self.node.qmemory.pop(pos)
        return outcome

    def _get_leaf_protocol_by_node_name(self, node_name):
        for leaf_protocol in self._leaf_protocols:
            if leaf_protocol.node.name == node_name:
                return leaf_protocol
        raise ValueError

    def _apply_buffer(self):
        # to be overridden
        pass


class LeafProtocol(StarNodeProtocol):
    """
    Protocol for a leaf node: each incoming qubit on the quantum
    connection with the switch is measured directly.
    """
    MEASURE_DIRECTLY = False

    def __init__(self, node, name, buffer_size, switch_node):
        """
        Parameters
        ----------
        node : :obj:`netsquid.nodes.node.Node`
            Node at which the protocol works.
        name : str
            Name of the protocol.
        buffer_size : int
        """
        super().__init__(node=node, name=name)
        self._buffer_size = buffer_size
        self._switch_node = switch_node

    def run(self):
        """Loops over the following events:

        - wait for an incoming link on the first qubit position
        - record the link in the MemoryManager
        - act on the link: either measure or move it to free up the
          first qubit position
        """
        while True:

            yield self._wait_for_incoming_link()
            self._record_incoming_link()

            if self.MEASURE_DIRECTLY:
                outcome = self._measure_and_wait_until_finished(pos=0)
                self._outcomes.append(outcome)
            else:
                for move in self._perform_necessary_moves_and_wait_until_finished():
                    yield move

    def _wait_for_incoming_link(self):
        port = self.node.qmemory.ports["qin0"]
        # somehow, replacing the line below by port.notify_next_input = True does not work
        port.notify_all_input = True
        return ns.EventExpression(source=port)

    def _record_incoming_link(self):
        self._add_fresh_link(remote_node_name=SWITCH_NODE_NAME,
                             mem_pos=0)

    def _set_reserved_positions(self):
        self._reserved_positions = [0]

    def _apply_buffer(self):
        pass


class SwitchProtocol(StarNodeProtocol):
    """
    Protocol for the centre node (switch).
    """
    FINCONN_SIGN_LABEL = "FINISHED_CONNECT"

    def __init__(self, node, name, leaf_nodes, buffer_size, leaf_protocols=None, connect_size=2, server_node_name=None):
        """
        Parameters
        ----------
        node : :obj:`netsquid.nodes.node.Node`
            Node at which the protocol works.
        name : str
            Name of the protocol.
        leaf_nodes: list of :obj:`netsquid.nodes.node.Node`
        connect_size : int
            Number of qubits that the `connect` operation acts upon.
        buffer_size : int
        """
        self._connect_size = connect_size
        self._buffer_size = buffer_size
        self._leaf_nodes = leaf_nodes
        self._server_node_name = server_node_name
        self._leaf_protocols = leaf_protocols
        super().__init__(node=node, name=name)

        self._connect_program = switch_qprog.create_quantum_circuit_for_connect(connect_size)
        self.add_signal(label=self.FINCONN_SIGN_LABEL)

    def _set_reserved_positions(self):
        number_of_leaves = len(self._leaf_nodes)
        self._reserved_positions = list(range(number_of_leaves))

    def _set_not_reserved_positions(self):
        # all memory positions to which no quantum channel
        # automatically deposits qubits
        self._not_reserved_positions = \
            list(set(range(self.node.qmemory.num_positions)) - set(self.reserved_positions))

    def run(self):
        """
        The protocol currently performs the following actions, in order:

        1. wait until a :obj:`netsquid.components.component.Port` object
           signals that it has an input
        2. once a port has signalled, check if there are qubits in the
           QuantumProcessor that sit on 'reservered' positions, i.e. the
           memory positions to which a quantum channel directly spits out
           qubits. If so, then perform the 'move' (local swap) operation on
           all of these qubits to move them to a free position that is not
           a reserved position.
        3. check if a `Connect` operation can be performed. If so, then perform
           the operation and start again at step 2. If not, go back to step 1.
        """
        for port in self.node.qmemory.ports.values():
            port.notify_all_input = True

        arrival_event_expression = ns.EventExpression(event_type=Port.evtype_input)
        while True:

            yield arrival_event_expression

            self._add_new_links_to_memory_manager_by_position_in_use()
            # The better alternative to adding links based on which memory positions
            # are in use would be the following: find all ports which fired
            # from the attribute 'triggered_events' of the arrival_event_expression.
            # However, this does not work in case two links arrive at precisely the
            # same time, in which case the first port fires, followed by the yielding on
            # of 'move' and 'connect' operations below. As a consequence, the other
            # ports which fired are now forgotten and when this while-loop will start
            # again, the 'yield arrival_event_expression' will not trigger again...

            for operation in self._operations_after_new_link_arrival():
                yield operation

    def _operations_after_new_link_arrival(self):

        # remove all links that have timed out
        # NOTE this assumes that the operations after this take 0 time!
        self._memorymanager.apply_timeout()

        self._apply_buffer()

        # perform move operations
        for move in self._perform_necessary_moves_and_wait_until_finished():
            yield move

        # perform all possible 'connect' operations
        linkgroups = []

        while self._can_perform_connect():
            positions = self._get_connectable_positions()
            links = [self._memorymanager.get_link(pos) for pos in positions]
            yield self._perform_connect(positions)
            outcomes = [self._connect_program.output["m{}".format(idx)][0]
                        for idx in range(self._connect_size)]
            linkgroup = LinkGroup(links)
            linkgroup.correction_operators = self._connect_program.get_correction_operators(outcomes)
            linkgroups.append(linkgroup)

        self.send_signal(signal_label=SwitchProtocol.FINCONN_SIGN_LABEL,
                         result=linkgroups)

    def _add_new_links_to_memory_manager_by_position_in_use(self):
        leaf_indices = [leaf_index for leaf_index in range(len(self._leaf_nodes))
                        if self.node.qmemory.mem_positions[leaf_index].in_use]
        for leaf_index in leaf_indices:
            self._add_new_link_to_memory_manager(leaf_index)

    def _add_new_links_to_memory_manager_by_triggered_ports(self, arrival_event_expression):
        leaf_node_names = [event.source.component.name for event in arrival_event_expression.triggered_events]
        for leaf_name, leaf_index in zip(leaf_node_names, range(len(leaf_node_names))):
            self._add_fresh_link(remote_node_name=leaf_name, mem_pos=leaf_index)

    def _add_new_link_to_memory_manager(self, leaf_index):
        leaf_name = self._leaf_nodes[leaf_index].name
        self._add_fresh_link(remote_node_name=leaf_name, mem_pos=leaf_index)

    def _does_port_belong_to_given_leaf_node(self, port, leaf_index):
        """
        Returns
        -------
        bool
        """
        qprocessor = port.component
        return self.node.qmemory == qprocessor and "qin{}".format(leaf_index) in port.name

    def _apply_buffer(self):
        for leaf_node in [node for node in self._leaf_nodes]:
            self._apply_buffer_with_leaf_by_name(leaf_node=leaf_node)

    def _apply_buffer_with_leaf_by_name(self, leaf_node):

        positions_to_discard_in_switch_manager = \
            self._memorymanager.positions_to_discard_following_buffer_by_remote_node_name(
                remote_node_name=leaf_node.name,
                buffer_size=self._buffer_size[leaf_node.name])
        for pos in positions_to_discard_in_switch_manager:
            self._memorymanager.remove_link(mem_pos=pos)
            self.node.qmemory.pop(pos)

        leaf_protocol = self._get_leaf_protocol_by_node_name(leaf_node.name)
        positions_to_discard_in_leaf_manager = \
            leaf_protocol.memorymanager.positions_to_discard_following_buffer_by_remote_node_name(
                remote_node_name=self.node.name,
                buffer_size=self._buffer_size[leaf_node.name])
        for pos in positions_to_discard_in_leaf_manager:
            leaf_protocol.memorymanager.remove_link(mem_pos=pos)
            leaf_node.qmemory.pop(pos)

    def _get_connectable_positions(self):
        """
        Returns
        -------
        list of int
            Memory positions on which a 'connect' operation can be applied to result into
            a GHZ state on the leaf nodes.
        """
        return self._memorymanager.get_connectable_positions(
            number_of_qubits=self._connect_size,
            server_node_name=self._server_node_name)

    def _can_perform_connect(self):
        """
        Returns
        -------
        bool
            Whether the node holds enough entanglement with sufficiently many distinct
            leaf nodes to perform the 'connect' operation
        """
        connectable_positions = \
            self._memorymanager.get_connectable_positions(
                number_of_qubits=self._connect_size,
                server_node_name=self._server_node_name)
        return not (connectable_positions is None)


class DataCollectProtocol(NodeProtocol):

    EVTYPE_COLLECT_FIDELITY = ns.EventType("COL_FID", "collect fidelity")

    def __init__(self, node, name, switch_protocol, leaf_protocols,
                 connect_size, delay_until_collect):
        super().__init__(node=node,
                         name=name)
        self._switch_protocol = switch_protocol
        self._leaf_protocols = leaf_protocols
        self._leaf_qmemories = [p.node.qmemory for p in leaf_protocols]
        self.add_signal(label=SwitchProtocol.FINCONN_SIGN_LABEL)
        self._ghz_state = get_ghz_state(connect_size)
        self._delay_until_collect = delay_until_collect
        self._collect_handler = ns.EventHandler(self._collect_fidelity_and_nodes_involved)
        self._helper_entity = ns.Entity()

    def _get_leaf_protocol_by_node_name(self, node_name):
        for leaf_protocol in self._leaf_protocols:
            if leaf_protocol.node.name == node_name:
                return leaf_protocol
        raise ValueError

    def _get_fidelity_and_nodes_involved(self, linkgroup, pop=True):
        # get all qubits needed to find fidelity
        qubits = []
        nodes_involved = []
        for link in linkgroup.links:
            leaf_protocol = self._get_leaf_protocol_by_node_name(link.remote_node_name)
            nodes_involved.append(link.remote_node_name)
            memorymanager = leaf_protocol.memorymanager
            pos = memorymanager.get_position(
                remote_node_name=SWITCH_NODE_NAME,
                link_ID=link.link_ID)
            memorymanager.remove_link(pos)
            if pop:
                qubit = leaf_protocol.node.qmemory.pop(pos)
            else:
                qubit = leaf_protocol.node.qmemory.peek(pos)
            qubits.append(qubit[0])
        # apply correction operators
        for ix, qubit in enumerate(qubits):
            ns.qubits.qubitapi.operate(qubit, linkgroup.correction_operators[ix])
        return ns.qubits.qubitapi.fidelity(qubits, self._ghz_state, squared=True), nodes_involved

    def _collect_fidelity_and_nodes_involved(self, event):
        linkgroup = self._linkgroups_to_be_collected.pop(0)
        fidelity, nodes_involved = self._get_fidelity_and_nodes_involved(linkgroup)
        self.fidelities.append(fidelity)
        self.nodes_involved.append(nodes_involved)

    def start(self):
        super().start()
        self.fidelities = []
        self.nodes_involved = []
        self._linkgroups_to_be_collected = []
        self._helper_entity._wait(self._collect_handler,
                                  event_type=self.EVTYPE_COLLECT_FIDELITY)

    def stop(self):
        super().stop()
        self._helper_entity._dismiss(self._collect_handler)

    def run(self):
        while True:
            label = SwitchProtocol.FINCONN_SIGN_LABEL
            yield self.await_signal(sender=self._switch_protocol,
                                    signal_label=label)
            linkgroups = self._switch_protocol.get_signal_result(label=label)
            for linkgroup in linkgroups:
                if linkgroup:
                    self._linkgroups_to_be_collected.append(linkgroup)
                    self._schedule_after(self._delay_until_collect,
                                         self.EVTYPE_COLLECT_FIDELITY)


def setup_protocols(network, connect_size, num_positions,
                    max_channel_delay, buffer_size, decoherence_rate=0, server_node_name=None,
                    memorymanager='default'):
    """
    Returns a "mother protocol" to which the switch protocol and a protocol
    for each of the leaves are added.

    Returns
    -------
    :obj:`netsquid.protocols.protocol.Protocol`
    """
    switch_node = network.subcomponents[SWITCH_NODE_NAME]
    leaf_nodes = [n for n in network.subcomponents.values()
                  if isinstance(n, Node) and LEAF_NODE_BASENAME in n.name]

    _buffer_size = dict()
    for i, leaf_node in enumerate(leaf_nodes):
        _buffer_size[leaf_node.name] = \
            buffer_size[i] if isinstance(buffer_size, list) else buffer_size
    protocol = Protocol()
    leaf_protocols = []
    for leaf_node in leaf_nodes:
        subprotocol = \
            LeafProtocol(node=leaf_node,
                         name=LEAF_PROTOCOL_BASENAME + leaf_node.name,
                         buffer_size=_buffer_size[leaf_node.name],
                         switch_node=switch_node)
        leaf_protocols.append(subprotocol)
        protocol.add_subprotocol(subprotocol)

    switch_protocol = SwitchProtocol(
        node=switch_node,
        name=SWITCH_PROTOCOL_NAME,
        leaf_nodes=leaf_nodes,
        buffer_size=_buffer_size,
        connect_size=connect_size,
        server_node_name=server_node_name,
        leaf_protocols=leaf_protocols)

    protocol.add_subprotocol(switch_protocol)

    data_collect_protocol = DataCollectProtocol(node=switch_node,
                                                name=DATA_PROTOCOL_NAME,
                                                switch_protocol=switch_protocol,
                                                leaf_protocols=leaf_protocols,
                                                connect_size=connect_size,
                                                delay_until_collect=max_channel_delay)
    protocol.add_subprotocol(data_collect_protocol)

    return protocol
