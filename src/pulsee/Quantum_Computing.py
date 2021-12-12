from .Operators import Observable, Operator, Density_Matrix
import numpy as np 
from .exceptions.Quantum_Computing import MatrixRepresentationError


def adjoint(a):
	"""
	Convenience method for quickly taking conjugate transpose of array.

	Params
	------
	- `a`: an array
	
	Returns
	------
	- the conjugate transpose of a.
	"""

	return np.array(np.matrix(a).getH())


def normalize(a):
	"""
	Normalize an array. 

	Params
	------
	- `a`: an array 
	
	Returns
	------
	A divided by its norm. 
	"""
	a = np.array(a)
	norm = np.linalg.norm(a) 
	return a / norm 


# Define quantum gates
class NGate(Operator):
	"""
	Quantum n-gate as defined in Scherer pg. 169: a unitary operator U: H^n → 
	H^n. If n = 1, one has a unary gate; if n = 2, one has a binary gate. 
	n specified by the given qubit space. 

	Params
	------
	- `x`: the array representing this operator. 
	- `qs`: the qubit space on which this operator/gate acts. 
	"""
	def __init__(self, x, qs):
		self._qs = qs 
		self._n = qs.n
		x = np.array(x)
		if not np.shape(x) == (2 ** self._n, 2 ** self._n):
			raise MatrixRepresentationError(f'Input array shape {np.shape(x)} invalid for ' \
				+ f'qubit space H^{self._n}')
		if np.array_equal(np.matmul(adjoint(x), x), np.identity(self._n)):
			raise MatrixRepresentationError('Input array must be unitary.')

		super().__init__(x)
	
	def apply(self, state):
		assert self._n == state.n
		return np.matmul(self.matrix, state.matrix)


class QubitState:
	def __init__(self, qs, matrix):
		"""
		Params
		------
		- `qs`: the qubit space of which this qubit state is an element.
		- `matrix`: an 1 by n matrix, where n is the number of factors of the 
		            (possibly composite) qubit space of which this qubit state 
					is an element.
		"""
		if not np.log2(np.shape(matrix)[0]) == qs.n:
			raise MatrixRepresentationError(f'Improper array shape ' + \
							 f'{np.shape(matrix[0])} for matrix representation ' + \
							 f'of {qs.n}-dimensional qubit space.')
		self._matrix = matrix
		self._qs = qs 

	@property 
	def matrix(self): 
		return self._matrix 


	@property
	def density_matrix(self):
		onb = self._qs.onb_matrices() 

		density_matrix = np.zeros((len(onb), len(onb)))
		for i in range(0, len(onb)):
			for j in range(0, len(onb)): 
				density_matrix[i][j] = np.dot(np.conjugate(onb[i]), self.matrix) \
									 * np.dot(np.conjugate(self.matrix), onb[j])
								
		# Density_Matrix:
		return Density_Matrix(density_matrix)


class CompositeQubitSpace:
	"""
	Implementation of an n-fold tensor product of qubit spaces (as defined in 
	Scherer 85) 
	"""
	def __init__(self, n: int): 
		"""
		Params
		------
		- n: number of qubit spaces of which this is a composition. 
		"""
		if n <= 0: 
			raise ValueError(f'Invalid qubit space composition: {n}.')	
		self._n = n 
	
	def basis_from_indices(self, indices):
		"""
		Generate the matrix representation of the basis ket of the desired 
		composition of basis qubits. E.g., if given `[0, 1, 0]` generates the 
		state ket |010⟩ as a matrix. 

		Params
		------
		- `indices`: iterable of one of {0, 1}. States of qubits of which this 
					 basis is a composition. 
		
		Returns
		------
		An ndarray representing the matrix representation of this composite 
		state ket. 
		"""
		# Ensure that no index is greater than 1 
		if not np.all([0 <= i <= 1 for i in indices]):
			raise MatrixRepresentationError(f'{indices} has one index greater than 1.')
		if not len(indices) == self._n:
			raise MatrixRepresentationError(f'Number of indices in {indices} does not match ' + \
							 f'dimension of composite qubit space: {self._n}.')
		basis = np.zeros((2 ** self._n))
		k = 1
		indices.reverse()
		i = indices[0]
		for ind in indices[1:]: 
			i += (ind) * 2 ** k 
			k += 1 
		basis[i] = 1
		return basis

	def onb_matrices(self):
		"""
		Returns
		------
		A list containing the orthonormal basis as matrix representations. 
		"""

		matrices = [] 
		def add_bit(bit, vec):
			new_vec = vec + [bit]
			if len(new_vec) == self.n: 
				matrices.append(self.basis_from_indices(new_vec))
			else: 
				add_bit(0, new_vec)
				add_bit(1, new_vec)

		add_bit(0, [])
		add_bit(1, [])
		return matrices

	def __eq__(self, other):
		if isinstance(other, CompositeQubitSpace):
			return self.n == other.n 
		return False 

	@property
	def n(self): 
		return self._n


class QubitSpace(CompositeQubitSpace):
	"""
	Implementation of a qubit space as specified by Scherer: a two-dimensional 
	Hilbert space equipped with an eigenbasis |0⟩ and |1⟩ and a corresponding 
	observable A such that A|0⟩ = 1 |0⟩ and A|1⟩ = - 1 |1⟩.
	"""
	def __init__(self):
		super().__init__(1)
		# Define base qubits 
		self._base_zero = super().basis_from_indices([0])
		self._base_one = super().basis_from_indices([1])


	# Defined observable for this qubit
	_observable = Observable(np.array([[1, 0], [0, -1]]))


	def make_state(self, alpha=None, beta=None, coeffs=None):
		"""
		TODO 
		- prioritizes angles; if one of angles is not defined uses coefficients.
		- normalizes coefficients. 
		"""
		if alpha is not None and beta is not None: 
			matrix = np.cos(beta / 2) * self._base_zero + np.sin(beta / 2) \
					* np.exp(1j * alpha) * self._base_one 
			return QubitState(self, matrix)

		elif coeffs is not None: 
			if len(coeffs) != 2: 
				raise MatrixRepresentationError
			
			# Normalize coefficients
			coeffs = normalize(coeffs)

			matrix = coeffs[0] * self._base_zero + coeffs[1] * self._base_one
			return QubitState(self, matrix)

		else: 
			raise MatrixRepresentationError("State vector must be created using either " \
						   + "coefficients or polar and azimuthal angles.")


# Define quantum gates.
HADAMARD = NGate((1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]]), QubitSpace())
CNOT = NGate(np.array([[1, 0, 0, 0], 
					   [0, 1, 0, 0], 
					   [0, 0, 0, 1], 
					   [0, 0, 1, 0]]), 
			 CompositeQubitSpace(2))
