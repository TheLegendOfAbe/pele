"""
lj potential with the number of near neighbors restricted.
"""
import numpy as np

from pygmin.potentials import BasePotential
from pygmin.systems import BLJCluster
import fortran.maxneib_blj as fortranpot

__all__ = ["MaxNeibsBLJ", "MaxNeibsBLJSystem"]


class MaxNeibsBLJ(BasePotential):
    """
    binary system of atoms interact with lj potential, with an additional energy penalty for too many neighbors
    
    Notes
    -----
    in addition to the LJ energy the penalty term is::
        
        E = sum_i F(ni, max_neibs, neib_crossover)
        
    where `F` is the fermi function defined as::
    
        F(x, mu, T) = 1. / (exp(-(x-mu)/T) + 1.)
    
    and `ni` is a continuous measure of the number of neighbors of the i'th
    atom::
    
        ni = sum_j F(rij, rneib, rneib_crossover)
    
    where `rij` is the separation of atoms `i` and `j`.  The other parameters
    above are defined in the Parameters section

    The Fermi function is used in order to get a continuous measure of whether
    two atoms are neighbors.  It is also used again to calculate the energy
    penalty if an atom has too many neighbors.


    
    
    Parameters
    ----------
    natoms : int
        number of atoms
    ntypeA : int
        number of type A atoms
    epsA, epsB, epsAB : float
        lj eps for the various interactions
    sigA, sigB, sigAB : float
        lj sig for the various interactions
    boxl : float
        box length if periodic
    max_neibs : float 
        maximum number of allowed neighbors
    neib_crossover : float
        width of neighbor energy crossover function
    rneib : float
        distance to consider two atoms neighbors
    rneib_crossover : float
        width of rneib crossover region
    epsneibs : float
        energy scale of the neighbor penalty function
    
    See Also
    --------
    MaxNeibsLJ

    
    """
    def __init__(self, natoms, ntypeA, 
                 epsA=1.0, sigA=1.0, 
                 epsB=0.5, sigB=0.88, epsAB="default", sigAB="default",
                 boxl=None,
                 max_neibs=5.,
                 neib_crossover=.4,
                 rneib=1.4,
                 rneib_crossover=0.08,
                 epsneibs=5.,
                 ):
        self.natoms = natoms
        self.ntypeA = ntypeA
        self.sigA = sigA
        self.epsA = epsA
        self.sigB = sigB
        self.epsB = epsB
        if sigAB == "default":
            self.sigAB = (self.sigA + self.sigB) / 2.
        else:
            self.sigAB = sigAB
        if epsAB == "default":
            self.epsAB = (self.epsA + self.epsB) / 2.
        else:
            self.epsAB = epsAB
        
        if boxl is None:
            self.boxl = 1e100
            self.periodic = False
        else:
            self.boxl = boxl
            self.periodic = True
        
        self.rneib = rneib
        self.rneib_crossover = rneib_crossover
        self.max_neibs = max_neibs
        self.neib_crossover = neib_crossover
        self.epsneibs = epsneibs

    def getEnergy(self, coords):
        E = fortranpot.maxneib_ljenergy(
                coords, self.ntypeA,
                self.epsA, self.sigA, 
                self.epsB, self.sigB, 
                self.epsAB, self.sigAB, 
                self.periodic, self.boxl, 
                self.rneib, self.rneib_crossover, self.max_neibs, self.neib_crossover, 
                self.epsneibs)
        return E
    def getEnergyGradient(self, coords):
        E, grad = fortranpot.maxneib_ljenergy_gradient(
                coords, self.ntypeA,
                self.epsA, self.sigA, 
                self.epsB, self.sigB, 
                self.epsAB, self.sigAB, 
                self.periodic, self.boxl, 
                self.rneib, self.rneib_crossover, self.max_neibs, self.neib_crossover, 
                self.epsneibs)
        return E, grad


class MaxNeibsBLJSystem(BLJCluster):
    def __init__(self, natoms, ntypeA="default", **potkwargs):
        super(MaxNeibsBLJSystem, self).__init__(natoms, ntypeA=ntypeA)
        self.potkwargs = potkwargs
        self.params.gui.basinhopping_nsteps = 300
        self.pot = self.get_potential()

    def __call__(self):
        return self
    
    def get_potential(self):
        return MaxNeibsBLJ(self.natoms, self.ntypeA, **self.potkwargs)


def run_gui(system):
    import pygmin.gui.run as gr
    gr.run_gui(system)


if __name__ == "__main__":
    natoms = 20
    ntypeA = natoms/2
    system = MaxNeibsBLJSystem(natoms, ntypeA=ntypeA, max_neibs=3, rneib=1.7)
    
    coords = system.get_random_configuration()
    pot = system.get_potential()
    E = pot.getEnergy(coords)
    print "energy", E
    pot.test_potential(coords)
    if True:
        coords = system.get_random_minimized_configuration()[0]
        pot.test_potential(coords)
#    exit(10)
    
    run_gui(system)
