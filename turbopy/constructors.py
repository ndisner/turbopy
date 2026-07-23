"""Helpers for constructing :class:`~turbopy.core.Simulation` objects.

This module provides high-level entry points for turning a
serialized configuration into a runnable
:class:`~turbopy.core.Simulation`.

The only file format supported today is TOML, parsed with the
:mod:`qtoml` library.  A TOML file must be structured as a nested
mapping matching the ``input_data`` dictionary described in
:class:`turbopy.core.Simulation` -- with top-level tables for
``Grid``, ``Clock``, ``Tools``, ``PhysicsModules``, and
``Diagnostics``.  See the narrative overview at
:doc:`/input_files` for a full example.
"""
import qtoml as toml

from .core import Simulation

def construct_simulation_from_toml(filename: str) -> Simulation:
    """Construct a :class:`~turbopy.core.Simulation` from a TOML file.

    Parameters
    ----------
    filename : str
        Path to a TOML input file.  The file is parsed with
        :mod:`qtoml` and the resulting nested dictionary is passed
        directly to :class:`~turbopy.core.Simulation`.

    Returns
    -------
    Simulation
        A fully constructed but *not yet initialized*
        :class:`~turbopy.core.Simulation`.  Call
        :meth:`~turbopy.core.Simulation.run` (or
        :meth:`~turbopy.core.Simulation.prepare_simulation`) to
        actually execute the simulation.
    """
    with open(filename) as f:
        input_data = toml.load(f)

    return Simulation(input_data)
