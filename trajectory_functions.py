# This file contains the function definitions for some trajectory-trajectory
# and trajectory-system interactions.

import numpy as np
import scipy.integrate as integ
from Trajectory import Trajectory
from System import System

def swap_tf(object):
    if hasattr(object, 'modes'):
        return np.fft.irfft(object.modes, axis = 1)
    elif type(object) == np.ndarray:
        return np.fft.rfft(object, axis = 1)
    else:
        raise TypeError("Input is not of correct type!")

def traj_grad(traj):
    """
        This function calculates the gradient vectors of a given trajectory and
        returns it as an instance of the Trajectory class. The algorithm used
        is based off of the RFFT

        Parameters
        ----------
        traj: Trajectory object
            the trajectory which we will calculate the gradient for
        
        Returns
        -------
        grad: Trajectory object
            the gradient of the input trajectory
    """
    # initialise array for new modes
    new_modes = np.zeros(traj.shape, dtype = np.complex)

    # loop over time and multiply modes by modifiers
    for k in range(traj.shape[1]):
        new_modes[:, k] = 1j*k*traj.modes[:, k]
    
    # force zero mode if symmetric
    if traj.shape[1] % 2 == 0:
        new_modes[:, traj.shape[1]//2] = 0

    return Trajectory(new_modes)

def traj_inner_prod(traj1, traj2):
    """
        This function calculates the Euclidean inner product of two
        trajectories at each location along their domains, s.

        Parameters
        ----------
        traj1: Trajectory object
            the first trajectory in the inner product
        traj2: Trajectory object
            the second trajectory in the inner product
        
        Returns
        -------
        traj_prod: Trajectory object
            the inner product of the two trajectories at each location along
            their domains, s
    """
    # initialise arrays
    prod_modes = np.zeros([1, traj1.shape[1]], dtype = complex)
    # prod_modes = np.zeros([1, 2*(traj1.shape[1] - 1)], dtype = complex)
    # traj1_full = np.zeros([traj1.shape[0], 2*(traj1.shape[1] - 1)], dtype = complex)
    # traj2_full = np.zeros([traj2.shape[0], 2*(traj2.shape[1] - 1)], dtype = complex)

    # nested loop to perform convolution
    for n in range(traj1.shape[1]):
        for m in range(1 - traj1.shape[1], traj1.shape[1]):
            if m < 0:
                vec1 = np.conj(traj1[:, -m])
            else:
                vec1 = traj1[:, m]
            if n - m < traj1.shape[1]:
                if n - m < 0:
                    vec2 = np.conj(traj2[:, m - n])
                else:
                    vec2 = traj2[:, n - m]
            else:
                vec2 = np.zeros(traj1.shape[0])
            prod_modes[:, n] += np.dot(vec1, vec2)
    
    # normalise
    prod_modes = prod_modes/(2*(traj1.shape[1] - 1))

    # populate full trajectory modes
    # for i in range(1 - traj1.shape[1], traj1.shape[1]):
    #     if i < 0:
    #         traj1_full[:, i] = np.conj(traj1[:, i])
    #         traj2_full[:, i] = np.conj(traj2[:, i])
    #     else:
    #         traj1_full[:, i] = traj1[:, i]
    #         traj2_full[:, i] = traj2[:, i]

    # # use perform convolution
    # for i in range(traj1.shape[0]):
    #     prod_modes[0, :] += np.convolve(traj1_full[i, :], traj2_full[i, :], mode = 'same')
    
    # return Trajectory(prod_modes[0, traj1.shape[1] - 1:])
    return(Trajectory(prod_modes))

def traj_response(traj, func):
    """
        This function evaluates the response over the domain of a given
        trajectory due to a given dyanmical system.

        Parameters
        ----------
        traj: Trajectory object
            the trajectory over which the response will be evaluated
        func: function
            the function that defines the response at each location along the
            trajectory, must be a function that inputs a vector and outputs a
            vector of the same size
        
        Returns
        -------
        response_traj: Trajectory object
            the response at each location of the trajectory, given as an
            instance of the Trajectory class
    """
    # convert trajectory to time domain
    curve = swap_tf(traj)

    # evaluate response in time domain
    for i in range(np.shape(curve)[1]):
        curve[:, i] = func(curve[:, i])

    # convert back to frequency domain and return
    return Trajectory(swap_tf(curve))

def jacob_init(traj, sys, if_transp = False):
    """
        This function initialises a jacobian function that returns the jacobian
        matrix for the given system at each location along the domain of the
        trajectory (through the indexing of the array, i).

        Parameters
        ----------
        traj: Trajectory object
            the trajectory over which the jacobian matrix will be evaluated
        sys: System object
            the system for which the jacobian matrix is for
        
        Returns
        -------
        jacob: function
            the function that returns the jacobian matrix for a given index of
            the array defining the trajectory in state-space
    """
    def jacobian(i):
        """
            This function returns the jacobian matrix for a dynamical system at
            a specified location along a trajectory through the associated
            state-space, indexed by i.

            Parameters
            ----------
            i: positive integer
                the discretised location along the trajectory in state-space
            
            Returns
            -------
            jacobian_matrix: numpy array
                the 2D numpy array for the jacobian of a dynamical system given
                at a specified location of the trajectory
        """
        # convert to time domain
        curve = swap_tf(traj)

        # test for input
        if i%1 != 0:
            raise TypeError("Inputs are not of the correct type!")
        if i >= np.shape(curve)[1]:
            raise ValueError("Input index is too large!")

        # make sure index is integer
        i = int(i)

        # state at index
        state = curve[:, i]

        # the jocobian for that state
        if if_transp == True:
            return np.transpose(sys.jacobian(state))
        elif if_transp == False:
            return sys.jacobian(state)
    return jacobian
