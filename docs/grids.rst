Grids
=====

turboPy grids provide the spatial discretization over which physics
modules solve their equations.  All grid types share a common abstract
base class, :class:`turbopy.core.GridBase`, and are dispatched from
the ``"coordinate_system"`` key of the ``"Grid"`` input dict by
:meth:`turbopy.core.Simulation.read_grid_from_input`.

Abstract base: ``GridBase``
---------------------------

Every grid class inherits from :class:`~turbopy.core.GridBase` and must
implement:

* :meth:`~turbopy.core.GridBase.generate_field` — allocate a zero-filled
  :class:`numpy.ndarray` shaped for the grid, at a requested point
  placement.
* :meth:`~turbopy.core.GridBase.create_interpolator` — return a callable
  that interpolates a field on this grid to a requested point.

The class attribute :attr:`~turbopy.core.GridBase.coordinate_system`
identifies the grid type.

Two useful ``isinstance`` idioms:

* ``isinstance(grid, GridBase)`` — accepts any grid type; use this in
  code that just needs "some grid" (e.g., diagnostics that handle 1D
  and 2D grids).
* ``isinstance(grid, Grid)`` — matches only the 1D
  :class:`~turbopy.core.Grid`; use this to gate 1D-only algorithms.

1D grids: ``Grid``
------------------

:class:`turbopy.core.Grid` is the built-in 1D grid.  Its
``"coordinate_system"`` may be ``"cartesian"``, ``"cylindrical"``, or
``"spherical"``.  These three options share the same set of grid points
but differ in their volume/area elements:

* ``"cartesian"`` — ``cell_volumes = cell_widths``,
  ``interface_areas = 1``.
* ``"cylindrical"`` — ``cell_volumes = pi * (r_{i+1}^2 - r_i^2)``,
  ``interface_areas = 2 pi r``.
* ``"spherical"`` — ``cell_volumes = (4/3) pi (r_{i+1}^3 - r_i^3)``,
  ``interface_areas = 4 pi r^2``.

Input parameters accepted:

* ``"N"`` (`int`) or exactly one of ``"dr"``/``"dx"`` (`float`).
* ``"min"``, ``"x_min"``, or ``"r_min"``.
* ``"max"``, ``"x_max"``, or ``"r_max"``.

Example::

    {"Grid": {"N": 101, "r_min": 0.0, "r_max": 1.0,
              "coordinate_system": "cylindrical"}}

Useful attributes of a 1D grid:
:attr:`~turbopy.core.Grid.r`,
:attr:`~turbopy.core.Grid.cell_edges`,
:attr:`~turbopy.core.Grid.cell_centers`,
:attr:`~turbopy.core.Grid.cell_widths`,
:attr:`~turbopy.core.Grid.cell_volumes`,
:attr:`~turbopy.core.Grid.interface_areas`,
:attr:`~turbopy.core.Grid.r_inv`.

Field placement on ``Grid``:
:meth:`~turbopy.core.Grid.generate_field` accepts
``placement_of_points="edge-centered"`` (default; shape
``(num_points,)``) or ``"cell-centered"`` (shape ``(num_points - 1,)``).

2D Cartesian: ``Grid2DCartesian``
---------------------------------

Selected with ``"coordinate_system": "cartesian2d"``.
See :class:`turbopy.core.Grid2DCartesian`.

Input parameters:

* Exactly one of ``"Nx"`` or ``"dx"``, plus ``"x_min"``, ``"x_max"``.
* Exactly one of ``"Ny"`` or ``"dy"``, plus ``"y_min"``, ``"y_max"``.

Example::

    {"Grid": {"coordinate_system": "cartesian2d",
              "Nx": 64, "x_min": 0.0, "x_max": 1.0,
              "Ny": 32, "y_min": 0.0, "y_max": 0.5}}

Notable attributes: :attr:`~turbopy.core.Grid2DCartesian.x`,
:attr:`~turbopy.core.Grid2DCartesian.y`,
:attr:`~turbopy.core.Grid2DCartesian.x_centers`,
:attr:`~turbopy.core.Grid2DCartesian.y_centers`,
:attr:`~turbopy.core.Grid2DCartesian.x_widths`,
:attr:`~turbopy.core.Grid2DCartesian.y_widths`,
:attr:`~turbopy.core.Grid2DCartesian.XX`,
:attr:`~turbopy.core.Grid2DCartesian.YY`,
:attr:`~turbopy.core.Grid2DCartesian.cell_volumes` (``dx * dy``),
:attr:`~turbopy.core.Grid2DCartesian.shape` (``(Nx, Ny)``).

The meshgrid arrays use ``indexing='ij'``, so
``XX.shape == YY.shape == (Nx, Ny)``.

Field placement on ``Grid2DCartesian``:
:meth:`~turbopy.core.Grid2DCartesian.generate_field` accepts
``"edge-centered"`` (``(Nx, Ny)``), ``"cell-centered"``
(``(Nx-1, Ny-1)``), ``"x-edge-y-cell"`` (``(Nx, Ny-1)``), or
``"x-cell-y-edge"`` (``(Nx-1, Ny)``).

2D cylindrical: ``Grid2DCylindrical``
-------------------------------------

Selected with ``"coordinate_system": "cylindrical2d"``.
See :class:`turbopy.core.Grid2DCylindrical`.

This is a full 2D ``(r, z)`` grid — distinct from the 1D
``"cylindrical"`` :class:`~turbopy.core.Grid`, which is only the
radial coordinate.

Input parameters:

* Exactly one of ``"Nr"`` or ``"dr"``, plus ``"r_min"``, ``"r_max"``.
* Exactly one of ``"Nz"`` or ``"dz"``, plus ``"z_min"``, ``"z_max"``.

Example::

    {"Grid": {"coordinate_system": "cylindrical2d",
              "Nr": 33, "r_min": 0.0, "r_max": 1.0,
              "Nz": 65, "z_min": 0.0, "z_max": 2.0}}

Notable attributes: :attr:`~turbopy.core.Grid2DCylindrical.r`,
:attr:`~turbopy.core.Grid2DCylindrical.z`,
:attr:`~turbopy.core.Grid2DCylindrical.RR`,
:attr:`~turbopy.core.Grid2DCylindrical.ZZ`,
:attr:`~turbopy.core.Grid2DCylindrical.r_inv`,
:attr:`~turbopy.core.Grid2DCylindrical.r_inv_2d`,
:attr:`~turbopy.core.Grid2DCylindrical.cell_volumes` (annular:
``pi (r_{i+1}^2 - r_i^2) dz_j``).

Field placement on ``Grid2DCylindrical``:
:meth:`~turbopy.core.Grid2DCylindrical.generate_field` accepts
``"edge-centered"`` (``(Nr, Nz)``), ``"cell-centered"``
(``(Nr-1, Nz-1)``), ``"r-edge-z-cell"`` (``(Nr, Nz-1)``), or
``"r-cell-z-edge"`` (``(Nr-1, Nz)``).

Allocating and interpolating fields
-----------------------------------

::

    from turbopy import Simulation

    sim = Simulation(input_data)
    sim.prepare_simulation()  # or sim.run()

    # allocate a zero-filled field
    E = sim.grid.generate_field(num_components=3,
                                placement_of_points="edge-centered")

    # get a bilinear interpolator to a specific point
    sample = sim.grid.create_interpolator((0.3, 0.2))
    value_at_point = sample(some_field_2d)

Writing grid-agnostic code
--------------------------

::

    from turbopy.core import GridBase, Grid

    def is_2d(grid: GridBase) -> bool:
        return not isinstance(grid, Grid)
