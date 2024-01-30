"""Quantum circuits that are used in the quantum switch protocols."""
from netsquid.components import QuantumProgram
from netsquid.components.instructions import (INSTR_MEASURE, INSTR_SWAP, Instruction, INSTR_CNOT, INSTR_H)
import netsquid.qubits.operators as ops


def create_quantum_circuit_for_connect(connect_size=2):
    """
    Returns a quantum circuit that performs a measurement
    in the GHZ-basis. When applied to one part of many EPR
    pairs each, this produces a multipartite entangled state
    on the other qubits in the EPR pairs.

    Parameters
    ----------
    connect_size : int
        The dimension of the GHZ-states (e.g. `connect_size=2`
        corresponds to a measurement in the Bell basis).

    Returns
    -------
    :obj:`netsquid.components.qprogram.QuantumProgram`
    """

    class GHZMeasureProgram(QuantumProgram):
        """Performs a measurement in the GHZ basis.
        """

        default_num_qubits = connect_size

        @classmethod
        def get_correction_operators(cls, outcomes):
            """
            Parameters
            ----------
            outcomes : list of int

            Returns
            -------
            list of :obj:`netsquid.qubits.operators.Operator`
            """
            if len(outcomes) != cls.default_num_qubits:
                raise ValueError("Number of outcomes should equal" +
                                 "number of measured qubits")
            control_qubit_correction = ops.Z if outcomes[0] == 1 else ops.I
            target_qubit_corrections = []
            for outcome in outcomes[1:]:
                target_qubit_correction = ops.X if outcome == 1 else ops.I
                target_qubit_corrections.append(target_qubit_correction)
            return [control_qubit_correction] + target_qubit_corrections

        def program(self):
            qubits = self.get_qubit_indices(connect_size)
            control_qubit = qubits[0]
            target_qubits = qubits[1:]
            for target_qubit in target_qubits:
                self.apply(INSTR_CNOT, [control_qubit, target_qubit])
            self.apply(INSTR_H, control_qubit)
            for qubit_index, qubit in enumerate(qubits):
                self.apply(INSTR_MEASURE,
                           qubit,
                           output_key='m{}'.format(qubit_index),
                           inplace=False)
            yield self.run()

    return GHZMeasureProgram()


class MoveProgram(QuantumProgram):
    """
    Quantum circuit for a local swap, i.e. a 'move' of a qubit
    from one memory position to another.
    """

    default_num_qubits = 2

    def program(self):
        qubits = self.get_qubit_indices(2)
        self.apply(INSTR_SWAP, qubits)
        yield self.run()


class MeasureProgram(QuantumProgram):
    """
    Quantum circuit for single-qubit measurement.
    """
    OUTCOME_KEY = "m"
    default_num_qubits = 1

    def __init__(self, measure_instruction=None):
        super().__init__()
        self.measure_instruction = measure_instruction

    @property
    def measure_instruction(self):
        """
        :obj:`netsquid.components.instructions.Instruction`
        """
        if self._measure_instruction is None:
            raise ValueError("No measure instruction provided")
        return self._measure_instruction

    @measure_instruction.setter
    def measure_instruction(self, val):
        """
        :obj:`netsquid.components.instructions.Instruction`
        """
        if not isinstance(val, Instruction):
            raise TypeError("{} is not of type Instruction".format(val))
        self._measure_instruction = val

    def program(self):
        qubit = self.get_qubit_indices(1)[0]
        self.apply(self.measure_instruction,
                   [qubit],
                   # NOTE using qubit_mapping=[qubit] here leads to an error
                   inplace=False,
                   output_key=MeasureProgram.OUTCOME_KEY)
        yield self.run()
