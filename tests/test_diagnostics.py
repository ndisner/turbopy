"""
Tests for the diagonstics.py file
"""
import pytest
import numpy as np
import xarray as xr
from turbopy.core import Simulation, PhysicsModule


class SharedField(PhysicsModule):
    """Example PhysicsModule subclass for tests"""
    def __init__(self, owner: Simulation, input_data: dict):
        super().__init__(owner, input_data)
        self.data = np.linspace(0, 1, 2)
        self._resources_to_share = {'Field': self.data}

    def update(self):
        pass


PhysicsModule.register("SharedField", SharedField)


class SharedField2D(PhysicsModule):
    """PhysicsModule that publishes a 2D field for HistoryDiagnostic tests."""
    def __init__(self, owner: Simulation, input_data: dict):
        super().__init__(owner, input_data)
        self.data = np.zeros(owner.grid.shape)
        self._resources_to_share = {'Field2D': self.data}

    def update(self):
        self.data[...] = self._owner.clock.time


PhysicsModule.register("SharedField2D", SharedField2D)


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


# ---------------------------------------------------------------------------
# HistoryDiagnostic 2D support
# ---------------------------------------------------------------------------

def _history_sim_2d(coord_sys, tmp_path):
    if coord_sys == "cartesian2d":
        grid_input = {"coordinate_system": "cartesian2d",
                      "Nx": 4, "Ny": 3,
                      "x_min": 0.0, "x_max": 3.0,
                      "y_min": 0.0, "y_max": 2.0}
        trace_dims = ["x", "y"]
    else:
        grid_input = {"coordinate_system": "cylindrical2d",
                      "Nr": 4, "Nz": 3,
                      "r_min": 1.0, "r_max": 2.0,
                      "z_min": 0.0, "z_max": 1.0}
        trace_dims = ["r", "z"]
    dic = {
        "Grid": grid_input,
        "Clock": {"start_time": 0.0, "end_time": 1.0, "num_steps": 2},
        "Tools": {},
        "PhysicsModules": {"SharedField2D": {}},
        "Diagnostics": {
            "directory": str(tmp_path),
            "histories": {
                "filename": str(tmp_path / "history.nc"),
                "traces": [
                    {"name": "Field2D",
                     "coords": trace_dims,
                     "units": "T",
                     "long_name": "Test 2D field"},
                ],
            },
        },
    }
    return Simulation(dic), trace_dims


def test_history_diagnostic_cartesian2d_writes_netcdf(tmp_path):
    sim, dims = _history_sim_2d("cartesian2d", tmp_path)
    sim.run()  # must not raise NotImplementedError
    ds = xr.open_dataset(tmp_path / "history.nc")
    for d in dims:
        assert d in ds.coords, f"expected coord {d!r} on saved dataset"
    field = ds["Field2D"]
    assert field.sizes["x"] == 4
    assert field.sizes["y"] == 3
    # SharedField2D.update() sets data = clock.time at each step
    assert "timestep" in field.dims
    ds.close()


def test_history_diagnostic_cylindrical2d_writes_netcdf(tmp_path):
    sim, dims = _history_sim_2d("cylindrical2d", tmp_path)
    sim.run()
    ds = xr.open_dataset(tmp_path / "history.nc")
    for d in dims:
        assert d in ds.coords
    field = ds["Field2D"]
    assert field.sizes["r"] == 4
    assert field.sizes["z"] == 3
    # coord values should match grid.r and grid.z
    np.testing.assert_allclose(ds["r"].values, np.linspace(1.0, 2.0, 4))
    np.testing.assert_allclose(ds["z"].values, np.linspace(0.0, 1.0, 3))
    ds.close()
