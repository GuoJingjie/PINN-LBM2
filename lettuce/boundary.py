"""
Boundary Conditions.

Boundary conditions take a mask (a boolean numpy array) and specifies the grid points on which the boundary
condition operates.
"""

import torch
import numpy as np
from lettuce import (LettuceException)


class BounceBackBoundary:
    """Fullway Bounce-Back Boundary"""
    def __init__(self, mask, lattice):
        self.mask = lattice.convert_to_tensor(mask).byte()
        self.lattice = lattice

    def __call__(self, f):
        f = torch.where(self.mask, f[self.lattice.stencil.opposite], f)
        return f


class EquilibriumBoundaryPU:
    """Sets distributions on this boundary to equilibrium with predefined velocity and pressure.
    Note that this behavior is generally not compatible with the Navier-Stokes equations.
    This boundary condition should only be used if no better options are available.
    """
    def __init__(self, mask, lattice, units, velocity, pressure=0):
        self.mask = lattice.convert_to_tensor(mask)
        self.lattice = lattice
        self.units = units
        self.velocity = lattice.convert_to_tensor(velocity)
        self.pressure = lattice.convert_to_tensor(pressure)

    def __call__(self, f):
        rho = self.units.convert_pressure_pu_to_density_lu(self.pressure)
        u = self.units.convert_velocity_to_lu(self.velocity)
        feq = self.lattice.equilibrium(rho, u)
        feq = self.lattice.einsum("q,q->q", [feq, torch.ones_like(f)])
        f = torch.where(self.mask, feq, f)
        return f

class AntiBounceBackOutlet:
    """Allows distributions to leave domain unobstructed through this boundary.
        Based on equations from page 195 of "The lattice Boltzmann method" (2016 by Krüger et al.)
        Give the planned side of the boundary as array [1, 0, 0] for positive x-direction in 3D; [1, 0] for the sam in 2D
        [-1, 0, 0] is negative x-direction ect. [x, y, z]; only one entry nonzero
        """

    def __init__(self, lattice, direction):
        assert (isinstance(direction, list) and len(direction) in [1,2,3] and ((np.abs(sum(direction)) == 1) and (np.max(np.abs(direction)) == 1) and (1 in direction) ^ (-1 in direction))), \
            LettuceException("Wrong direction. Expected list of length 1, 2 or 3 with all entrys 0 except one 1 or -1, "
                                f"but got {type(direction)} of size {len(direction)} and entrys {direction}.")
        direction = np.array(direction)
        self.lattice = lattice

        #select velocities to be bounced (the ones pointing in "direction")
        self.velocities = np.concatenate(np.argwhere(np.matmul(self.lattice.stencil.e, direction) == 1), axis=0)

        # build indices of u and f that determine the side of the domain
        self.index = []
        self.neighbour = []
        for i in direction:
            if i == 0:
                self.index.append(slice(None))
                self.neighbour.append(slice(None))
            if i == 1:
                self.index.append(-1)
                self.neighbour.append(-2)
            if i == -1:
                self.index.append(0)
                self.neighbour.append(1)
        # construct indices for einsum
        if len(direction) == 3:
            #self.dims = 'c, xyz -> '.replace('xyz'[(np.where(abs(direction)==1))[0][0]], 'c') + 'xyz'.replace('xyz'[(np.where(abs(direction)==1))[0][0]], '')
            self.dims = 'dc, cxy -> dxy'
            self.w = self.lattice.w[self.velocities].view(1, -1).t().unsqueeze(1)
        if len(direction) == 2:
            #self.dims = 'c, xy -> '.replace('xy'[(np.where(abs(direction)==1))[0][0]], 'c') + 'xy'.replace('xy'[(np.where(abs(direction)==1))[0][0]], '')
            self.dims = 'dc, cx -> dx'
            self.w = self.lattice.w[self.velocities].view(1, -1).t()
        if len(direction) == 1:
            self.dims = 'dc, c -> dc'
            self.w = self.lattice.w[self.velocities]

    def __call__(self, f):
        u = self.lattice.u(f)
        u_w = u[[slice(None)] + self.index] + 0.5 * (u[[slice(None)] + self.index] - u[[slice(None)] + self.neighbour])
        f[[np.array(self.lattice.stencil.opposite)[self.velocities]] + self.index] = - f[[self.velocities] + self.index] + self.w * \
             self.lattice.rho(f)[[slice(None)] + self.index] * (2 + torch.einsum(self.dims,self.lattice.e[self.velocities],u_w) ** 2 / self.lattice.cs ** 4 - (torch.norm(u_w,dim=0) / self.lattice.cs) ** 2)
        return f

#    def __call__(self, f):
         # self.mask = torch.zeros(lattice.convert_to_tensor(grid).shape[1:], device=lattice.device, dtype=torch.bool)
         # self.mask[-1, :] = True
#        # 3D: self.direction = [1, 11, 13, 15, 17, 19, 21, 23, 25]
#        # 2D: self.direction = [1, 5, 8]
#        u = self.lattice.u(f)
#        u_w = u[:, -1, :] + 0.5 * (u[:, -1, :] - u[:, -2, :]) #2D
#        u_w = u[:, -1, :, :] + 0.5 * (u[:, -1, :, :] - u[:, -2, :, :]) #3D
#        #f_bounced = torch.where(self.mask, f[self.lattice.stencil.opposite], f)
#        for i in self.velocities:
#        #2D:
#            f[self.lattice.stencil.opposite[i], -1, :] = - f[i, -1, :] + self.lattice.stencil.w[i] * self.lattice.rho(f)[0, self.mask] * \
#                        (2 + torch.matmul(torch.tensor((self.lattice.stencil.e[i]), device=f.device, dtype=f.dtype), u_w) ** 2 / self.lattice.stencil.cs ** 4 - (torch.norm(u_w, dim=0) / self.lattice.stencil.cs)**2)
         #3D:
#        f[self.lattice.stencil.opposite[i], -1, :, :] = - f[i, -1, :, :] + self.lattice.stencil.w[i] * self.lattice.rho(f)[0, self.mask].reshape(f[0].shape[1],f[0].shape[2]) * \
#              (2 + torch.einsum('c, cyz -> yz',torch.tensor(self.lattice.stencil.e[i],device=f.device, dtype=f.dtype),u_w) ** 2 / self.lattice.stencil.cs ** 4 - (torch.norm(u_w,dim=0) / self.lattice.stencil.cs) ** 2)
#        return f

