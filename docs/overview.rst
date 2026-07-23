Framework Overview
==================

turboPy is organized around a small set of cooperating classes.  The
:class:`turbopy.core.Simulation` object owns everything and drives the
main time loop; user physics lives in :class:`turbopy.core.PhysicsModule`
subclasses; numerical kernels shared between modules live in
:class:`turbopy.core.ComputeTool` subclasses; and observation of the
running simulation is done through :class:`turbopy.core.Diagnostic`
subclasses.

The mental model
----------------

::

                                     +------------------+
                                     |    Simulation    |
                                     |------------------|
                                     | grid             |
                                     | clock            |
                                     | all_shared_...   |
                                     +---------+--------+
                                               |
                +------------------+-----------+-----------+----------------+
                |                  |                       |                |
        +-------v-------+  +-------v---------+     +-------v-------+   +----v-----+
        | PhysicsModule |  | PhysicsModule   |     |  ComputeTool  |   | Diagnos- |
        +---------------+  +-----------------+     +---------------+   |   tic    |
                |                  |                       ^           +----+-----+
                | update()         | update()              |                |
                +---- publishes ---+--- consumes shared ---+                |
                       resources        resources                  reads state
                                                                   writes files

Every step of the main loop, the simulation runs each diagnostic, then
calls :meth:`~turbopy.core.PhysicsModule.reset` on every module, then
calls :meth:`~turbopy.core.PhysicsModule.update` on every module, then
advances the :class:`~turbopy.core.SimulationClock`.  See
:doc:`simulation_lifecycle` for the full sequence.

The DynamicFactory registry pattern
-----------------------------------

:class:`~turbopy.core.PhysicsModule`, :class:`~turbopy.core.ComputeTool`,
and :class:`~turbopy.core.Diagnostic` are all subclasses of
:class:`~turbopy.core.DynamicFactory`.  A subclass becomes reachable from
input data (a Python dict, or a TOML file) by registering itself under a
string key::

    from turbopy import PhysicsModule

    class MyPusher(PhysicsModule):
        def update(self):
            ...

    PhysicsModule.register("MyPusher", MyPusher)

The :class:`~turbopy.core.Simulation` then finds and instantiates the
class whenever the input dict names ``"MyPusher"`` under
``"PhysicsModules"``.  See :doc:`dynamic_factory` for the full protocol.

The fundamental cycle
---------------------

The main time loop is
:meth:`turbopy.core.Simulation.fundamental_cycle`::

    def fundamental_cycle(self):
        for d in self.diagnostics:
            d.diagnose()
        for m in self.physics_modules:
            m.reset()
        for m in self.physics_modules:
            m.update()
        self.clock.advance()

Reading order for the rest of the guide
---------------------------------------

* :doc:`simulation_lifecycle` — how a run is set up and torn down.
* :doc:`clock` — configuring the time integration.
* :doc:`grids` — 1D and 2D grids, field placement, interpolation.
* :doc:`physics_modules` — writing your own physics.
* :doc:`compute_tools` — sharing numerics between modules.
* :doc:`diagnostics` — capturing and writing simulation output.
* :doc:`sharing_data` — the ``_resources_to_share`` /
  ``_needed_resources`` protocol.
* :doc:`dynamic_factory` — the registration protocol.
* :doc:`input_files` — TOML input file format.
* :doc:`api` — the exhaustive autodoc reference.
