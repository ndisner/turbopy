"""
Tests for the diagonstics.py file
"""
import pytest
import numpy as np
from turbopy.core import Simulation, PhysicsModule
from turbopy.diagnostics import PrintOutputUtility, utilities


class SharedField(PhysicsModule):
    """Example PhysicsModule subclass for tests"""
    def __init__(self, owner: Simulation, input_data: dict):
        super().__init__(owner, input_data)
        self.data = np.linspace(0, 1, 2)
        self._resources_to_share = {'Field': self.data}

    def update(self):
        pass


PhysicsModule.register("SharedField", SharedField)


@pytest.fixture(name='simple_field_csv')
def field_fixt_csv(tmp_path):
    """Pytest fixture for FieldDiagnostic class writing to csv file"""
    sim_dic = {"Grid": {"N": 2, "r_min": 0, "r_max": 1},
               "Clock": {"start_time": 0,
                         "end_time": 10,
                         "num_steps": 100},
               "PhysicsModules": {"SharedField": {}},
               "Diagnostics": {
                   "directory": f"{tmp_path}/default_output",
                   # "clock": {},
                   "field": [
                       {"component": "Component",
                        "field": "Field",
                        "output_type": "csv",
                        "filename": "output.csv",
                        "dump_interval": 1}
                       ]
               }
               }
    sim = Simulation(sim_dic)
    sim.read_diagnostics_from_input()
    sim.read_clock_from_input()
    sim.read_grid_from_input()
    field = sim.diagnostics[0]
    return field


@pytest.fixture(name='simple_field_npy')
def field_fixt_npy(tmp_path):
    """Pytest fixture for FieldDiagnostic class writing to npy file"""
    sim_dic = {"Grid": {"N": 2, "r_min": 0, "r_max": 1},
               "Clock": {"start_time": 0,
                         "end_time": 10,
                         "num_steps": 100},
               "PhysicsModules": {"SharedField": {}},
               "Diagnostics": {
                   "directory": f"{tmp_path}/default_output",
                   # "clock": {},
                   "field": [
                       {"component": "Component",
                        "field": "Field",
                        "output_type": "npy",
                        "filename": "output.npy",
                        "dump_interval": 1}
                       ]
               }
               }
    sim = Simulation(sim_dic)
    sim.read_diagnostics_from_input()
    sim.read_clock_from_input()
    sim.read_grid_from_input()
    field = sim.diagnostics[0]
    return field


# Test methods for FieldDiagnostic class with csv file
def test_init_should_create_class_instance_when_called(simple_field_csv):
    """Tests init method in FieldDiagnostic class"""
    assert simple_field_csv.component == "Component"
    assert simple_field_csv.field_name == "Field"
    assert simple_field_csv.output == "csv"
    assert simple_field_csv.field is None
    assert simple_field_csv.outputter is None


def test_check_step_should_update_last_dump_after_dump_interval_has_passed(simple_field_csv):
    """Tests check_step method in FieldDiagnostic class"""
    simple_field_csv._owner.prepare_simulation()
    simple_field_csv.initialize()
    simple_field_csv._owner.clock.time = 1
    simple_field_csv.dump_handler.perform_action(simple_field_csv._owner.clock.time)
    assert simple_field_csv.dump_handler._last_action == 1


def test_initialize_should_set_remaining_parameters_when_called(simple_field_csv):
    """Tests initialize method in FieldDiagnostic class for declared attributes"""
    simple_field_csv._owner.prepare_simulation()
    simple_field_csv.initialize()
    assert simple_field_csv.diagnostic_size == (11, 2)


def test_initialize_should_set_outputter_parameters_when_called(simple_field_csv, tmp_path):
    simple_field_csv._owner.prepare_simulation()
    simple_field_csv.initialize()
    assert simple_field_csv.outputter._filename == f"{tmp_path}/default_output/output.csv"
    assert np.allclose(simple_field_csv.outputter._buffer, np.zeros((11, 2)))
    assert simple_field_csv.outputter._buffer_index == 0


def test_csv_diagnose_should_append_data_to_csv_when_called(simple_field_csv):
    """Tests csv_diagnose method in FieldDiagnostic class"""
    simple_field_csv._owner.prepare_simulation()
    simple_field_csv.initialize()
    simple_field_csv.do_diagnostic()
    assert np.allclose(simple_field_csv.outputter._buffer[
                            simple_field_csv.outputter._buffer_index - 1, :],
                       simple_field_csv.field)
    assert simple_field_csv.outputter._buffer_index == 1


# Test methods for FieldDiagnostic class with npy files
def test_init_should_create_class_instance_when_called_npy(simple_field_npy):
    """Tests init method in FieldDiagnostic class"""
    assert simple_field_npy.component == "Component"
    assert simple_field_npy.field_name == "Field"
    assert simple_field_npy.output == "npy"
    assert simple_field_npy.field is None
    assert simple_field_npy.diagnostic_size is None


def test_check_step_should_update_last_dump_after_dump_interval_has_passed_npy(simple_field_npy):
    """Tests check_step method in FieldDiagnostic class"""
    simple_field_npy._owner.prepare_simulation()
    simple_field_npy.initialize()
    simple_field_npy._owner.clock.time = 1
    simple_field_npy.dump_handler.perform_action(simple_field_npy._owner.clock.time)
    assert simple_field_npy.dump_handler._last_action == 1


def test_initialize_should_set_remaining_parameters_when_called_npy(simple_field_npy):
    """Tests initialize method in FieldDiagnostic class for declared attributes"""
    simple_field_npy._owner.prepare_simulation()
    simple_field_npy.initialize()
    assert simple_field_npy.dump_interval == 1
    assert simple_field_npy.diagnostic_size == (11, 2)


def test_initialize_should_set_outputter_parameters_when_called_npy(simple_field_npy, tmp_path):
    simple_field_npy._owner.prepare_simulation()
    simple_field_npy.initialize()
    assert simple_field_npy.outputter._filename == f"{tmp_path}/default_output/output.npy"
    assert np.allclose(simple_field_npy.outputter._buffer, np.zeros((11, 2)))
    assert simple_field_npy.outputter._buffer_index == 0


def test_csv_diagnose_should_append_data_to_csv_when_called_npy(simple_field_npy):
    """Tests npy_diagnose method in FieldDiagnostic class"""
    simple_field_npy._owner.prepare_simulation()
    simple_field_npy.initialize()
    simple_field_npy.do_diagnostic()
    assert np.allclose(simple_field_npy.outputter._buffer[
                       simple_field_npy.outputter._buffer_index - 1, :],
                       simple_field_npy.field)
    assert simple_field_npy.outputter._buffer_index == 1


# Regression tests for PrintOutputUtility.
# Before the fix, PrintOutputUtility left OutputUtility.finalize and
# .write_data abstract, so instantiating it (including via the "stdout"
# entry in the utilities registry) raised TypeError. These tests lock in
# that the class is instantiable and that finalize/write_data are safe
# no-ops, keeping the "stdout" output_type usable end-to-end.
def test_print_output_utility_can_be_instantiated():
    utility = PrintOutputUtility()
    assert isinstance(utility, PrintOutputUtility)


def test_print_output_utility_diagnose_prints_to_stdout(capsys):
    utility = PrintOutputUtility()
    utility.diagnose(np.array([1.0, 2.0, 3.0]))
    captured = capsys.readouterr()
    assert "1." in captured.out and "3." in captured.out


def test_print_output_utility_finalize_and_write_data_are_noops():
    utility = PrintOutputUtility()
    assert utility.finalize() is None
    assert utility.write_data() is None


def test_utilities_stdout_entry_matches_diagnostic_call_pattern():
    """The ``"stdout"`` entry must accept the same kwargs a diagnostic splats.

    Real diagnostics do ``utilities[output_type](**self._input_data)`` (see
    :meth:`turbopy.diagnostics.PointDiagnostic.initialize` /
    :meth:`turbopy.diagnostics.FieldDiagnostic.initialize`), so the stdout
    utility must tolerate keys like ``filename`` and ``diagnostic_size``.
    """
    diagnostic_input_data = {
        "output_type": "stdout",
        "filename": None,
        "diagnostic_size": (1, 1),
        "component": "Component",
        "field": "Field",
    }
    utility = utilities["stdout"](**diagnostic_input_data)
    assert isinstance(utility, PrintOutputUtility)
