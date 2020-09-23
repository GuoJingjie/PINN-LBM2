
import pytest
import os
from lettuce import TaylorGreenVortex2D, TaylorGreenVortex3D, PoiseuilleFlow2D, Lattice, D3Q27, D2Q9, write_image, BGKCollision, StandardStreaming, Simulation
from lettuce.reporters import write_vtk, VTKReporter,EnstrophyReporter,EnergyReporter,MaxUReporter
import numpy as np


def test_write_image(tmpdir):
    pytest.skip("matplotlib not working")
    lattice = Lattice(D2Q9, "cpu")
    flow = TaylorGreenVortex2D(resolution=16, reynolds_number=10, mach_number=0.05, lattice=lattice)
    p, u = flow.initial_solution(flow.grid)
    write_image(tmpdir/"p.png", p[0])
    print(tmpdir/"p.png")
    assert os.path.isfile(tmpdir/"p.png")


@pytest.mark.parametrize("Reporter", [EnstrophyReporter, EnergyReporter, MaxUReporter])
@pytest.mark.parametrize("Case", [TaylorGreenVortex2D,TaylorGreenVortex3D])
def test_generic_reporters(Reporter, Case, dtype_device):
    dtype, device = dtype_device
    lattice = Lattice(D2Q9, dtype=dtype, device=device)
    flow = Case(64, 10000, 0.05, lattice=lattice)
    if Case == TaylorGreenVortex3D:
        lattice = Lattice(D3Q27, dtype=dtype, device=device)
    collision = BGKCollision(lattice, tau=flow.units.relaxation_parameter_lu)
    streaming = StandardStreaming(lattice)
    simulation = Simulation(flow=flow, lattice=lattice, collision=collision, streaming=streaming)
    kinE_reporter = Reporter(lattice, flow, interval=1, out=None)
    simulation.reporters.append(kinE_reporter)
    simulation.step(2)
    assert(np.asarray(kinE_reporter.out)[1,1] == pytest.approx(np.asarray(kinE_reporter.out)[0,1], rel=0.05))


def test_write_vtk(tmpdir):
    lattice = Lattice(D2Q9, "cpu")
    flow = TaylorGreenVortex2D(resolution=16, reynolds_number=10, mach_number=0.05, lattice=lattice)
    p, u = flow.initial_solution(flow.grid)
    point_dict = {}
    point_dict["p"] = p[0, ..., None]
    write_vtk(point_dict, id=1, filename_base=tmpdir/"output")
    assert os.path.isfile(tmpdir/"output_00000001.vtr")


def test_vtk_reporter_no_mask(tmpdir):
    lattice = Lattice(D2Q9, "cpu")
    flow = TaylorGreenVortex2D(resolution=16, reynolds_number=10, mach_number=0.05, lattice=lattice)
    collision = BGKCollision(lattice, tau=flow.units.relaxation_parameter_lu)
    streaming = StandardStreaming(lattice)
    simulation = Simulation(flow=flow, lattice=lattice, collision=collision, streaming=streaming)
    vtk_reporter = VTKReporter(lattice, flow, interval=1, filename_base=tmpdir/"output")
    simulation.reporters.append(vtk_reporter)
    simulation.step(2)
    assert os.path.isfile(tmpdir/"output_00000001.vtr")
    assert os.path.isfile(tmpdir/"output_00000002.vtr")

def test_vtk_reporter_mask(tmpdir):
    lattice = Lattice(D2Q9, "cpu")
    flow = PoiseuilleFlow2D(resolution=16, reynolds_number=10, mach_number=0.05, lattice=lattice)
    collision = BGKCollision(lattice, tau=flow.units.relaxation_parameter_lu)
    streaming = StandardStreaming(lattice)
    simulation = Simulation(flow=flow, lattice=lattice, collision=collision, streaming=streaming)
    vtk_reporter = VTKReporter(lattice, flow, interval=1, filename_base=tmpdir/"output2")
    simulation.reporters.append(vtk_reporter)
    simulation.step(2)
    assert os.path.isfile(tmpdir / "output2_mask.vtr")
    assert os.path.isfile(tmpdir/"output2_00000001.vtr")
    assert os.path.isfile(tmpdir/"output2_00000002.vtr")
