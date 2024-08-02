from .. import Force
from ... import Flow, Collision

__all__ = ['BGKInitialization']


class BGKInitialization(Collision):
    """
    Keep velocity constant.
    """

    def __init__(self, flow: 'Flow', moment_transformation):
        self.tau = flow.units.relaxation_parameter_lu
        self.moment_transformation = moment_transformation
        p, u = flow.initial_pu()
        self.u = flow.units.convert_velocity_to_lu(flow.context.convert_to_tensor(u))
        self.rho0 = flow.units.characteristic_density_lu
        momentum_names = tuple([f"j{x}" for x in "xyz"[:flow.stencil.d]])
        self.momentum_indices = moment_transformation[momentum_names]

    def __call__(self, flow: 'Flow'):
        rho = flow.rho()
        feq = flow.equilibrium(flow, rho, self.u)
        m = self.moment_transformation.transform(flow.f)
        meq = self.moment_transformation.transform(feq)
        mnew = m - 1.0 / self.tau * (m - meq)
        mnew[0] = m[0] - 1.0 / (self.tau + 1) * (m[0] - meq[0])
        mnew[self.momentum_indices] = rho * self.u
        f = self.moment_transformation.inverse_transform(mnew)
        return f
