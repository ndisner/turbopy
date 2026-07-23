Physics Modules
===============

A :class:`turbopy.core.PhysicsModule` is the unit of user-supplied
physical dynamics.  Every module is called once per time step from the
main loop via :meth:`~turbopy.core.PhysicsModule.update`.

Anatomy of a module
-------------------

A minimal module::

    import numpy as np
    from turbopy import PhysicsModule

    class HarmonicOscillator(PhysicsModule):
        def __init__(self, owner, input_data):
            super().__init__(owner, input_data)
            self.k = input_data["k"]
            self.mass = input_data["mass"]
            self.position = np.zeros(3)
            self.momentum = np.zeros(3)
            # published automatically as HarmonicOscillator_position, etc.
            self._resources_to_share = {
                "position": self.position,
                "momentum": self.momentum,
            }

        def update(self):
            dt = self._owner.clock.dt
            self.momentum -= self.k * self.position * dt
            self.position += self.momentum * dt / self.mass

    PhysicsModule.register("HarmonicOscillator", HarmonicOscillator)

Lifecycle hooks
---------------

The following methods are called by the simulation, in this order:

1. ``__init__(owner, input_data)`` — during
   :meth:`~turbopy.core.Simulation.read_modules_from_input`.  Set up
   attributes and populate :attr:`_resources_to_share` and
   :attr:`_needed_resources`.
2. :meth:`~turbopy.core.PhysicsModule.exchange_resources` — called on
   every module before any module's
   :meth:`~turbopy.core.PhysicsModule.inspect_resources` runs.  The
   default implementation publishes
   :attr:`_resources_to_share` to
   :attr:`~turbopy.core.Simulation.all_shared_resources`.
3. :meth:`~turbopy.core.PhysicsModule.inspect_resources` — the default
   implementation binds every entry in
   :attr:`_needed_resources` to an attribute of the module.
4. :meth:`~turbopy.core.PhysicsModule.initialize` — one-time per-module
   setup that requires shared resources to be bound.

Then, per time step:

5. :meth:`~turbopy.core.PhysicsModule.reset` — optional; called on every
   module before *any* :meth:`~turbopy.core.PhysicsModule.update`.
6. :meth:`~turbopy.core.PhysicsModule.update` — **required**; subclasses
   that do not override it will raise :class:`NotImplementedError`.

Sharing data between modules
----------------------------

By default a subclass shares any public attribute (any name that does
not start with ``_``) under the key
``<ClassName>_<attribute_name>``.  To publish custom keys, or to
consume data from another module, use the dictionaries
:attr:`_resources_to_share` and :attr:`_needed_resources`.  See
:doc:`sharing_data` for the full protocol and gotchas around
mutable versus immutable variables.

Registration
------------

For a class to be reachable from the input dict, register it once at
module import::

    PhysicsModule.register("HarmonicOscillator", HarmonicOscillator)

Registration is described in detail in :doc:`dynamic_factory`.
