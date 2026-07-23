Input Files
===========

A turboPy simulation is fully described by a nested dictionary.  You
can either build that dictionary in Python and pass it directly to
:class:`turbopy.core.Simulation`, or you can read it from a TOML file
via :func:`turbopy.constructors.construct_simulation_from_toml`.

Loading from a TOML file
------------------------

::

    from turbopy import construct_simulation_from_toml

    sim = construct_simulation_from_toml("my_input.toml")
    sim.run()

Internally, :func:`~turbopy.constructors.construct_simulation_from_toml`
uses :mod:`qtoml` to parse the file into a dict, then passes it to
:class:`~turbopy.core.Simulation`.

Top-level keys
--------------

The input dict has up to five top-level keys.  All except
``"PhysicsModules"`` are optional.

``"Grid"`` (optional)
    Grid configuration.  If omitted, the simulation runs "gridless"
    (a warning is emitted, and :attr:`Simulation.grid` remains
    ``None``).  The ``"coordinate_system"`` sub-key selects the grid
    class:

    * ``"cartesian"`` (default), ``"cylindrical"``, or ``"spherical"``
      -> 1D :class:`~turbopy.core.Grid`.
    * ``"cartesian2d"`` -> :class:`~turbopy.core.Grid2DCartesian`.
    * ``"cylindrical2d"`` -> :class:`~turbopy.core.Grid2DCylindrical`.

    See :doc:`grids` for the parameters each grid class accepts.

``"Clock"`` (required)
    Time integration configuration.  See :doc:`clock` for the keys.

``"Tools"`` (optional)
    Dictionary of :class:`~turbopy.core.ComputeTool` instances to
    construct.  Each key is the registered tool name; each value is
    either a single dict of parameters or a *list* of dicts (to
    create multiple instances of the same tool, typically
    distinguished with a ``"custom_name"``).  See :doc:`compute_tools`.

``"PhysicsModules"`` (required in practice)
    Dictionary of :class:`~turbopy.core.PhysicsModule` instances to
    construct.  Each key is the registered module name; each value is
    a dict of parameters.  See :doc:`physics_modules`.

``"Diagnostics"`` (optional)
    Dictionary of :class:`~turbopy.core.Diagnostic` instances plus
    default parameters.  Entries whose key is a registered diagnostic
    name are constructed; other entries are merged into every
    diagnostic's parameter dict as defaults (see
    :doc:`diagnostics`).

Example TOML input
------------------

.. code-block:: toml

    [Grid]
    N = 101
    r_min = 0.0
    r_max = 1.0
    coordinate_system = "cylindrical"

    [Clock]
    start_time = 0.0
    end_time = 1.0
    num_steps = 1000

    [Tools.FiniteDifference]
    method = "centered"

    [PhysicsModules.HarmonicOscillator]
    k = 1.0
    mass = 1.0

    [Diagnostics]
    directory = "output/"

    [Diagnostics.grid]
    filename = "grid.csv"

    [Diagnostics.clock]
    filename = "time.csv"

Equivalent Python dict
----------------------

::

    input_data = {
        "Grid": {"N": 101, "r_min": 0.0, "r_max": 1.0,
                 "coordinate_system": "cylindrical"},
        "Clock": {"start_time": 0.0, "end_time": 1.0, "num_steps": 1000},
        "Tools": {"FiniteDifference": {"method": "centered"}},
        "PhysicsModules": {"HarmonicOscillator": {"k": 1.0, "mass": 1.0}},
        "Diagnostics": {
            "directory": "output/",
            "grid":  {"filename": "grid.csv"},
            "clock": {"filename": "time.csv"},
        },
    }

    from turbopy import Simulation
    Simulation(input_data).run()
