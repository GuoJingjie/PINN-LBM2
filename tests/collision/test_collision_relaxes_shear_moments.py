from tests.common import *

@pytest.mark.parametrize("Collision",
                         [BGKCollision, TRTCollision, KBCCollision,
                          RegularizedCollision])
def test_collision_relaxes_shear_moments(Collision,
                                         fix_device,
                                         fix_dtype,
                                         fix_stencil):
    """checks whether the collision models relax the shear moments according
    to the prescribed relaxation time"""
    if Collision == KBCCollision and type(fix_stencil) not in [D2Q9, D3Q27]:
        pytest.skip("KBCCollision only implemented for D2Q9 and D3Q27")
    context = Context(device=fix_device, dtype=fix_dtype, use_native=False)
    flow = TestFlow(context=context,
                    resolution=[16] * fix_stencil.d,
                    reynolds_number=100,
                    mach_number=0.1,
                    stencil=fix_stencil)
    feq = flow.equilibrium(flow)
    shear_pre = flow.shear_tensor()
    shear_eq_pre = flow.shear_tensor(feq)
    tau = 0.6
    coll = Collision(tau)
    f_post = coll(flow)
    shear_post = flow.shear_tensor(f_post)
    assert (shear_post.cpu().numpy() ==
            pytest.approx((shear_pre
                           - 1 / tau * (shear_pre - shear_eq_pre)
                           ).cpu().numpy(), abs=1e-5))