import pytest
import torch.cuda

from lettuce import Context, UnitConversion, Simulation
from lettuce.ext import ExtFlow, BGKCollision
from typing import List, Union, Optional


class DummyBGK(ExtFlow):
    def __init__(self, context: Context):
        ExtFlow.__init__(self, context, 16, 1.0, 1.0)

    def make_resolution(self, resolution: Union[int, List[int]],
                        stencil: Optional['Stencil'] = None) -> List[int]:
        return [resolution, resolution] if isinstance(resolution, int) \
            else resolution

    def make_units(self, reynolds_number, mach_number, _: List[int]
                   ) -> 'UnitConversion':
        return UnitConversion(reynolds_number=reynolds_number,
                              mach_number=mach_number)

    def initial_pu(self) -> (float, List[float]):
        ...

    def initialize(self):
        self.f[:, :, :] = 1.0
        self.f[:, 2, 2] = 2.0

    @property
    def boundaries(self) -> List['Boundary']:
        return []


def test_native_bgk_collision():
    cpu_context = Context('cpu')
    cpu_flow = DummyBGK(cpu_context)

    assert cpu_flow.f.shape[0] == 9
    assert cpu_flow.f.shape[1] == 16
    assert cpu_flow.f.shape[2] == 16

    native_context = Context(use_native=True)
    native_flow = DummyBGK(native_context)

    assert native_flow.f.shape[0] == 9
    assert native_flow.f.shape[1] == 16
    assert native_flow.f.shape[2] == 16

    collision = BGKCollision(2.0)

    cpu_simulation = Simulation(cpu_flow, collision, [])
    native_simulation = Simulation(native_flow, collision, [])

    assert cpu_flow.f.cpu().numpy() == pytest.approx(
        native_flow.f.cpu().numpy())

    cpu_simulation(1)
    native_simulation(1)

    # for i in range(9):
    #     for j in range(16):
    #         print()
    #         print(f"[{i}, {j}, :] cpu ", cpu_flow.f.cpu().numpy()[i, j, :])
    #         print(f"[{i}, {j}, :] nat ", native_flow.f.cpu().numpy()[i, j, :]
    #         )

    for i in range(9):
        for j in range(16):
            assert cpu_flow.f.cpu().numpy()[i, j, :] == pytest.approx(
                native_flow.f.cpu().numpy()[i, j, :]), f"[{i}, {j}, :]"

    #     print()
    #     cpu_index = int((cpu_flow.f.cpu()[i, :, :] == float(i + 1)).
    #     nonzero(as_tuple=True)[0])
    #     native_index = int((native_flow.f.cpu()[i, :, :] == float(i + 1)).
    #     nonzero(as_tuple=True)[0])
    #     print(f"cpu    distribution {i} row {cpu_index}: ", cpu_flow.f.cpu()
    #     [i, :, :][cpu_index])
    #     print(f"cuda_native distribution {i} row {native_index}: ",
    #     native_flow.f.cpu()[i, :, :][native_index])
