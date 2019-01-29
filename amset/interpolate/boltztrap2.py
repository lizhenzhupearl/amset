"""
Class to interpolate a band structure using BoltzTraP2
"""

__author__ = "Alex Ganose, Francesco Ricci and Alireza Faghaninia"
__copyright__ = "Copyright 2019, HackingMaterials"
__maintainer__ = "Alex Ganose"

import multiprocessing

from BoltzTraP2 import sphere, fite
from pymatgen.electronic_structure.boltztrap2 import BandstructureLoader
from amset.interpolate.base import AbstractInterpolater


class BoltzTraP2Interpolater(AbstractInterpolater):
    """Class to interpolate band structures based on BoltzTraP2.

    The fitting algorithm is the Shankland-Koelling-Wood Fourier interpolation
    scheme, implemented in the BolzTraP1 software package.

    Details of the interpolation method are available in:

    1. R.N. Euwema, D.J. Stukel, T.C. Collins, J.S. DeWitt, D.G. Shankland,
       Phys. Rev. 178 (1969)  1419–1423.
    2. D.D. Koelling, J.H. Wood, J. Comput. Phys. 67 (1986) 253–262.
    3. Madsen, G. K. & Singh, D. J. Computer Physics Communications 175, 67–71
       (2006).

    The coefficient for fitting are calculated in BoltzTraP1, not in this code.
    The coefficients are used by this class to calculate the band eigenvalues.

    Note: This interpolater requires a modified version of BoltzTraP1 to run
    correctly. The modified version outputs the band structure coefficients to
    a file called "fort.123". A patch to modify BoltzTraP1 is provided in the
    "patch_for_boltztrap" directory.

    Args:
        band_structure (BandStructure): A pymatgen band structure object.
        num_electrons (num_electrons): The number of electrons in the system.
        coeff_file (str, optional): Path to a band structure coefficients file
            generated by a modified version of BoltzTraP1. If ``None``,
            BoltzTraP1 will be run to generate the file. Note, this requires
            a patched version of BoltzTraP1. More information can be found in
            the "patch_for_boltztrap" directory.
        max_temperature (int, optional): The maximum temperature at which to
            run BoltzTraP1 (if required). This will be used by BoltzTraP1 to
            decide how many bands to interpolate.
        lattice_matrix (np.ndarray): 3x3 array of the direct lattice matrix used
            to convert the velocity from fractional to cartesian coordinates.
    """

    def __init__(self, band_structure, num_electrons, n_jobs=-1, **kwargs):
        super(BoltzTraP2Interpolater, self).__init__(
            band_structure, num_electrons, **kwargs)
        self._n_jobs = multiprocessing.cpu_count() if n_jobs == -1 else n_jobs
        self._parameters = None

    def initialize(self):
        """Initialise the interpolater.

        This function will attempt to load the band structure coefficients.
        If a coefficient file is not provided, BoltzTraP1 will be run to
        generate it. This requires a modified version of BoltzTraP1 to run
        correctly. The modified version outputs the band structure coefficients
        to a file called "fort.123". A patch to modify BoltzTraP1 is provided in
        the "patch_for_boltztrap" directory.
        """
        bz2_data = BandstructureLoader(
            self._band_structure, structure=self._band_structure.structure,
            nelect=self._num_electrons)
        equivalences = sphere.get_equivalences(
            atoms=bz2_data.atoms, nkpt=len(bz2_data.kpoints) * 5,
            magmom=None)
        lattvec = bz2_data.get_lattvec()
        coeffs = fite.fitde3D(bz2_data, equivalences)

        self._parameters = (equivalences, lattvec, coeffs)

