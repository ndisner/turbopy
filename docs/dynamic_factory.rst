The DynamicFactory Registry
===========================

turboPy makes user-supplied classes reachable from configuration data
via the :class:`turbopy.core.DynamicFactory` registry pattern.  Every
subclass of :class:`~turbopy.core.PhysicsModule`,
:class:`~turbopy.core.ComputeTool`, and
:class:`~turbopy.core.Diagnostic` registers itself under a string key;
:class:`~turbopy.core.Simulation` then instantiates classes by name
from the input dict.

Registering a class
-------------------

Use the classmethod :meth:`~turbopy.core.DynamicFactory.register`::

    from turbopy import PhysicsModule

    class MyModule(PhysicsModule):
        def update(self):
            ...

    PhysicsModule.register("MyModule", MyModule)

:meth:`~turbopy.core.DynamicFactory.register` raises
:class:`ValueError` if the name is already in the registry (unless
``override=True`` is passed), and :class:`TypeError` if the class
being registered is not a subclass of the factory it is being
registered with.

The same pattern applies for :class:`~turbopy.core.ComputeTool` and
:class:`~turbopy.core.Diagnostic`::

    ComputeTool.register("MyTool", MyTool)
    Diagnostic.register("MyDiag", MyDiag)

Looking up a class
------------------

:meth:`~turbopy.core.DynamicFactory.lookup` returns the class
associated with a name, or raises :class:`KeyError` if not found::

    cls = PhysicsModule.lookup("MyModule")

:meth:`~turbopy.core.DynamicFactory.is_valid_name` returns ``True`` if
the name is in the registry — used, for example, by
:meth:`turbopy.core.Simulation.parse_diagnostic_input_dictionary` to
split the ``"Diagnostics"`` dict into diagnostics-by-name and
default-parameters.

Where registration must happen
------------------------------

Registration is a side effect of importing the module that defines
the class.  Import your module at least once before constructing the
:class:`~turbopy.core.Simulation`, e.g., at the top of your entry
script::

    import my_project.modules   # triggers PhysicsModule.register(...)
    from turbopy import Simulation

    sim = Simulation(input_data)

Implementing a new factory
--------------------------

Subclasses of :class:`~turbopy.core.DynamicFactory` provide two class
attributes:

* :attr:`_factory_type_name` — a human-readable string used in error
  messages.
* :attr:`_registry` — a class-level dictionary that holds the
  registered classes.

The built-in factories set these as::

    class PhysicsModule(DynamicFactory):
        _factory_type_name = "Physics Module"
        _registry = {}

Custom factories are rarely needed; users typically extend the three
provided ones.
