# turboPy — 2D Grid / Finite Difference / Poisson Design Record

Design document for the 2D infrastructure added in the `2D-grid` and
`2D-Solve` branches. Captures the mathematical formulation, discrete operators,
data-layout conventions, boundary handling, and verification strategy for:

- `Grid2DCartesian`, `Grid2DCylindrical` — 2D grid classes ([turbopy/core.py](turbopy/core.py))
- `FiniteDifference2D` — sparse Kronecker-product operators ([turbopy/computetools.py](turbopy/computetools.py))
- `PoissonSolver2D` — direct Dirichlet Poisson solve ([turbopy/computetools.py](turbopy/computetools.py))

Intended audience: turboPy contributors extending or reviewing the 2D stack.
For user-facing API summaries see [CLAUDE.md](CLAUDE.md); for branch-status
notes see [NOTES.md](NOTES.md).

---

## 1. Scope and Motivation

turboPy's original `Grid` class is one-dimensional (Cartesian, cylindrical-
radial, or spherical). Prototype problems that need a genuinely 2D field
solve — e.g. axisymmetric electrostatics, transverse Laplacians — previously
required workarounds. The 2D stack adds a small, self-contained set of
classes that:

1. Represent 2D uniform grids in Cartesian `(x, y)` and axisymmetric
   cylindrical `(r, z)` coordinates.
2. Build discrete first- and second-order derivative operators as sparse
   matrices, so they can be reused across compute tools and solvers.
3. Provide a Dirichlet Poisson solve on those grids as a first concrete
   application.

Design constraints:

- **No new dependencies.** Everything is built from `numpy` and `scipy.sparse`.
- **Fits the existing hierarchy.** New classes plug in via the same
  `GridBase` / `ComputeTool` / registry pattern as everything else — no
  changes to `Simulation`, no changes to how modules request resources.
- **Backward compatibility.** The 1D `Grid` and `FiniteDifference` classes
  are untouched. `HistoryDiagnostic` retains its 1D path and gains new 2D
  branches.

---

## 2. 2D Grids

### 2.1 Common conventions

Both 2D grid classes are subclasses of `GridBase` and share a strict set of
conventions used by every downstream operator and diagnostic:

| Convention | Value |
|---|---|
| Meshgrid indexing | `numpy.meshgrid(..., indexing='ij')` |
| Field shape | `(N1, N2)` where axis 0 is the "outer" coordinate |
| Flatten order | `field.ravel(order='C')` → row-major |
| Reshape back | `flat.reshape((N1, N2))` |
| Placement default | `"edge-centered"` (fields live on the `N1 × N2` node grid) |
| Grid spacing | Uniform along each axis (`dx`, `dy`, `dr`, `dz`) |

For a Cartesian grid: axis 0 = `x`, axis 1 = `y`, so `shape == (Nx, Ny)`.
For a cylindrical grid: axis 0 = `r`, axis 1 = `z`, so `shape == (Nr, Nz)`.

The `'ij'` indexing choice and the `'C'` flatten order together imply that
in the flattened vector, index `k = i * N2 + j` corresponds to grid point
`(i, j)`. This drives the Kronecker-product ordering used by
`FiniteDifference2D` (see §3.1).

### 2.2 `Grid2DCartesian`

Input schema (`"coordinate_system": "cartesian2d"`):

```
Nx | dx , Ny | dy , x_min, x_max, y_min, y_max
```

Grid points are uniform:

$$
x_i = x_{\min} + i\,\Delta x, \quad i = 0, \dots, N_x - 1, \quad \Delta x = \frac{x_{\max} - x_{\min}}{N_x - 1}
$$

Cell volumes (areas) are the tensor product of 1D widths:

$$
V_{ij} = \Delta x_i \cdot \Delta y_j, \quad V \in \mathbb{R}^{(N_x - 1) \times (N_y - 1)}
$$

Edge-centered field placement is the default; three staggered variants are
available via `generate_field(placement_of_points=...)`:

- `"edge-centered"`   → `(Nx, Ny)`
- `"cell-centered"`   → `(Nx-1, Ny-1)`
- `"x-edge-y-cell"`   → `(Nx, Ny-1)`
- `"x-cell-y-edge"`   → `(Nx-1, Ny)`

`create_interpolator((x0, y0))` returns a bilinear interpolation closure
for edge-centered fields:

$$
f(x_0, y_0) \approx (1 - t_x)(1 - t_y)\,f_{00} + t_x(1 - t_y)\,f_{10} + (1 - t_x)t_y\,f_{01} + t_x t_y\,f_{11}
$$

with $t_x = (x_0 - x_i) / \Delta x$, $t_y = (y_0 - y_j) / \Delta y$.

### 2.3 `Grid2DCylindrical`

Input schema (`"coordinate_system": "cylindrical2d"`):

```
Nr | dr , Nz | dz , r_min, r_max, z_min, z_max
```

This is the **axisymmetric** cylindrical grid — fields have no $\theta$
dependence — and is distinct from the 1D `"cylindrical"` grid, which is
purely radial. Uniform edges:

$$
r_i = r_{\min} + i\,\Delta r, \quad z_j = z_{\min} + j\,\Delta z
$$

**Annular cell volumes** (proper axisymmetric volume element):

$$
V_{ij} = \pi \left( r_{i+1}^2 - r_i^2 \right) \Delta z_j, \quad V \in \mathbb{R}^{(N_r - 1) \times (N_z - 1)}
$$

**Radial reciprocal (`r_inv`, `r_inv_2d`).**  The $1/r$ coefficient appears
in the cylindrical Laplacian and in vector operators. To keep operators
finite when the domain includes the axis ($r = 0$), we define:

$$
r^{-1}_i \;=\; \begin{cases} 1 / r_i & r_i \ne 0 \\ 0 & r_i = 0 \end{cases}
$$

The value at $r = 0$ is *not* mathematically $1/r$; it is a placeholder
that yields a well-defined discrete operator. When it multiplies a
correctly discretized $\partial/\partial r$ that vanishes on the axis by
symmetry, the product remains finite. Callers whose analytic reference
does not vanish at $r = 0$ should place the domain off-axis (as the tests
do; see §5.2).

`r_inv_2d` is the `(Nr, Nz)` broadcast of `r_inv` along the $z$ axis and
is used directly in `FiniteDifference2D.del2_r()`.

### 2.4 Dispatch and registration

`Simulation.read_grid_from_input()` dispatches on the `"coordinate_system"`
key of the `Grid` input dict:

- `"cartesian"`, `"cylindrical"`, `"spherical"` → 1D `Grid`
- `"cartesian2d"` → `Grid2DCartesian`
- `"cylindrical2d"` → `Grid2DCylindrical`

Downstream code that wants to accept any grid uses
`isinstance(grid, GridBase)`; code that must distinguish 1D from 2D uses
`isinstance(grid, Grid)` for 1D.

---

## 3. `FiniteDifference2D`

Sparse-matrix finite-difference operators on 2D grids. All operators are
returned as `scipy.sparse.csr_matrix` of shape `(N1*N2, N1*N2)`; the caller
flattens/reshapes in `'C'` order.

### 3.1 Kronecker-product formulation

Let $D_1 \in \mathbb{R}^{N_1 \times N_1}$ and $D_2 \in \mathbb{R}^{N_2 \times N_2}$
be 1D operators along axis 0 and axis 1 respectively. For a field
$F \in \mathbb{R}^{N_1 \times N_2}$ with flat vector $f = \text{vec}(F)$
(row-major), the 2D operators are:

$$
\partial_{a_1} F \;\;\longleftrightarrow\;\; (D_1 \otimes I_{N_2}) f
$$

$$
\partial_{a_2} F \;\;\longleftrightarrow\;\; (I_{N_1} \otimes D_2) f
$$

The row-major convention pairs with `kron(D1, I)` (not `kron(I, D1)`); this
is the source of the "outer axis first" ordering throughout.

### 3.2 1D building blocks

Two private helpers construct the 1D operator ingredients on uniform
spacing $h$:

**Centered first derivative** — three-point, second-order accurate on
interior nodes:

$$
(D f)_i = \frac{f_{i+1} - f_{i-1}}{2h}, \quad i = 1, \dots, N-2
$$

Boundary rows are left as degenerate one-sided stencils (missing neighbor
treated as zero). This is acceptable when the operator's boundary rows
are later overridden by a solver (as in `PoissonSolver2D`); callers using
these operators standalone for open-boundary problems must supply their
own boundary treatment. This is a known limitation (see §6).

**Three-point Laplacian** — second-order accurate on interior nodes,
*exact* on quadratics:

$$
(L f)_i = \frac{f_{i-1} - 2 f_i + f_{i+1}}{h^2}
$$

Same boundary caveat.

### 3.3 Cartesian operators

For a `Grid2DCartesian`:

| Method | Continuous | Sparse form |
|---|---|---|
| `ddx()` | $\partial / \partial x$ | $D_x \otimes I_{N_y}$ |
| `ddy()` | $\partial / \partial y$ | $I_{N_x} \otimes D_y$ |
| `del2_x()` | $\partial^2 / \partial x^2$ | $L_x \otimes I_{N_y}$ |
| `del2_y()` | $\partial^2 / \partial y^2$ | $I_{N_x} \otimes L_y$ |
| `laplacian()` | $\nabla^2 = \partial^2/\partial x^2 + \partial^2/\partial y^2$ | `del2_x() + del2_y()` |

Each `ddx`/`del2_x`-family method raises `TypeError` if called on a
cylindrical grid, and vice versa.

### 3.4 Cylindrical operators (axisymmetric)

For a `Grid2DCylindrical`, using $\partial/\partial\theta = 0$:

| Method | Continuous | Sparse form |
|---|---|---|
| `ddr()` | $\partial / \partial r$ | $D_r \otimes I_{N_z}$ |
| `ddz()` | $\partial / \partial z$ | $I_{N_r} \otimes D_z$ |
| `del2_z()` | $\partial^2 / \partial z^2$ | $I_{N_r} \otimes L_z$ |
| `del2_r()` | $\partial^2/\partial r^2 + (1/r)\,\partial/\partial r$ | $L_r \otimes I_{N_z} \;+\; \mathrm{diag}(r^{-1}) \cdot (D_r \otimes I_{N_z})$ |
| `laplacian()` | $\nabla^2 = \partial^2/\partial r^2 + (1/r)\,\partial/\partial r + \partial^2/\partial z^2$ | `del2_r() + del2_z()` |

The radial Laplacian derivation is the standard axisymmetric reduction:

$$
\nabla^2 \phi = \frac{1}{r} \frac{\partial}{\partial r}\!\left(r\,\frac{\partial \phi}{\partial r}\right) + \frac{\partial^2 \phi}{\partial z^2} \;=\; \frac{\partial^2 \phi}{\partial r^2} + \frac{1}{r}\,\frac{\partial \phi}{\partial r} + \frac{\partial^2 \phi}{\partial z^2}
$$

The $1/r$ factor is applied as a left multiplication by a diagonal matrix
built from `grid.r_inv_2d.ravel('C')`, which is zero on the axis (§2.3).

### 3.5 Design choice: two-form Laplacian vs. conservative form

We use the **non-conservative** form
$\partial_r^2 + (1/r)\partial_r$ rather than the conservative form
$(1/r)\partial_r(r\,\partial_r)$. Both are analytically equivalent; the
non-conservative form gives a simpler sparse pattern (identical 3-point
stencils on each row with an added weighted first-derivative row), and it
matches how the Cartesian Laplacian is assembled from single-axis pieces.
For strongly non-uniform fields the conservative form has better
discrete conservation properties; if a future application needs that, it
would go alongside `del2_r` rather than replacing it.

---

## 4. `PoissonSolver2D`

Solves the 2D Poisson equation with homogeneous Dirichlet boundary
conditions:

$$
\nabla^2 \phi(\mathbf{x}) = s(\mathbf{x}) \quad \text{in } \Omega
\qquad \phi = 0 \quad \text{on } \partial\Omega
$$

on either `Grid2DCartesian` or `Grid2DCylindrical`. This is v1; extensions
to non-zero Dirichlet, Neumann, and mixed BCs are deferred (see
[NOTES.md](NOTES.md)).

### 4.1 Discretization

Let $A_0 \in \mathbb{R}^{N \times N}$ be the discrete Laplacian on the
full grid, $N = N_1 \cdot N_2$, obtained from
`FiniteDifference2D.laplacian()`. Its boundary rows are degenerate
(§3.2). Let $\mathcal{B}$ be the set of flat indices that lie on the
grid boundary (top, bottom, left, right).

Define the **BC-projected operator** $A$:

$$
A_{k,l} = \begin{cases} 1 & k \in \mathcal{B},\; l = k \\ 0 & k \in \mathcal{B},\; l \ne k \\ (A_0)_{k,l} & k \notin \mathcal{B} \end{cases}
$$

and the **BC-projected source** $\tilde s$:

$$
\tilde s_k = \begin{cases} 0 & k \in \mathcal{B} \\ s_k & k \notin \mathcal{B} \end{cases}
$$

Then $\phi$ is the solution of

$$
A\,\phi = \tilde s
$$

which enforces $\phi_k = 0$ for boundary indices exactly (the boundary
row reads $1 \cdot \phi_k = 0$).

### 4.2 Assembly

`__init__` performs a one-time assembly:

1. Get `L = FiniteDifference2D(...).laplacian()` (dispatched on grid type,
   §3).
2. Compute the boundary mask (all four edges of the `(N1, N2)` grid) and
   flatten in `'C'` order.
3. Convert `L` to `lil_matrix` for cheap row assignment; for each boundary
   flat index $k$ replace row $k$ with the identity row (`rows[k] = [k]`,
   `data[k] = [1.0]`).
4. Convert the modified operator back to `csr_matrix` and store it as
   `self._operator`.

The BC mask is stored alongside so that `solve()` can zero the RHS entries
without re-assembling.

### 4.3 Solve

`solve(source)`:

1. Check that `source.shape == grid.shape`; raise `ValueError` otherwise.
2. Flatten in `'C'` order and cast to float; zero the boundary entries.
3. `phi_flat = scipy.sparse.linalg.spsolve(self._operator, rhs)`.
4. Reshape back to `grid.shape` and return.

`spsolve` is a **direct sparse LU** solve. This is exact (up to floating
point), correct for both symmetric-Cartesian and non-symmetric-cylindrical
operators, and fast enough for the fixture-scale grids used in tests
(`Nx*Ny` up to ~100). For production-scale runs an iterative method with
an appropriate preconditioner would be more appropriate; see the deferred
scale-out item in [NOTES.md](NOTES.md).

### 4.4 Design choices

- **Direct solver over iterative.** For a first implementation, `spsolve`
  is a one-line call with no tuning knobs. Iterative solvers (CG for the
  symmetric Cartesian operator, BiCGStab for the non-symmetric cylindrical
  operator) need a preconditioner to be worth the complexity at any
  reasonable resolution; that decision waits for a real use-case.
- **Row-replacement BC over row-elimination.** We keep the boundary rows
  in the matrix (as identity rows) rather than removing them and solving
  a smaller system. This preserves the flat-index / grid-shape mapping
  everywhere and lets the caller pass in a full-shape source without
  bookkeeping.
- **Always zero the RHS at the boundary.** Because $A$ has identity
  boundary rows, whatever value we put in the RHS at those indices is
  the boundary value of $\phi$. Zeroing enforces $\phi = 0$ on all edges,
  which is the only supported BC in v1. When non-zero Dirichlet is added,
  this step becomes "write the boundary value to the RHS at that index."
- **Assemble once, solve many.** `__init__` builds and stores the
  BC-projected operator, so repeated `solve()` calls only pay for the
  factorization + back-substitution inside `spsolve`. (Caching the LU
  factorization across calls is a further optimization we haven't taken.)

---

## 5. Verification

### 5.1 `FiniteDifference2D` — polynomial reference solutions

Centered finite-difference stencils are **exact on polynomials up to their
order** — the 3-point centered first derivative is exact on linears; the
3-point Laplacian is exact on quadratics. Tests exploit this to assert to
floating-point tolerance (`atol=1e-10`) rather than a loose discretization
tolerance. Coverage:

- Shape and dtype checks on every operator.
- `ddx` / `ddy` / `ddr` / `ddz` applied to their respective linear fields
  should return the constant slope on interior nodes.
- `del2_x` / `del2_y` / `del2_z` applied to quadratics along each axis
  should return the constant second derivative on interior nodes.
- `del2_r` applied to a radial polynomial with a known
  $\partial_r^2 + (1/r)\partial_r$ evaluation.
- Full Cartesian Laplacian on $x^2 + y^2$ returns a constant.
- Full cylindrical Laplacian on $r^2 + z^2$ returns
  $\partial_r^2(r^2) + (1/r)\partial_r(r^2) + \partial_z^2(z^2) = 2 + 2 + 2 = 6$.
- Type-guard tests: every Cartesian method raises on cylindrical grids;
  every cylindrical method raises on Cartesian grids; both classes' 1D
  rejection is covered.

Interior nodes only (boundary rows are degenerate; see §3.2).

### 5.2 `PoissonSolver2D` — manufactured solutions

Uses the same "quadratic-exact" trick. For each supported grid type we
manufacture a $\phi$ that vanishes on all four boundaries, compute the
analytical source $s = \nabla^2 \phi$, run the solver on $s$, and assert
that the reconstructed $\phi$ matches to floating-point tolerance.

**Cartesian** — on $[0, 1] \times [0, 1]$:

$$
\phi(x, y) = x(1 - x)\,y(1 - y)
$$

$$
s(x, y) = \nabla^2 \phi = -2 y(1 - y) - 2 x(1 - x)
$$

Both sides are polynomials of degree $\le 2$ in each variable, so the
3-point Laplacian is exact.

**Cylindrical** — on $r \in [1, 2]$, $z \in [0, 1]$ (deliberately
**off-axis** so the analytic $1/r$ term is finite and the reference is
unambiguous):

$$
\phi(r, z) = (r - 1)(2 - r)\,z(1 - z)
$$

The radial factor $f_r(r) = (r-1)(2-r) = -r^2 + 3r - 2$ gives
$f_r' = -2r + 3$, $f_r'' = -2$; the axial factor $f_z(z) = z(1-z)$ gives
$f_z'' = -2$. Then:

$$
\nabla^2 \phi \;=\; f_z\!\left(f_r'' + \tfrac{1}{r} f_r'\right) + f_r f_z'' \;=\; f_z\!\left(-2 + \tfrac{-2r + 3}{r}\right) + f_r\,(-2)
$$

Rewriting the parenthesis, $-2 + (-2r + 3)/r = -4 + 3/r$, so

$$
s(r, z) = \left(-4 + \tfrac{3}{r}\right) z(1 - z) \;-\; 2 (r - 1)(2 - r)
$$

The solver reconstructs $\phi$ to `atol=1e-10`. Both tests also check
$\phi = 0$ on all four edges independently.

Additional coverage: shape mismatch raises `ValueError`; 1D grid at
construction raises `TypeError`.

### 5.3 Test topology

| File | Class / Feature | Tests |
|---|---|---|
| [tests/test_computetools.py](tests/test_computetools.py) | `FiniteDifference2D` | 15 |
| [tests/test_computetools.py](tests/test_computetools.py) | `PoissonSolver2D` | 6 |
| [tests/test_diagnostics.py](tests/test_diagnostics.py) | `HistoryDiagnostic` 2D | 2 |
| [tests/test_core.py](tests/test_core.py) | `Grid2DCartesian`, `Grid2DCylindrical` | (from PR #189) |

Full suite: 128 tests, all green.

---

## 6. Known Limitations and Follow-ups

Recorded here in enough detail that a future contributor can pick them up
without re-deriving the current shape of things. See [NOTES.md](NOTES.md)
for the branch-level task list.

- **Boundary rows of `_centered_diff_1d` and `_laplacian_1d`.** Row 0 and
  row $N-1$ have a missing neighbor treated as zero. This is *not* a
  one-sided stencil — the row is simply truncated. It's fine when the
  boundary rows are overridden downstream (as in `PoissonSolver2D`) or
  when the caller only inspects interior nodes. For genuine open-boundary
  problems this needs to be either (a) explicit one-sided stencils per
  operator, or (b) a shared BC-application helper that the caller invokes
  after building the raw operator.
- **Cell-centered operators.** Current operators assume edge-centered
  fields (shape `(N1, N2)`). Cell-centered variants (shape `(N1-1, N2-1)`)
  would require rebuilding all 1D pieces on the corresponding grid.
- **Non-Dirichlet Poisson BCs.** Adding non-zero Dirichlet is a small
  patch (write the boundary value to the RHS instead of 0). Neumann /
  mixed BCs require touching the operator rows and possibly reconsidering
  the row-replacement scheme; a cleaner abstraction is a per-edge BC
  object.
- **Poisson scale-out.** Direct `spsolve` is $O(N^{1.5})$ for 2D grids;
  fine below ~10⁵ unknowns. Above that, prefer CG (Cartesian, SPD) or
  BiCGStab / GMRES (cylindrical, non-symmetric) with an ILU or algebraic
  multigrid preconditioner. Any switch should be benchmarked on a fixture
  matching the target use-case.
- **`HistoryDiagnostic` on 2D vector/tensor fields.** Only scalar 2D
  fields are exercised end-to-end. Multi-component storage on 2D grids
  should be verified before it's relied on.
- **Sphinx documentation.** The 2D API (`Grid2DCartesian`,
  `Grid2DCylindrical`, `FiniteDifference2D`, `PoissonSolver2D`) does not
  yet have Sphinx pages under `docs/`; the CLAUDE.md summary is the
  current source of truth.
- **Unified `laplacian()` for 1D and 2D.** 1D users go through
  `FiniteDifference`; 2D users through `FiniteDifference2D`. A dispatch
  wrapper would give a single entry point, but the split is intentional
  today because the underlying operator shapes differ.

---

## 7. File Index

| File | Role |
|---|---|
| [turbopy/core.py](turbopy/core.py) | `GridBase`, `Grid2DCartesian`, `Grid2DCylindrical` |
| [turbopy/computetools.py](turbopy/computetools.py) | `FiniteDifference2D`, `PoissonSolver2D` |
| [turbopy/diagnostics.py](turbopy/diagnostics.py) | `HistoryDiagnostic` 2D coord attachment |
| [tests/test_core.py](tests/test_core.py) | 2D grid unit tests |
| [tests/test_computetools.py](tests/test_computetools.py) | FD2D and PoissonSolver2D tests |
| [tests/test_diagnostics.py](tests/test_diagnostics.py) | HistoryDiagnostic 2D tests |
| [CLAUDE.md](CLAUDE.md) | User-facing API summary |
| [NOTES.md](NOTES.md) | Branch-level changelog + follow-ups |
