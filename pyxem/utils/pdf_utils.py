# -*- coding: utf-8 -*-
# Copyright 2017-2019 The pyXem developers
#
# This file is part of pyXem.
#
# pyXem is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyXem is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyXem.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np

def normalise_pdf_signal_to_max(z, index_min, *args, **kwargs):
    """Used by hs.map in the PairDistributionFunction1D to normalise the signal
    to the maximum in the signal.

    Parameters
    ----------
    z : np.array
        A pair distribution function np.array to be transformed
    index_min : int
        The minimum scattering vector s to be considered, given as the lowest
        index in the array to consider for finding the present maximum.
        This is to prevent the effect of large oscillations at r=0.
    *args:
        Arguments to be passed to map().
    **kwargs:
        Keyword arguments to be passed to map().
    """

    max_val = np.max(z[index_min:])
    return np.divide(z,max_val)

def mask_from_pattern(z, pattern, *args, **kwargs):
    """Used by hs.map in the ReducedIntensityGenerator to mask using a
    background pattern.

    Parameters
    ----------
    z : np.array
        A np.array to be transformed
    pattern : np.array
        A numpy array consisting of 0s and 1s in a single line profile
        of the same resolution (same number of pixels) as the signal.
        1s in the signal are kept. 0s are masked (into zeroes)
    mask_threshold : int or float
        An integer or float threshold. Any pixel in the
        mask_pattern with lower intensity is kept, any with
        higher or equal is set to zero.
    *args:
        Arguments to be passed to map().
    **kwargs:
        Keyword arguments to be passed to map().
    """
    return z*pattern

def scattering_to_signal_lobato(elements, fracs, N, C, s_size, s_scale):
    """ A function to override HyperSpy's as_signal method in a fit, as that
    method fails for large signals.

    Fit to Lobato & Van Dyck (2014)

    Parameters
    ----------
    elements: list of str
        A list of elements present (by symbol).
    fracs: list of float
        A list of fraction of the respective elements. Should sum to 1.
    N : array of float
        The "slope" of the fit.
    C : array of float
        An additive constant to the fit. Supplied as array.
    s_size : int
        Size of fitted signal in the signal dimension (in pixels)/
    s_scale : float
        Calibration factor of scattering factor s = 1/d in reciprocal
        angstroms per pixel.
    """
    params = []

    for e in elements:
        params.append(ATOMIC_SCATTERING_PARAMS_LOBATO[e])

    x_size = N.data.shape[0]
    y_size = N.data.shape[1]

    sum_squares = np.zeros((x_size, y_size, s_size))
    square_sum = np.zeros((x_size, y_size, s_size))

    x = np.arange(s_size) * s_scale

    for i, element in enumerate(params):
        fi = np.zeros(s_size)
        for n in range(len(element)):  # 5 parameters per element
            fi += (element[n][0] * (2 + element[n][1] * np.square(2 * x))
                   * np.divide(1, np.square(1 + element[n][1] *
                                                np.square(2 * x))))
        elem_frac = fracs[i]
        sum_squares += np.square(fi) * elem_frac
        square_sum += fi * elem_frac

    signal = N.data.reshape(x_size, y_size, 1) * sum_squares + C.data.reshape(x_size, y_size, 1)
    square_sum = N.data.reshape(x_size, y_size, 1) * square_sum

    return signal, square_sum



def scattering_to_signal_xtables(elements, fracs, N, C, s_size, s_scale):
    """ A function to override HyperSpy's as_signal method in a fit, as that
    method fails for large signals.

    Fit to International Tables Vol. C, table 4.3.2.3

    Parameters
    ----------
    elements: list of str
        A list of elements present (by symbol).
    fracs: list of float
        A list of fraction of the respective elements. Should sum to 1.
    N : array of float
        The "slope" of the fit.
    C : array of float
        An additive constant to the fit. Supplied as array.
    s_size : int
        Size of fitted signal in the signal dimension (in pixels)/
    s_scale : float
        Calibration factor of scattering factor s = 1/d in reciprocal
        angstroms per pixel.
    """
    params = []

    for e in elements:
        params.append(ATOMIC_SCATTERING_PARAMS[e])

    x_size = N.data.shape[0]
    y_size = N.data.shape[1]

    sum_squares = np.zeros((x_size, y_size, s_size))
    square_sum = np.zeros((x_size, y_size, s_size))

    x = np.arange(s_size) * s_scale

    for i, element in enumerate(params):
        fi = np.zeros(s_size)
        for n in range(len(element)):  # 5 parameters per element
            fi += element[n][0] * np.exp(-element[n][1] * (np.square(x)))
        elem_frac = fracs[i]
        sum_squares += np.square(fi) * elem_frac
        square_sum += fi * elem_frac

    signal = N.data.reshape(x_size, y_size, 1) * sum_squares + C.data.reshape(x_size, y_size, 1)
    square_sum = N.data.reshape(x_size, y_size, 1) * square_sum

    return signal, square_sum

def damp_ri_exponential(z, b, s_scale, s_size, *args, **kwargs):
    """Used by hs.map in the ReducedIntensity1D to damp the reduced
    intensity signal to reduce noise in the high s region by a factor of
    exp(-b*(s^2)), where b is the damping parameter.

    Parameters
    ----------
    z : np.array
        A reduced intensity np.array to be transformed.
    b : float
        The damping parameter.
    scale : float
        The scattering vector calibation of the reduced intensity array.
    size : int
        The size of the reduced intensity signal. (in pixels)
    *args:
        Arguments to be passed to map().
    **kwargs:
        Keyword arguments to be passed to map().
    """

    scattering_axis = s_scale * np.arange(s_size, dtype='float64')
    damping_term = np.exp(-b * np.square(scattering_axis))
    return z*damping_term

def damp_ri_lorch(z, s_max, s_scale, s_size, *args, **kwargs):
    """Used by hs.map in the ReducedIntensity1D to damp the reduced
    intensity signal to reduce noise in the high s region by a factor of
    sin(s*delta) / (s*delta), where delta = pi / s_max. (from Lorch 1969).

    Parameters
    ----------
    z : np.array
        A reduced intensity np.array to be transformed.
    s_max : float
        The maximum s value to be used for transformation to PDF.
    scale : float
        The scattering vector calibation of the reduced intensity array.
    size : int
        The size of the reduced intensity signal. (in pixels)
    *args:
        Arguments to be passed to map().
    **kwargs:
        Keyword arguments to be passed to map().
    """

    delta = np.pi / s_max

    scattering_axis = s_scale * np.arange(s_size, dtype='float64')
    damping_term = np.sin(delta * scattering_axis) / (delta * scattering_axis)
    damping_term = np.nan_to_num(damping_term)
    return z*damping_term

def damp_ri_updated_lorch(z, s_max, s_scale, s_size, *args, **kwargs):
    """Used by hs.map in the ReducedIntensity1D to damp the reduced
    intensity signal to reduce noise in the high s region by a factor of
    3 / (s*delta)^3 (sin(s*delta)-s*delta(cos(s*delta))),
    where delta = pi / s_max.

    From "Extracting the pair distribution function from white-beam X-ray
    total scattering data", Soper & Barney, (2011).

    Parameters
    ----------
    z : np.array
        A reduced intensity np.array to be transformed.
    s_max : float
        The damping parameter, which need not be the maximum scattering
        vector s to be used for the PDF transform.
    scale : float
        The scattering vector calibation of the reduced intensity array.
    size : int
        The size of the reduced intensity signal. (in pixels)
    *args:
        Arguments to be passed to map().
    **kwargs:
        Keyword arguments to be passed to map().
    """

    delta = np.pi / s_max

    scattering_axis = s_scale * np.arange(s_size, dtype='float64')
    exponent_array = 3 * np.ones(scattering_axis.shape)
    cubic_array = np.power(scattering_axis, exponent_array)
    multiplicative_term = np.divide(3 / (delta**3), cubic_array)
    sine_term = (np.sin(delta * scattering_axis)
                 - delta * scattering_axis * np.cos(delta * scattering_axis))

    damping_term = multiplicative_term * sine_term
    damping_term = np.nan_to_num(damping_term)
    return z*damping_term

def damp_ri_low_q_region_erfc(z, scale, offset, s_scale, s_size, *args,
                                **kwargs):
    """Used by hs.map in the ReducedIntensity1D to damp the reduced
    intensity signal in the low q region as a correction to central beam
    effects. The reduced intensity profile is damped by
    (erf(scale * s - offset) + 1) / 2

    Parameters
    ----------
    z : np.array
        A reduced intensity np.array to be transformed.
    scale : float
        A scalar multiplier for s in the error function
    offset : float
        A scalar offset affecting the error function.
    scale : float
        The scattering vector calibation of the reduced intensity array.
    size : int
        The size of the reduced intensity signal. (in pixels)
    *args:
        Arguments to be passed to map().
    **kwargs:
        Keyword arguments to be passed to map().
    """

    scattering_axis = s_scale * np.arange(s_size, dtype='float64')

    damping_term = (special.erf(scattering_axis * scale - offset) + 1) / 2
    return z*damping_term
