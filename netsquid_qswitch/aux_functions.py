"""Methods for getting the analytical expressions as presented in
    G. Vardoyan, S. Guha, P. Nain, and D. Towsley,
    "On the stochastic analysis of a quantum entanglement switch,"
    SIGMETRICS Perform. Eval. Rev., vol. 47, pp. 27–29, Dec. 2019
    (arXiv: https://arxiv.org/abs/1903.04420).
"""
import numpy as np


def distance_to_rate(distance, loss_parameter, loss_coefficient,
                     attempt_duration):
    r"""Computes the entanglement generation rate over a given distance
    of glass fibre, computed as
    :math:`\text{attemptduration} / (\text{lossparameter}
    \cdot \text{transmissivity}).`

    Parameters
    ----------
    distance : float
        Distance [km]
    loss_parameter : float
    loss_coefficient : float
        [dB / km]
    attempt_duration : float
        Duration of a single entanglement generation attempt [s]

    Returns
    -------
    float
        Entanglement generation rate [1/s]
    """
    # transmissivity between one end of the link and midpoint station
    transmissivity = 10 ** (-0.1 * loss_coefficient * distance/2)
    return (2 * loss_parameter * transmissivity) / attempt_duration


def rate_to_distance(rate, loss_parameter, loss_coefficient,
                     attempt_duration):
    """
    Converts a given entanglement generation rate to the distance
    of the glass fibre that was used to generate entanglement.

    Parameters
    ----------
    rate : float
        Entanglement generation rate [Hz]
    loss_parameter : float
    loss_coefficient : float
        [dB / km]
    attempt_duration : float
        Duration of a single entanglement generation attempt [s]

    Returns
    -------
    float
        Distance [km]

    Notes
    -----

      * This function is the inverse of
        :meth:`quantum_switch.delaymodels.distance_to_rate`.
      * In Vardoyan et al., the rate is given in Mega-ebits per second,
        whereas this function returns units of Herz (1 ebit per second).
    """
    return -10 * np.log(attempt_duration * rate / loss_parameter / 2) /\
        (np.log(10) * loss_coefficient / 2)


def get_ghz_state(number_of_qubits):
    """
    Returns
    -------
    :obj:`numpy.array`
    """
    s = 1 / np.sqrt(2)
    list_ket = [[s]] + \
               [[0]] * (2 ** number_of_qubits - 2) + \
               [[s]]
    return np.array(list_ket)


###########################################
# Analytical results from Vardoyan et al. #
###########################################


# Constants from Vardoyan et al.,
# "On the stochastic analysis of quantum entanglement switch ",
# section VII 'Numerical Observations'.
# (https://arxiv.org/abs/1903.04420).
VARDOYAN_LOSS_COEFFICIENT = 0.2  # [dB/km], called 'beta'
VARDOYAN_ATTEMPT_DURATION = 10 ** (-9)  # [s], called 'tau'
VARDOYAN_LOSS_PARAMETER = 0.1  # called 'c' on p. 10 of paper


def vardoyan_distance_to_rate(distance):
    """Computes the entanglement generation rate over a given distance
    of glass fibre. Follows the numbers used by Vardoyan et al.,
    "On the stochastic analysis of quantum entanglement switch ",
    section VII 'Numerical Observations'.

    Parameters
    ----------
    distance : float
        Distance [km]

    Returns
    -------
    float
        Entanglement generation rate [Hz]

    Note
    ----
    In Vardoyan et al., the rate is given in Mega-ebits per second,
    whereas this function returns units of Herz (1 ebit per second).
    """
    return distance_to_rate(distance=distance,
                            loss_parameter=VARDOYAN_LOSS_PARAMETER,
                            loss_coefficient=VARDOYAN_LOSS_COEFFICIENT,
                            attempt_duration=VARDOYAN_ATTEMPT_DURATION)


def vardoyan_rate_to_distance(rate):
    """
    Converts a given entanglement generation rate to the distance
    of the glass fibre that was used to generate entanglement.
    Follows the numbers used by Vardoyan et al.,
    "On the stochastic analysis of quantum entanglement switch ",
    section VII 'Numerical Observations'.

    Parameters
    ----------
    rate : float
        Entanglement generation rate [Hz]

    Returns
    -------
    float
        Distance [km]
    """
    return rate_to_distance(rate=rate,
                            loss_parameter=VARDOYAN_LOSS_PARAMETER,
                            loss_coefficient=VARDOYAN_LOSS_COEFFICIENT,
                            attempt_duration=VARDOYAN_ATTEMPT_DURATION)


def analytical_capacity_with_ghz_dimension_2(mus, B, alpha, q):
    """Analytically computes the capacity of the quantum switch
    in case it produces Bell pairs (i.e. GHZ-states on 2 qubits).
    Taken from Vardoyan et al.,
    "On the stochastic analysis of quantum entanglement switch ".

    Parameters
    ----------
    mus : list of float
        List of the rate switch-user for each user.
    B : int
        Buffer size
    alpha : float
        Decoherence parameter
    q : float
        Success probability of the 'connect' operation.

    Returns
    -------
    float
    """
    def _pi0_capacity_heter_decoh_buffer_connsize2(mus, B, alpha):
        gamma = sum(mus)
        total_sum = 0
        for mu in mus:
            for j in [x + 1 for x in range(B)]:
                prod = 1
                for i in [y + 1 for y in range(j)]:
                    prod *= mu / (gamma - mu + i * alpha)
                total_sum += prod
        return 1 / (1 + total_sum)

    gamma = sum(mus)

    total_sum = 0
    for mu in mus:
        for j in [x + 1 for x in range(B)]:
            prod = 1
            for i in [y + 1 for y in range(j)]:
                prod *= mu / (gamma - mu + i * alpha)
            total_sum += prod * (gamma - mu)

    pi0 = _pi0_capacity_heter_decoh_buffer_connsize2(mus=mus, B=B, alpha=alpha)
    return q * pi0 * (total_sum)


def analytical_capacity_in_homogeneous_noiseless_case(q, mu, k, n):
    """Analytically computes the capacity of the quantum switch
    in the 'homogeneous' case (entanglement-generation rate
    between switch and user is identical for all users), in the absence
    of the Vardoyan-et-al. decoherence model and with unbounded buffer size.
    Taken from Prop. 1 in Vardoyan et al.,
    "On the stochastic analysis of quantum entanglement switch ".

    Parameters
    ----------
    q : float
        Success probability of the 'connect' operation.
    mu : float
        Rate at which switch-user entanglement is generated.
    k : int
        Number of users.
    n : Dimension of the GHZ state that is produced between the users.

    Returns
    -------
    float
    """
    return q * mu * k / n
