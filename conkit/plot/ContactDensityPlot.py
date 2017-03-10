"""
A module to produce a domain boundary plot
"""

from __future__ import division

__author__ = "Felix Simkovic"
__date__ = "23 Feb 2017"
__version__ = 0.1

import matplotlib.pyplot
import numpy
import warnings

try:
    import scipy.signal
    SCIPY = True
except ImportError:
    SCIPY = False


from conkit.plot._Figure import Figure
from conkit.plot._plottools import ColorDefinitions


class ContactDensityFigure(Figure):
    """A Figure object specifically for a contact density illustration.

    This figure is an adaptation of the algorithm published by Sadowski
    (2013) [#]_.

    .. [#] Sadowski M. (2013). Prediction of protein domain boundaries
       from inverse covariances. Proteins 81(2), 253-260.

    Attributes
    ----------
    hierarchy : :obj:`ContactMap <conkit.core.ContactMap>`
       The default contact map hierarchy
    bw_method : str
       The method to estimate the bandwidth [default: bowman]

    Examples
    --------
    >>> import conkit
    >>> cmap = conkit.io.read('toxd/toxd.mat', 'ccmpred').top_map
    >>> conkit.plot.ContactDensityFigure(cmap)

    """
    BW_METHODS = ['bowman']

    def __init__(self, hierarchy, bw_method='bowman', **kwargs):
        """A new contact density plot

        Parameters
        ----------
        hierarchy : :obj:`ContactMap <conkit.core.ContactMap>`
           The default contact map hierarchy
        bw_method : str, optional
           The method to estimate the bandwidth [default: bowman]
        **kwargs
           General :obj:`Figure <conkit.plot._Figure.Figure>` keyword arguments

        """
        super(ContactDensityFigure, self).__init__(**kwargs)
        self._bw_method = None
        self._hierarchy = None

        self.bw_method = bw_method
        self.hierarchy = hierarchy

        self._draw()

    def __repr__(self):
        return "{0}(file_name=\"{1}\" bw_method=\"{2}\")".format(
            self.__class__.__name__, self.file_name, self.bw_method
        )

    @property
    def bw_method(self):
        """The method to estimate the bandwidth"""
        return self._bw_method

    @bw_method.setter
    def bw_method(self, bw_method):
        """Define the method to estimate the bandwidth

        Raises
        ------
        ValueError
           Method not yet defined

        """
        if bw_method not in ContactDensityFigure.BW_METHODS:
            msg = "Bandwidth method not yet implemented: {0}".format(bw_method)
            raise ValueError(msg)
        self._bw_method = bw_method

    @property
    def hierarchy(self):
        """A ConKit :obj:`ContactMap <conkit.core.ContactMap>`"""
        return self._hierarchy

    @hierarchy.setter
    def hierarchy(self, hierarchy):
        """Define the ConKit :obj:`ContactMap <conkit.core.ContactMap>`

        Raises
        ------
        RuntimeError
           The hierarchy is not an contact map

        """
        if hierarchy:
            Figure._check_hierarchy(hierarchy, "ContactMap")
        self._hierarchy = hierarchy

    def redraw(self):
        """Re-draw the plot with updated parameters"""
        self._draw()

    def _draw(self):
        """Draw the actual plot"""

        # Estimate the Kernel Density using original data
        dens = numpy.asarray(self.hierarchy.calculate_kernel_density(self.bw_method))
        
        # Plot the data
        fig, ax = matplotlib.pyplot.subplots()

        # The residues for the x-axis
        residues = numpy.asarray(
            list(set(
                sorted([c.res1_seq for c in self.hierarchy] + [c.res2_seq for c in self.hierarchy])
            ))
        )
        x = numpy.arange(residues.min(), residues.max())

        ax.plot(x, dens, linestyle="solid",
                color=ColorDefinitions.GENERAL, label="Kernel Density Estimate")

        # Find all local minima
        if SCIPY:
            local_minima_idx = scipy.signal.argrelmin(dens)[0]
            ax.scatter(x[local_minima_idx], dens[local_minima_idx], marker="p",
                       color=ColorDefinitions.MISMATCH, label="Local Minimum")
        else:
            warnings.warn("SciPy not installed - cannot determine local minima")

        # Prettify the plot
        ax.set_xlim(x.min(), x.max())
        ax.set_ylim(0., dens.max())

        ax.set_xlabel('Residue number')
        ax.set_ylabel('Kernel Density Estimate')
        ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=3, mode="expand", borderaxespad=0.,
                  scatterpoints=1)

        # Make axes length proportional and remove whitespace around the plot
        aspectratio = Figure._correct_aspect(ax, 0.3)
        ax.set(aspect=aspectratio)
        fig.tight_layout()

        fig.savefig(self.file_name, bbox_inches='tight', dpi=self.dpi)
