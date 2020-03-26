# -*- coding: utf-8 -*-
# Copyright 2017-2020 The pyXem developers
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

from hyperspy.api import interactive


class CommonDiffraction:
    @staticmethod
    def _get_sum_signal(signal, out_signal_axes=None):
        out = signal.sum(signal.axes_manager.signal_axes)
        if out_signal_axes is None:
            out_signal_axes = list(
                np.arange(min(signal.axes_manager.navigation_dimension, 2))
            )
        if len(out_signal_axes) > signal.axes_manager.navigation_dimension:
            raise ValueError(
                "The length of 'out_signal_axes' can't be longer"
                "than the navigation dimension of the signal."
            )
        # Reset signal to default Signal1D or Signal2D
        out.set_signal_type("")
        return out.transpose(out_signal_axes)

    def plot_integrated_intensity(self, roi, out_signal_axes=None, **kwargs):
        """Interactively plots the integrated intensity over the scattering
        range defined by the roi.

        Parameters
        ----------
        roi : float
            Any interactive ROI detailed in HyperSpy.
        out_signal_axes : None, iterable of int or string
            Specify which navigation axes to use as signal axes in the virtual
            image. If None, the two first navigation axis are used.
        **kwargs:
            Keyword arguments to be passed to the `plot` method of the virtual
            image.

        Examples
        --------
        .. code-block:: python

            >>> # For 1D diffraction signal, we can use a SpanROI
            >>> roi = hs.roi.SpanROI(left=1., right=2.)
            >>> dp.plot_integrated_intensity(roi)

        .. code-block:: python

            >>> # For 2D diffraction signal,we can use a CircleROI
            >>> roi = hs.roi.CircleROI(3, 3, 5)
            >>> dp.plot_integrated_intensity(roi)

        """
        # Plot signal when necessary
        if self._plot is None or not self._plot.is_active:
            self.plot()

        # Get the sliced signal from the roi
        sliced_signal = roi.interactive(self, axes=self.axes_manager.signal_axes)

        # Create an output signal for the virtual dark-field calculation.
        out = self._get_sum_signal(self, out_signal_axes)
        out.metadata.General.title = "Integrated intensity"

        # Create the interactive signal
        interactive(
            sliced_signal.sum,
            axis=sliced_signal.axes_manager.signal_axes,
            event=roi.events.changed,
            recompute_out_event=None,
            out=out,
        )

        # Plot the result
        out.plot(**kwargs)

    def get_integrated_intensity(self, roi, out_signal_axes=None):
        """Obtains the intensity integrated over the scattering range as
        defined by the roi.

        Parameters
        ----------
        roi : :obj:`hyperspy.roi.BaseInteractiveROI`
            Any interactive ROI detailed in HyperSpy.
        out_signal_axes : None, iterable of int or string
            Specify which navigation axes to use as signal axes in the virtual
            image. If None, the two first navigation axis are used.

        Returns
        -------
        integrated_intensity : :obj:`hyperspy.signals.Signal2D` or :obj:`hyperspy.signals.Signal1D`
            The intensity integrated over the scattering range as defined by
            the roi.

        Examples
        --------
        .. code-block:: python

            >>> # For 1D diffraction signal, we can use a SpanROI
            >>> roi = hs.roi.SpanROI(left=1., right=2.)
            >>> virtual_image = dp.get_integrated_intensity(roi)

        .. code-block:: python

            >>> # For 2D diffraction signal,we can use a CircleROI
            >>> roi = hs.roi.CircleROI(3, 3, 5)
            >>> virtual_image = dp.get_integrated_intensity(roi)

        """
        dark_field = roi(self, axes=self.axes_manager.signal_axes)
        dark_field_sum = self._get_sum_signal(dark_field, out_signal_axes)
        dark_field_sum.metadata.General.title = "Integrated intensity"
        roi_info = f"{roi}"
        if self.metadata.get_item("General.title") not in ("", None):
            roi_info += f" of {self.metadata.General.title}"
        dark_field_sum.metadata.set_item("Diffraction.intergrated_range", roi_info)

        return dark_field_sum
