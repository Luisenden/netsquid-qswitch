"""Physical components of the switch network and tools for setting them up."""
import netsquid as ns
from netsquid.nodes import Connection, Node
from netsquid.components import (PhysicalInstruction, Component, QSource, SourceStatus, QuantumChannel,
                                 QuantumProcessor, Clock, ClassicalFibre)
from netsquid.components.instructions import (
    INSTR_MEASURE, INSTR_MEASURE_X, INSTR_SWAP, INSTR_CNOT, INSTR_H,
    INSTR_MEASURE_BELL)
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.components.models import DelayModel
from netsquid.qubits.state_sampler import StateSampler


# naming conventions
SWITCH_NODE_NAME = "switch_node"
LEAF_NODE_BASENAME = "leaf_node_"  # leaf nodes have names X1, X2, etc where X=LEAF_NODE_BASENAME


def _create_qconnection(leaf_node_name, distance_from_centre, single_hop_state,
                        single_hop_timing_model, bright_state_population):
    """
    A quantum connection between the switch node and a leaf node.
    The connection continuously produces entangled pairs of qubits
    and spits out one to each side (internally, this is done by a
    :obj:`netsquid.components.components.qsource.QSource`).

    Parameters
    ----------
    name : str
    distance_from_centre: float
    single_hop_state : :obj:`netsquid.qubits.qstate.QState`
        The two-qubit state that is produced by the connection.
    single_hop_timing_model :  :obj:`netsquid.components.delaymodel.DelayModel`
        The timing at which the two-qubit states are produced, one after
        another.

    Returns
    -------
    :obj:`netsquid.nodes.connection.Connection`

    Note
    ----
    The ports of the connection are identified as

      * A: to the switch node
      * B: to the leaf node
    """

    # quantum connection
    state_sampler = StateSampler(qs_reprs=[single_hop_state],
                                 probabilities=[1])

    qsource = QSource("qsource{}".format(leaf_node_name),
                      state_sampler=state_sampler,
                      num_ports=2,
                      timing_model=single_hop_timing_model,
                      status=SourceStatus.EXTERNAL)
    clock = Clock(name="clock",
                  start_delay=single_hop_timing_model(),
                  models={"timing_model": single_hop_timing_model})
    clock.ports["cout"].connect(qsource.ports["trigger"])

    qchannel_M2leaf = QuantumChannel(
        name="qchannel_M2leaf{}".format(leaf_node_name),
        length=distance_from_centre / 2.,
        models={"delay_model": None,
                "quantum_noise_model": DepolarNoiseModel(4/3*bright_state_population, time_independent=True)})
    qchannel_M2switch = QuantumChannel(
        name="qchannel_M2switch{}".format(leaf_node_name),
        length=distance_from_centre / 2.,
        models={"delay_model": None,
                "quantum_noise_model": None})

    # classical_connection
    cchannel = ClassicalFibre("cchannel2leaf{}".format(leaf_node_name),
                              length=distance_from_centre)

    # wrap the two quantum channels and the quantum source into
    # a single connection component
    connection = Connection("qchann{}".format(leaf_node_name))
    connection.add_subcomponent(clock)
    connection.add_subcomponent(qsource)
    connection.add_subcomponent(qchannel_M2leaf)
    connection.add_subcomponent(qchannel_M2switch)
    connection.add_subcomponent(cchannel)

    # link the subcomponents internally
    qsource.ports["qout0"].connect(qchannel_M2switch.ports["send"])
    qsource.ports["qout1"].connect(qchannel_M2leaf.ports["send"])
    qchannel_M2leaf.ports["recv"].forward_output(connection.ports["A"])
    qchannel_M2switch.ports["recv"].forward_output(connection.ports["B"])

    return connection


def _create_quantumprocessor(name, num_positions, T2):
    """
    Parameters
    ----------
    name : str
    num_positions : int

    Returns
    -------
    :obj:`netsquid.components.qprocessor.QuantumProcessor`
    """
    physical_instructions = [
        PhysicalInstruction(INSTR_MEASURE, duration=0, q_noise_model=None),
        PhysicalInstruction(INSTR_MEASURE_X, duration=0, q_noise_model=None),
        PhysicalInstruction(INSTR_SWAP, duration=0, q_nosie_model=None),
        PhysicalInstruction(INSTR_CNOT, duration=0, q_nosie_model=None),
        PhysicalInstruction(INSTR_H, duration=0, q_nosie_model=None),
        PhysicalInstruction(INSTR_MEASURE_BELL, duration=0,
                            q_noise_model=None)
    ]

    qprocessor = QuantumProcessor(name=name,
                                  num_positions=num_positions,
                                  fallback_to_nonphysical=False,
                                  mem_noise_models=[None] * num_positions,
                                  phys_instructions=physical_instructions)
    return qprocessor


def setup_network(number_of_leaves, distances_from_centre,
                  single_hop_state, single_hop_timing_models, bright_state_population,
                  num_positions, T2):
    """
    Constructs a star topology network of a single centre node (the switch) and
    multiple leaf nodes.

    Parameters
    ----------
    number_of_leaf_nodes : int
    distances_from_centre : list of int
    single_hop_state : :obj:`netsquid.qubits.qstate.QState`
    single_hop_timing_models : list of
        :obj:`netsquid.components.models.delaymodels.DelayModel`
    num_positions : int
        Number of qubits in each quantum processor (one for each node)

    Returns
    -------
    :obj:`netsquid.components.component.Component`
    """
    network = Component("star_network")
    leaf_nodes = [Node("{}{}".format(LEAF_NODE_BASENAME, ix))
                  for ix in range(number_of_leaves)]
    port_names = ["port_qconn2qproc_{}".format(ix)
                  for ix in range(number_of_leaves)]
    switch_node = Node(SWITCH_NODE_NAME, port_names=port_names)

    # add quantumprocessor to each node
    for node in [switch_node] + leaf_nodes:
        qprocessor = _create_quantumprocessor(node.name, num_positions, T2)
        node.add_subcomponent(qprocessor)
        network.add_subcomponent(node)

    # add quantum connections between switch and each of the leaves
    for leaf_ix, leaf_node in enumerate(leaf_nodes):
        qconnection = _create_qconnection(
            leaf_node_name=str(leaf_ix),
            distance_from_centre=distances_from_centre[leaf_ix],
            single_hop_state=single_hop_state,
            single_hop_timing_model=single_hop_timing_models[leaf_ix],
            bright_state_population=bright_state_population[leaf_ix])

        network.add_subcomponent(qconnection)

    return network


class ExponentialDelayModel(DelayModel):
    r"""
    Delay model where the delay follows the exponential
    distribution with mean 1/rate.

    Parameters
    ----------
    rate : float
        Characteristic parameter (rate parameter) of the exponential
        distribution with mean 1/rate [Hz].
    """

    def __init__(self, rate, **kwargs):
        super().__init__(**kwargs)
        if rate <= 0:
            raise ValueError("Rate parameter of exponential" +
                             "distribution should be strictly positive")
        self._rate = rate * 10 ** (-9)
        ns.util.simtools.set_random_state(42)

    def get_mean(self, **kwargs):
        return 1. / self._rate

    def get_std(self, **kwargs):
        return 1. / (self._rate ** 2)

    def generate_delay(self, **kwargs):
        return self.rng.exponential(scale=self.get_mean())
