import pytest
import os
from lettuce import (TaylorGreenVortex2D, TaylorGreenVortex3D,
                     PoiseuilleFlow2D, Lattice, D3Q27, D2Q9, write_image,
                     BGKCollision, StandardStreaming, Simulation, Context)
from lettuce.util.reporters import write_vtk, VTKReporter, ObservableReporter
from lettuce.util.datautils import HDF5Reporter, LettuceDataset
from lettuce.util.observables import (Enstrophy, EnergySpectrum,
                                      MaximumVelocity,
                                      IncompressibleKineticEnergy, Mass)
import numpy as np
import torch


def test_HDF5Reporter(tmpdir):
    step = 3
    lattice = Lattice(D2Q9, "cpu")
    flow = TaylorGreenVortex2D(resolution=16, reynolds_number=10,
                               mach_number=0.05, lattice=lattice)
    collision = BGKCollision(lattice=lattice,
                             tau=flow.units.relaxation_parameter_lu)
    streaming = StandardStreaming(lattice=lattice)
    simulation = Simulation(flow=flow,
                            lattice=lattice,
                            collision=collision,
                            streaming=streaming)
    hdf5_reporter = HDF5Reporter(
        flow=flow,
        collision=collision,
        interval=step,
        filebase=tmpdir / "output")
    simulation.reporters.append(hdf5_reporter)
    simulation.step(step)
    assert os.path.isfile(tmpdir / "output.h5")

    dataset_train = LettuceDataset(
        filebase=tmpdir / "output.h5",
        target=True)
    train_loader = torch.utils.data.DataLoader(dataset_train, shuffle=False)
    print(dataset_train)
    for (f, target, idx) in train_loader:
        assert idx in (0, 1, 2)
        assert f.shape == (1, 9, 16, 16)
        assert target.shape == (1, 9, 16, 16)
