"""Shared pytest fixtures for all test levels."""
import pytest
from pathlib import Path
from typer.testing import CliRunner

from facade_planner.domain.entities.panel_format import PanelFormat
from facade_planner.domain.entities.supplier_catalog import SupplierCatalog
from facade_planner.domain.entities.facade_surface import FacadeSurface
from facade_planner.domain.value_objects.joint_config import JointConfig
from facade_planner.cli.main import app


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Isolated project directory in a temp folder."""
    return tmp_path


@pytest.fixture
def sample_panel_format() -> PanelFormat:
    return PanelFormat(
        format_code="SW-1250x3050",
        width_mm=1250.0,
        height_mm=3050.0,
        thickness_mm=8.0,
        weight_kg_m2=4.2,
        description="Swisspearl standard panel",
    )


@pytest.fixture
def sample_supplier_catalog(sample_panel_format: PanelFormat) -> SupplierCatalog:
    import uuid
    return SupplierCatalog(
        id=str(uuid.uuid4()),
        supplier_name="Swisspearl",
        formats=[sample_panel_format],
    )


@pytest.fixture
def sample_surface() -> FacadeSurface:
    """Simple 5000x3000mm rectangular surface."""
    import uuid
    return FacadeSurface(
        id=str(uuid.uuid4()),
        plan_id="plan-001",
        page_number=1,
        boundary=[(0.0, 0.0), (5000.0, 0.0), (5000.0, 3000.0), (0.0, 3000.0)],
    )


@pytest.fixture
def default_joint_config() -> JointConfig:
    return JointConfig(
        horizontal_joint_mm=10.0,
        vertical_joint_mm=10.0,
        expansion_joint_interval_mm=6000.0,
        expansion_joint_width_mm=20.0,
    )
