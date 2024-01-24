import unittest
import numpy as np
from netsquid_qswitch.aux_functions import (get_ghz_state, vardoyan_distance_to_rate, vardoyan_rate_to_distance)


class TestAuxilliaryFunctions(unittest.TestCase):

    def test_get_ghz_state(self):
        s = 1 / np.sqrt(2)

        # GHZ state on 2 qubits
        expected_ket_array = np.array([[s], [0], [0], [s]])
        computed_ket_array = get_ghz_state(number_of_qubits=2)
        self.assertTrue(np.array_equal(computed_ket_array, expected_ket_array))

        # GHZ state on 3 qubits
        expected_ket_array = np.array([[s], [0], [0], [0], [0], [0], [0], [s]])
        computed_ket_array = get_ghz_state(number_of_qubits=3)
        self.assertTrue(np.array_equal(computed_ket_array, expected_ket_array))

        # GHZ state on 4 qubits
        expected_ket_array = np.array([[s], [0], [0], [0], [0], [0], [0],
                                       [0], [0], [0], [0], [0], [0], [0], [0],
                                       [s]])
        computed_ket_array = get_ghz_state(number_of_qubits=4)
        self.assertTrue(np.array_equal(computed_ket_array, expected_ket_array))

    def test_vardoyan_rate_computation(self):
        for distance in [0.01, 0.1, 1, 10, 100]:
            computed_rate = vardoyan_distance_to_rate(distance)
            computed_distance = vardoyan_rate_to_distance(computed_rate)
            self.assertTrue(np.isclose(computed_distance, distance))

        # Vardoyan et al. state "mu=1 (corresponding to 100 km long links)"
        # where mu is the rate and is provided in units of Mega-ebits per
        # second. We test for this value
        computed_rate = vardoyan_distance_to_rate(distance=100)
        self.assertTrue(np.isclose(computed_rate, 10 ** 6))


if __name__ == "__main__":
    unittest.main()
