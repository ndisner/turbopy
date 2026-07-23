The Simulation Clock
====================

The :class:`turbopy.core.SimulationClock` drives the main loop.  It is
constructed from the ``"Clock"`` entry in the input dict during
:meth:`~turbopy.core.Simulation.read_clock_from_input`.

Configuration
-------------

The clock accepts the following keys:

* ``"start_time"`` (`float`) — clock start time.
* ``"end_time"`` (`float`) — clock end time.
* Exactly one of ``"num_steps"`` (`int`) or ``"dt"`` (`float`).
* ``"print_time"`` (`bool`, optional; default ``False``) — if ``True``,
  the clock prints the current time on every
  :meth:`~turbopy.core.SimulationClock.advance` call.

Example input::

    {
        "Clock": {
            "start_time": 0.0,
            "end_time": 1.0,
            "num_steps": 1000,
            "print_time": False,
        },
        ...
    }

Or with a fixed step size::

    {
        "Clock": {
            "start_time": 0.0,
            "end_time": 1.0,
            "dt": 1.0e-3,
        },
        ...
    }

When ``"dt"`` is used, ``end_time - start_time`` must be an integer
multiple of ``dt``.  If it is not, the constructor raises
:class:`RuntimeError`.

Runtime API
-----------

While the simulation is running, the clock exposes:

* :meth:`~turbopy.core.SimulationClock.advance` — increment
  :attr:`~turbopy.core.SimulationClock.this_step` by 1 and recompute
  :attr:`~turbopy.core.SimulationClock.time` from
  ``start_time + dt * this_step``.  Called by
  :meth:`turbopy.core.Simulation.fundamental_cycle`.
* :meth:`~turbopy.core.SimulationClock.turn_back` — undo one or more
  steps.  Rarely needed in user code, but useful in modules that need
  to iterate to convergence within a step.
* :meth:`~turbopy.core.SimulationClock.is_running` — returns ``True``
  while ``this_step < num_steps``.

Reading the time from a module
------------------------------

Inside a :class:`~turbopy.core.PhysicsModule` or
:class:`~turbopy.core.Diagnostic`, the clock is reachable through the
owner::

    class MyModule(PhysicsModule):
        def update(self):
            t = self._owner.clock.time
            dt = self._owner.clock.dt
            ...
