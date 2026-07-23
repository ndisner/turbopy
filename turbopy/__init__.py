"""turboPy: a lightweight computational-physics framework.

turboPy organizes a simulation around a small set of cooperating
classes:

* :class:`turbopy.core.Simulation` -- the top-level container that
  owns the grid, clock, physics modules, compute tools, and
  diagnostics, and drives the main loop.
* :class:`turbopy.core.PhysicsModule` -- user-supplied physical
  dynamics; must implement :meth:`~turbopy.core.PhysicsModule.update`.
* :class:`turbopy.core.ComputeTool` -- reusable numerical kernels
  (finite differences, particle pushers, Poisson solvers, ...).
* :class:`turbopy.core.Diagnostic` -- data-collection / output
  hooks fired every step.
* :class:`turbopy.core.DynamicFactory` -- the registry base class
  that lets :class:`~turbopy.core.Simulation` construct components
  by name from an input dictionary.

Public re-exports
-----------------

Everything from :mod:`turbopy.core`, :mod:`turbopy.diagnostics`,
:mod:`turbopy.computetools`, and :mod:`turbopy.constructors` is
re-exported at the package top level.  For example::

    from turbopy import Simulation, PhysicsModule, ComputeTool, Diagnostic
    from turbopy import Grid, Grid2DCartesian, Grid2DCylindrical
    from turbopy import construct_simulation_from_toml

See :mod:`turbopy.core`, :mod:`turbopy.computetools`,
:mod:`turbopy.diagnostics`, and :mod:`turbopy.constructors` for the
full public API.
"""
from .__version__ import __version__
from .core import *
from .diagnostics import *
from .computetools import *
from .constructors import *
