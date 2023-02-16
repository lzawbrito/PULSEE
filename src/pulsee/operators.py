import numpy as np
from scipy.constants import Planck, Boltzmann
from qutip import Qobj, rand_herm, rand_dm


def exp_diagonalize(q):
    """
    Diagonalizes the given operator, and exponentiates the diagonal eigenvalue
    matrix. 
    
    Parameters:
    -----------
    - q: Qobj

    Returns:
    --------
    A list of Qobjs including the eigenvector matrix, the diagonal eigenvalue 
    matrix, and the exponent of the diagonal eigenvalue matrix. 
    """
    evals, evects = q.eigenstates()
    d = np.zeros((len(evals), len(evals)), dtype=np.complex128)
    dexp = np.zeros((len(evals), len(evals)), dtype=np.complex128)

    i = 0
    for e in evals:
        d[i, i] = e
        dexp[i, i] = np.exp(e)
        i += 1

    d = Qobj(d)        
    dexp = Qobj(dexp)        
    u = Qobj(np.concatenate(evects, axis=1))

    return u, d, dexp


def changed_picture(q, h_change_of_picture, time, invert=False):
    """
    Casts the operator either in a new picture generated by the Operator h_change_of_picture or
    back to the Schroedinger picture, according to the parameter invert.

    Parameters
    ----------
    - q: Qobj
    - h_change_of_picture: Qobj
                                Operator which generates the change to the new picture. Typically,
                                this operator is a term of the Hamiltonian (measured in MHz).
    - time: float
                Instant of evaluation of the operator in the new picture, expressed in microseconds.
    - invert: bool
                    When it is False, the owner Operator object is assumed to be expressed in the
                    Schroedinger picture and is converted into the new one.
                    When it is True, the owner object is thought in the new picture and the
                    opposite operation is performed.

    Returns
    -------
    A new Operator object equivalent to the owner object but expressed in a different picture.
    """
    t = Qobj(-1j * 2 * np.pi * h_change_of_picture * time)
    if invert: t = -t
    return q.transform(t.expm())

      
def unit_trace(q):
    """
    Returns a boolean which expresses whether the trace of the operator is equal to 1,
    within a relative error tolerance of 10<sup>-6</sup>.
    Parameters
    ----------
    - q: Qobj

    Returns
    -------
    True, when unit trace is verified.
    
    False, when unit trace is not verified.
    """
    return np.isclose(q.tr(), 1, rtol=1e-6)

      
def positivity(q):
    """
    Returns a boolean which expresses whether the operator is a positive operator,
     i.e. its matrix has only non-negative eigenvalues (taking the 0 with an error margin of 10^(-10)).

    Parameters
    ----------
    - q: Qobj

    Returns
    -------
    True, when positivity is verified.
    
    False, when positivity is not verified.
    """
    eigenvalues = q.eigenenergies()
    return np.all(np.real(eigenvalues) >= -1e-10)


def free_evolution(q, static_hamiltonian, time):
    """
    Returns the density matrix represented by the owner object evolved through a
    time interval time under the action of the stationary Hamiltonian static_hamiltonian.
    
    Parameters
    ----------
    - static_hamiltonian: Observable or in general a hermitian Operator
                            Time-independent Hamiltonian of the system, in MHz.
    - time: float
                Duration of the evolution, expressed in microseconds.
    
    Returns
    -------
    A DensityMatrix object representing the evolved state converted to rads.
    """
    iHt = 1j * 2 * np.pi * static_hamiltonian * time 
    evolved_dm = q.transform(iHt.expm())
    return evolved_dm


def random_operator(d):
    """
    Returns a randomly generated operator object of dimensions d.
    
    Parameters
    ----------
    - d: int
         Dimensions of the Operator to be generated.
           
    Returns
    -------
    An Operator object whose matrix is d-dimensional and has random complex elements
     with real and imaginary parts in the half-open interval [-10., 10.].
    """
    round_elements = np.vectorize(round)
    real_part = round_elements(20 * (np.random.rand(d, d) -1/2), 2)
    imaginary_part = 1j * round_elements(20 * (np.random.rand(d, d)-1/2), 2)
    random_array = real_part + imaginary_part
    return Qobj(random_array)


def random_observable(d):
    """
    Returns a randomly generated observable of dimensions d. Wrapper for QuTiP's
    `rand_herm()`.

  
    Parameters
    ----------
    - d: int
         Dimensions of the Observable to be generated.
          
    Returns
    -------
    An Observable object whose matrix is d-dimensional and has random complex elements with real
    and imaginary parts in the half-open interval [-10., 10.].
    """
    return rand_herm(d)


def random_density_matrix(d):
    """
    Returns a randomly generated density matrix of dimensions d. Wrapper for 
    QuTiP's `rand_dm()`.
    
    Parameters
    ----------
    
    - d: int
         Dimensions of the DensityMatrix to be generated.
    
    Returns
    -------
    A DensityMatrix object whose matrix is d-dimensional and has randomly generated eigenvalues.
    """
    return rand_dm(d)


def commutator(A, B):
    """
    Returns the commutator of operators A and B.
    
    Parameters
    ----------
    - A, B: Operator
    
    Returns
    -------
    An Operator representing the commutator of A and B.
    """
    return A * B - B * A


def magnus_expansion_1st_term(h, time_step):
    """
    Returns the 1st order term of the Magnus expansion of the passed time-dependent Hamiltonian.
    
    Parameters
    ----------
    - h: np.ndarray of Observable
         Time-dependent Hamiltonian (expressed in MHz). Technically, an array of Observable
          objects which correspond to the Hamiltonian evaluated at successive instants of time.
          The start and end points of the array are taken as the extremes of integration 0 and t;
    - time_step: float 
                 Time difference between adjacent points of the array h, expressed in microseconds.
    
    Returns
    -------
    An adimensional Operator object resulting from the integral of h over the whole array size,
     multiplied by -1j*2*np.pi. The integration is carried out through the traditional trapezoidal rule.
    """
    integral = h[0]
    for t in range(len(h) - 2):
        integral = integral + 2 * h[t + 1]
    integral = (integral + h[-1]) * (time_step) / 2
    magnus_1st_term = Qobj(-1j * 2 * np.pi * integral)
    return magnus_1st_term


def magnus_expansion_2nd_term(h, time_step):
    """
    Returns the 2nd order term of the Magnus expansion of the passed time-dependent Hamiltonian.
    
    Parameters
    ----------
    - h: np.ndarray of Observable
         Time-dependent Hamiltonian (expressed in MHz). Technically, an array of Observable objects
         which correspond to the Hamiltonian evaluated at successive instants of time. The start and
          end points of the array are taken as the extremes of integration 0 and t;
    - time_step: float
                 Time difference between adjacent points of the array h, expressed in microseconds.
    
    Returns
    -------
    An adimensional Operator object representing the 2nd order Magnus term of the Hamiltonian,
    calculated applying Commutator to the elements in h and summing them.
    """
    integral = (h[0]*0)
    for t1 in range(len(h)-1):
        for t2 in range(t1+1):
            integral = integral + (commutator(h[t1], h[t2]))*(time_step ** 2)
    magnus_2nd_term = ((2 * np.pi) ** 2) * Qobj(-(1 / 2) * integral)
    return magnus_2nd_term


def magnus_expansion_3rd_term(h, time_step):
    """
    Returns the 3rd order term of the Magnus expansion of the passed time-dependent Hamiltonian.
    
    Parameters
    ----------
    
    - h: np.ndarray of Observable
         Time-dependent Hamiltonian (expressed in MHz). Technically, an array of Observable objects
         which correspond to the Hamiltonian evaluated at successive instants of time. The start and end
         points of the array are taken as the extremes of integration 0 and t;
    - time_step: float
                 Time difference between adjacent points of the array h, expressed in microseconds.
    
    Returns
    -------
    An adimensional Operator object representing the 3rd order Magnus term of the Hamiltonian,
    calculated applying nested Commutator to the elements in h and summing them.
    """
    integral = (h[0] * 0)
    for t1 in range(len(h) - 1):
        for t2 in range(t1 + 1):
            for t3 in range(t2 + 1):
                integral = integral + \
                           ((commutator(h[t1], commutator(h[t2], h[t3])) + \
                             commutator(h[t3], commutator(h[t2], h[t1])))) * (time_step ** 3)
    magnus_3rd_term = Qobj((1j / 6) * ((2 * np.pi) ** 3) * integral)
    return magnus_3rd_term


def canonical_density_matrix(hamiltonian, temperature):
    """
    Returns the density matrix of a canonical ensemble of quantum systems at thermal equilibrium.
    
    Parameters
    ----------
    - hamiltonian: Operator
                   Hamiltonian of the system at equilibrium, expressed in MHz.
    - temperature: positive float
                   Temperature of the system in kelvin.

    Returns
    -------
    A DensityMatrix object which embodies the canonical density matrix.
    
    Raises
    ------
    ValueError, if temperature is negative or equal to zero.
    """
    if temperature <= 0:
        raise ValueError("The temperature must take a positive value")
    
    # don't forget we need to multiply factor of 2 * np.pi back into the hamiltonian
    exponent = - ((Planck/Boltzmann) * hamiltonian * 2 * np.pi * 1e6) / temperature
    numerator = exponent.expm()
    canonical_dm = numerator.unit()
    return canonical_dm








