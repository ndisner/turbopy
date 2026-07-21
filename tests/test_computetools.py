"""Tests for turbopy/computetools.py"""
import pytest
import numpy as np
from turbopy.computetools import *


def test_init_should_create_object():
    """Method that creates a BorisPush object to test __init__"""
    init_example = BorisPush(Simulation({"type": "BorisPush"}),
                             {"type": "BorisPush"})
    assert isinstance(init_example, BorisPush)
    assert init_example.c2 == 2.9979e8 ** 2


def test_push_with_no_fields():
    """Tests the functionality of the push method, when E=B=0"""
    input_data = {"Clock":
                      {"start_time": 0, "end_time": 100, "dt": 1e-9},
                  "type": "BorisPush",
                  "Grid": {"N": 10, "min": 20, "max": 30},
                  "PhysicsModules": {}}
    owner = Simulation(input_data)
    owner.prepare_simulation()
    push_example = BorisPush(owner, input_data)
    charge = 1.6022e-19
    mass = 1.6726e-27
    E = np.zeros(3)
    B = np.zeros(3)
    x_i = np.array([[0, 0, 0.0]], dtype=np.float64)
    v_i = np.array([[0, 0, 3.0e2]], dtype=np.float64)
    p_i = mass * v_i
    clock = input_data["Clock"]
    N = 10
    x_final = v_i * N * clock["dt"]
    for i in range(N):
        push_example.push(x_i, p_i, charge, mass, E, B)
    assert np.allclose(x_i, x_final)


def test_push_with_crossed_fields():
    """Tests the functionality of the push method for E, B, not 0"""
    input_data = {
        "Clock": {"start_time": 0, "end_time": 100, "dt": 1e-9},
        "type": "BorisPush",
        "Grid": {"N": 10, "min": 20, "max": 30},
        "PhysicsModules": {}}
    owner = Simulation(input_data)
    owner.prepare_simulation()
    push_example = BorisPush(owner, input_data)
    charge = 1.6022e-19
    mass = 1.6726e-27
    N = 10
    x_i = np.array([[0, 0, 0.0]], dtype=np.float64)
    p_i = np.array([[0, 0, 0.0]], dtype=np.float64)
    E = np.array([[10, 0, 0]], dtype=np.float64)
    B = np.array([[0, 0, 10]], dtype=np.float64)
    for i in range(N):
        push_example.push(x_i, p_i, charge, mass, E, B)
    x_final = np.array([[2.20028479e-09, -1.04482737e-08, 0]])
    assert np.allclose(x_i, x_final)
    p_final = np.array([[0.47183691, -1.88168585,  0]]) * mass
    assert np.allclose(p_i / mass, p_final / mass)


@pytest.fixture
def interpolator():
    """Pytest fixture for basic Interpolator class"""
    return Interpolators(Simulation({}), {"type": "Interpolator"})


def test_interpolate1D(interpolator):
    """Tests for turbopy.computetools.Interpolator's interpolate1D method"""
    x = np.arange(0, 10, 1)
    y = np.exp(x)
    xnew = np.arange(0, 1, 0.1)

    f1 = interpolator.interpolate1D(x, y)
    f2 = interpolate.interp1d(x, y)
    assert np.allclose(f1(x), y)
    assert np.allclose(f1(xnew), f2(xnew))

    y = np.asarray([n ** 2 for n in x])
    f1 = interpolator.interpolate1D(x, y, 'quadratic')
    f2 = interpolate.interp1d(x, y, 'quadratic')
    assert np.allclose(f1(x), y)
    assert np.allclose(f1(xnew), f2(xnew))


@pytest.fixture
def fin_diff():
    """Pytest fixture for basic FiniteDifference class with centered method."""
    dic = {"Grid": {"N": 10, "r_min": 0, "r_max": 10},
           "Clock": {"start_time": 0,
                     "end_time": 10,
                     "num_steps": 100},
           "Tools": {},
           "PhysicsModules": {},
           }
    sim = Simulation(dic)
    sim.run()
    return FiniteDifference(sim, {'type': 'FiniteDifference', 'method': 'centered'})


def test_setup_ddx(fin_diff):
    """Tests that `setup_ddx` returns the function specified by `method` in
    `input_data`.
    """
    y = np.arange(0, 10)
    center = fin_diff.setup_ddx()

    assert center == fin_diff.centered_difference
    assert center(y).shape == (10,)
    assert np.allclose(center(y), fin_diff.centered_difference(y))

    fin_diff._input_data['method'] = 'upwind_left'
    upwind = fin_diff.setup_ddx()
    assert upwind == fin_diff.upwind_left
    assert upwind(y).shape == (10,)
    assert np.allclose(upwind(y), fin_diff.upwind_left(y))


def test_centered_difference(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's centered_difference method."""
    dr = fin_diff._owner.grid.dr
    f = fin_diff._owner.grid.generate_field()
    y = np.arange(0, 10)

    assert np.allclose(fin_diff.centered_difference(y),
                       np.append([f[0]], np.append((y[2:] - y[:-2]) / (2 * dr), f[-1])))


def test_upwind_left(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's upwind_left method."""
    cell_widths = fin_diff._owner.grid.cell_widths
    f = fin_diff._owner.grid.generate_field()
    y = np.arange(0, 10)

    assert np.allclose(fin_diff.upwind_left(y), np.append([f[0]], (y[1:] - y[:-1]) / cell_widths))


def test_ddx(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's ddx method."""
    N = fin_diff._owner.grid.num_points
    g = 1 / (2.0 * fin_diff.dr)
    d = fin_diff.ddx()
    assert d.shape == (N, N)
    assert np.allclose(d.toarray(), sparse.dia_matrix(([np.zeros(N) - g, np.zeros(N) + g], [-1, 1]),
                                                      shape=(N, N)).toarray())


def test_radial_curl(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's radial_curl method."""
    with np.errstate(divide='ignore'):
        N = fin_diff._owner.grid.num_points
        dr = fin_diff._owner.grid.dr
        r = fin_diff._owner.grid.r
        g = 1 / (2.0 * dr)
        below = np.append(-g * (r[:-1] / r[1:])[:-1], [0.0, 0.0])
        diag = np.append(np.zeros(N - 1), [1 / dr])
        above = np.append([0.0, 2.0 / dr], g * (r[1:] / r[:-1])[1:])
        d = fin_diff.radial_curl()
        assert d.shape == (N, N)
        for actual, expected in zip(d.data, [below, diag, above]):
            assert np.allclose(actual, expected)


def test_del2_radial(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's del2_radial method."""
    with np.errstate(divide='ignore'):
        N = fin_diff._owner.grid.num_points
        dr = fin_diff._owner.grid.dr
        r = fin_diff._owner.grid.r
        g1 = 1 / (2.0 * dr)
        g2 = 1 / (dr ** 2)
        below = np.append(-g1 / r[1:], [-g1]) + (g2 * np.ones(N))
        above = (np.append([g1, 0], g1 / r[1:-1]) +
                 np.append([g2, g2 * 2], g2 * np.ones(N - 2)))
        diag = -2 * g2 * np.ones(N)
        d = fin_diff.del2_radial()
        d_array = d.toarray()
        assert d.shape == (N, N)
        for ind in range(N - 1):
            assert d_array[ind + 1][ind] == below[ind]
        for ind in range(N):
            assert d_array[ind][ind] == diag[ind]
        for ind in range(N - 1):
            assert d_array[ind][ind + 1] == above[ind + 1]


def test_del2(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's del2 method."""
    N = fin_diff._owner.grid.num_points
    dr = fin_diff._owner.grid.dr
    g = 1 / (dr ** 2)

    below = g * np.ones(N)
    diag = -2 * g * np.ones(N)
    above = g * np.ones(N)
    above[1] *= 2

    d = fin_diff.del2()
    assert d.shape == (N, N)
    for actual, expected in zip(d.data, [below, diag, above]):
        assert np.allclose(actual, expected)


def test_ddr(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's ddr method."""
    N = fin_diff._owner.grid.num_points
    dr = fin_diff._owner.grid.dr
    g1 = 1 / (2.0 * dr)

    below = -g1 * np.ones(N)
    above = g1 * np.ones(N)
    above[1] = 0

    d = fin_diff.ddr()
    assert d.shape == (N, N)
    for actual, expected in zip(d.data, [below, above]):
        assert np.allclose(actual, expected)


def test_BC_left_extrap(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's BC_left_extrap method."""
    N = fin_diff._owner.grid.num_points

    diag = np.append(0, np.ones(N-1))
    above = np.append([0.0, 2.0], np.zeros(N-2))
    above2 = np.append([0.0, 0.0, -1.0], np.zeros(N-3))

    d = fin_diff.BC_left_extrap()
    assert d.shape == (N, N)
    for actual, expected in zip(d.data, [diag, above, above2]):
        assert np.allclose(actual, expected)


def test_BC_left_avg(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's BC_left_avg method."""
    N = fin_diff._owner.grid.num_points

    diag = np.append(0, np.ones(N - 1))
    above = np.append([0.0, 1.5], np.zeros(N - 2))
    above2 = np.append([0.0, 0.0, -0.5], np.zeros(N - 3))

    d = fin_diff.BC_left_avg()
    assert d.shape == (N, N)
    for actual, expected in zip(d.data, [diag, above, above2]):
        assert np.allclose(actual, expected)


def test_BC_left_quad(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's BC_left_quad method."""
    N = fin_diff._owner.grid.num_points
    r = fin_diff._owner.grid.r
    R = (r[1]**2 + r[2]**2)/(r[2]**2 - r[1]**2)/2

    diag = np.append(0, np.ones(N - 1))
    above = np.append([0.0, 0.5 + R], np.zeros(N - 2))
    above2 = np.append([0.0, 0.0, 0.5 - R], np.zeros(N - 3))

    d = fin_diff.BC_left_quad()
    assert d.shape == (N, N)
    for actual, expected in zip(d.data, [diag, above, above2]):
        assert np.allclose(actual, expected)


def test_BC_left_flat(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's BC_left_flat method."""
    N = fin_diff._owner.grid.num_points

    diag = np.append(0, np.ones(N - 1))
    above = np.append([0.0, 1], np.zeros(N - 2))

    d = fin_diff.BC_left_flat()
    assert d.shape == (N, N)
    for actual, expected in zip(d.data, [diag, above]):
        assert np.allclose(actual, expected)

def test_BC_right_extrap(fin_diff):
    """Tests for turbopy.computetools.FiniteDifference's BC_right_extrap method."""
    N = fin_diff._owner.grid.num_points

    below2 = np.append(np.zeros(N - 3), [-1.0, 0.0, 0.0])
    below = np.append(np.zeros(N - 2), [2.0, 0.0])
    diag = np.append(np.ones(N - 1), 0)

    d = fin_diff.BC_right_extrap()
    assert d.shape == (N, N)
    for actual, expected in zip(d.data, [below2, below, diag]):
        assert np.allclose(actual, expected)

        
def test_init_poisson():
    """Method that creates a PoissonSolver1DRadial object to test __init__"""
    input_data = {
        "Clock": {"start_time": 0, "end_time": 100, "dt": 1e-9},
        "type": "PoissonSolver1DRadial",
        "Grid": {"N": 10, "min": 20, "max": 30},
        "PhysicsModules": {}}
    owner = Simulation(input_data)
    owner.prepare_simulation()
    solver = PoissonSolver1DRadial(owner, input_data)
    assert isinstance(solver, PoissonSolver1DRadial)


def test_poisson_solver():
    sources = np.array([5.0, 2.0, 7.0, 9.0, 2.0, 12.0, 4.0, 14.0, 11.0, 1.0, 3.0])
    input_data = {
        "Clock": {"start_time": 0, "end_time": 100, "dt": 1e-9},
        "type": "PoissonSolver1DRadial",
        "Grid": {"N": 11, "r_min": 0, "r_max": 1},
        "PhysicsModules": {}}
    owner = Simulation(input_data)
    owner.prepare_simulation()
    solver = PoissonSolver1DRadial(owner, input_data)
    solved = solver.solve(sources)
    assert solved[-1] == 0
    ans = np.array([-2.67860, -2.61860, -2.49860, -2.31527, -2.14777, -1.88577, -1.62077,
            -1.24791, -0.80666, -0.4, 0.0])
    np.testing.assert_almost_equal(solved, ans, decimal=4)
    assert solved.size == input_data["Grid"]["N"]

    sources = np.array([5.0, 2.0, 7.0])  # fix innard parts
    input_data = {
        "Clock": {"start_time": 0, "end_time": 100, "dt": 1e-9},
        "type": "PoissonSolver1DRadial",
        "Grid": {"N": 3, "r_min": 0, "r_max": 1},
        "PhysicsModules": {}}
    owner = Simulation(input_data)
    owner.prepare_simulation()
    solver = PoissonSolver1DRadial(owner, input_data)
    solved = solver.solve(sources)
    assert solved[-1] == 0
    ans = np.array([-4.5, -3.0, 0.0])
    np.testing.assert_almost_equal(solved, ans, decimal=4)
    assert solved.size == input_data["Grid"]["N"]


# ---------------------------------------------------------------------------
# FiniteDifference2D
# ---------------------------------------------------------------------------

def _clock_tools():
    return {
        "Clock": {"start_time": 0, "end_time": 1, "num_steps": 1},
        "Tools": {},
        "PhysicsModules": {},
    }


@pytest.fixture
def cart2d_sim():
    """Simulation with a Grid2DCartesian; regular 5x4 grid on [0,4] x [0,3]."""
    dic = {"Grid": {"coordinate_system": "cartesian2d",
                    "Nx": 5, "Ny": 4,
                    "x_min": 0.0, "x_max": 4.0,
                    "y_min": 0.0, "y_max": 3.0},
           **_clock_tools()}
    sim = Simulation(dic)
    sim.prepare_simulation()
    return sim


@pytest.fixture
def cart2d_fd(cart2d_sim):
    return FiniteDifference2D(cart2d_sim, {"type": "FiniteDifference2D"})


@pytest.fixture
def cyl2d_sim():
    """Simulation with a Grid2DCylindrical; r ∈ [1, 5], z ∈ [0, 3]. r_min > 0
    keeps the (1/r) term regular so analytic references stay clean.
    """
    dic = {"Grid": {"coordinate_system": "cylindrical2d",
                    "Nr": 5, "Nz": 4,
                    "r_min": 1.0, "r_max": 5.0,
                    "z_min": 0.0, "z_max": 3.0},
           **_clock_tools()}
    sim = Simulation(dic)
    sim.prepare_simulation()
    return sim


@pytest.fixture
def cyl2d_fd(cyl2d_sim):
    return FiniteDifference2D(cyl2d_sim, {"type": "FiniteDifference2D"})


def _apply(op, field):
    """Apply a 2D sparse operator to a field of shape (N1, N2)."""
    return (op @ field.ravel(order='C')).reshape(field.shape)


def test_fd2d_init_rejects_1d_grid():
    dic = {"Grid": {"N": 5, "r_min": 0, "r_max": 1}, **_clock_tools()}
    sim = Simulation(dic)
    sim.prepare_simulation()
    with pytest.raises(TypeError):
        FiniteDifference2D(sim, {"type": "FiniteDifference2D"})


# ----- Cartesian --------------------------------------------------------------

def test_ddx_shape(cart2d_fd, cart2d_sim):
    Nx, Ny = cart2d_sim.grid.Nx, cart2d_sim.grid.Ny
    assert cart2d_fd.ddx().shape == (Nx * Ny, Nx * Ny)


def test_ddx_on_linear_x(cart2d_fd, cart2d_sim):
    grid = cart2d_sim.grid
    f = grid.XX.copy()  # f(x, y) = x
    result = _apply(cart2d_fd.ddx(), f)
    # centered difference of x is 1 on interior rows (i = 1..Nx-2)
    assert np.allclose(result[1:-1, :], 1.0)


def test_ddy_on_linear_y(cart2d_fd, cart2d_sim):
    grid = cart2d_sim.grid
    f = grid.YY.copy()  # f(x, y) = y
    result = _apply(cart2d_fd.ddy(), f)
    assert np.allclose(result[:, 1:-1], 1.0)


def test_del2_x_on_quadratic_x(cart2d_fd, cart2d_sim):
    grid = cart2d_sim.grid
    f = grid.XX ** 2  # d^2/dx^2 = 2 (exact for centered diff on quadratics)
    result = _apply(cart2d_fd.del2_x(), f)
    assert np.allclose(result[1:-1, :], 2.0)


def test_del2_y_on_quadratic_y(cart2d_fd, cart2d_sim):
    grid = cart2d_sim.grid
    f = grid.YY ** 2
    result = _apply(cart2d_fd.del2_y(), f)
    assert np.allclose(result[:, 1:-1], 2.0)


def test_laplacian_cartesian_on_x2_plus_y2(cart2d_fd, cart2d_sim):
    grid = cart2d_sim.grid
    f = grid.XX ** 2 + grid.YY ** 2
    result = _apply(cart2d_fd.laplacian(), f)
    assert np.allclose(result[1:-1, 1:-1], 4.0)


def test_cartesian_ops_reject_cylindrical_grid(cyl2d_fd):
    with pytest.raises(TypeError):
        cyl2d_fd.ddx()
    with pytest.raises(TypeError):
        cyl2d_fd.ddy()
    with pytest.raises(TypeError):
        cyl2d_fd.del2_x()
    with pytest.raises(TypeError):
        cyl2d_fd.del2_y()


# ----- Cylindrical ------------------------------------------------------------

def test_ddr_shape(cyl2d_fd, cyl2d_sim):
    Nr, Nz = cyl2d_sim.grid.Nr, cyl2d_sim.grid.Nz
    assert cyl2d_fd.ddr().shape == (Nr * Nz, Nr * Nz)


def test_ddr_on_linear_r(cyl2d_fd, cyl2d_sim):
    grid = cyl2d_sim.grid
    f = grid.RR.copy()  # f(r, z) = r; df/dr = 1
    result = _apply(cyl2d_fd.ddr(), f)
    assert np.allclose(result[1:-1, :], 1.0)


def test_ddz_on_linear_z(cyl2d_fd, cyl2d_sim):
    grid = cyl2d_sim.grid
    f = grid.ZZ.copy()
    result = _apply(cyl2d_fd.ddz(), f)
    assert np.allclose(result[:, 1:-1], 1.0)


def test_del2_z_on_quadratic_z(cyl2d_fd, cyl2d_sim):
    grid = cyl2d_sim.grid
    f = grid.ZZ ** 2
    result = _apply(cyl2d_fd.del2_z(), f)
    assert np.allclose(result[:, 1:-1], 2.0)


def test_del2_r_on_quadratic_r(cyl2d_fd, cyl2d_sim):
    """d²/dr² + (1/r) d/dr applied to r² is 2 + (1/r)(2r) = 4 (exact for
    centered diff on quadratics)."""
    grid = cyl2d_sim.grid
    f = grid.RR ** 2
    result = _apply(cyl2d_fd.del2_r(), f)
    assert np.allclose(result[1:-1, :], 4.0)


def test_laplacian_cylindrical_on_r2_plus_z2(cyl2d_fd, cyl2d_sim):
    """∇² (r² + z²) = 4 + 2 = 6 in axisymmetric cylindrical coords."""
    grid = cyl2d_sim.grid
    f = grid.RR ** 2 + grid.ZZ ** 2
    result = _apply(cyl2d_fd.laplacian(), f)
    assert np.allclose(result[1:-1, 1:-1], 6.0)


def test_cylindrical_ops_reject_cartesian_grid(cart2d_fd):
    with pytest.raises(TypeError):
        cart2d_fd.ddr()
    with pytest.raises(TypeError):
        cart2d_fd.ddz()
    with pytest.raises(TypeError):
        cart2d_fd.del2_z()
    with pytest.raises(TypeError):
        cart2d_fd.del2_r()


# ---------------------------------------------------------------------------
# PoissonSolver2D
# ---------------------------------------------------------------------------

def _poisson2d_cart_sim(Nx=9, Ny=7):
    dic = {"Grid": {"coordinate_system": "cartesian2d",
                    "Nx": Nx, "Ny": Ny,
                    "x_min": 0.0, "x_max": 1.0,
                    "y_min": 0.0, "y_max": 1.0},
           **_clock_tools()}
    sim = Simulation(dic)
    sim.prepare_simulation()
    return sim


def _poisson2d_cyl_sim(Nr=9, Nz=7):
    dic = {"Grid": {"coordinate_system": "cylindrical2d",
                    "Nr": Nr, "Nz": Nz,
                    "r_min": 1.0, "r_max": 2.0,
                    "z_min": 0.0, "z_max": 1.0},
           **_clock_tools()}
    sim = Simulation(dic)
    sim.prepare_simulation()
    return sim


def test_poisson2d_init_rejects_1d_grid():
    dic = {"Grid": {"N": 5, "r_min": 0, "r_max": 1}, **_clock_tools()}
    sim = Simulation(dic)
    sim.prepare_simulation()
    with pytest.raises(TypeError):
        PoissonSolver2D(sim, {"type": "PoissonSolver2D"})


def test_poisson2d_solve_wrong_shape_raises():
    sim = _poisson2d_cart_sim()
    solver = PoissonSolver2D(sim, {"type": "PoissonSolver2D"})
    with pytest.raises(ValueError):
        solver.solve(np.zeros((3, 3)))


def test_poisson2d_cartesian_polynomial_solution_is_exact():
    """φ(x,y) = x(1-x)y(1-y) is exactly recovered because the centered-diff
    Laplacian is exact on quadratics. ∇²φ = -2y(1-y) - 2x(1-x)."""
    sim = _poisson2d_cart_sim(Nx=9, Ny=7)
    solver = PoissonSolver2D(sim, {"type": "PoissonSolver2D"})
    grid = sim.grid
    xx, yy = grid.XX, grid.YY
    phi_true = xx * (1.0 - xx) * yy * (1.0 - yy)
    source = -2.0 * yy * (1.0 - yy) - 2.0 * xx * (1.0 - xx)
    phi = solver.solve(source)
    np.testing.assert_allclose(phi, phi_true, atol=1e-10)


def test_poisson2d_cartesian_dirichlet_zero_on_all_edges():
    sim = _poisson2d_cart_sim()
    solver = PoissonSolver2D(sim, {"type": "PoissonSolver2D"})
    grid = sim.grid
    source = np.ones(grid.shape)  # arbitrary source
    phi = solver.solve(source)
    assert np.allclose(phi[0, :], 0.0)
    assert np.allclose(phi[-1, :], 0.0)
    assert np.allclose(phi[:, 0], 0.0)
    assert np.allclose(phi[:, -1], 0.0)


def test_poisson2d_cylindrical_polynomial_solution_is_exact():
    """φ(r,z) = (r-1)(2-r) z(1-z). ∇²φ in axisymmetric cyl. coords is exact
    for this quadratic in r plus the (1/r) d/dr term.

    fr(r) = -r² + 3r - 2  → fr' = 3 - 2r, fr'' = -2
    fz(z) = z - z²        → fz'' = -2
    ∇²φ = [fr'' + (1/r) fr'] fz + fr fz''
        = (-4 + 3/r) fz - 2 fr
    """
    sim = _poisson2d_cyl_sim(Nr=9, Nz=7)
    solver = PoissonSolver2D(sim, {"type": "PoissonSolver2D"})
    grid = sim.grid
    rr, zz = grid.RR, grid.ZZ
    fr = (rr - 1.0) * (2.0 - rr)
    fz = zz * (1.0 - zz)
    phi_true = fr * fz
    source = (-4.0 + 3.0 / rr) * fz - 2.0 * fr
    phi = solver.solve(source)
    np.testing.assert_allclose(phi, phi_true, atol=1e-10)


def test_poisson2d_cylindrical_dirichlet_zero_on_all_edges():
    sim = _poisson2d_cyl_sim()
    solver = PoissonSolver2D(sim, {"type": "PoissonSolver2D"})
    grid = sim.grid
    source = np.ones(grid.shape)
    phi = solver.solve(source)
    assert np.allclose(phi[0, :], 0.0)
    assert np.allclose(phi[-1, :], 0.0)
    assert np.allclose(phi[:, 0], 0.0)
    assert np.allclose(phi[:, -1], 0.0)
