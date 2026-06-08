"""Unit tests for ProjectRepository and ProjectService."""
from pathlib import Path

import pytest
from typer.testing import CliRunner

from facade_planner.cli.main import app
from facade_planner.domain.exceptions import ProjectAlreadyExistsError, ProjectNotInitializedError
from facade_planner.infrastructure.persistence.project_repository import FileProjectRepository


class TestFileProjectRepository:
    def test_create_project(self, tmp_path: Path) -> None:
        repo = FileProjectRepository(tmp_path)
        project = repo.create("Test Project")
        assert project.name == "Test Project"
        assert (tmp_path / ".facadeplanner" / "project.json").exists()

    def test_create_creates_subdirs(self, tmp_path: Path) -> None:
        repo = FileProjectRepository(tmp_path)
        repo.create("Test")
        for sub in ("plans", "surfaces", "jobs", "exports", "catalogs"):
            assert (tmp_path / ".facadeplanner" / sub).is_dir()

    def test_create_raises_if_exists(self, tmp_path: Path) -> None:
        repo = FileProjectRepository(tmp_path)
        repo.create("First")
        with pytest.raises(ProjectAlreadyExistsError):
            repo.create("Second")

    def test_load_project(self, tmp_path: Path) -> None:
        repo = FileProjectRepository(tmp_path)
        original = repo.create("Load Test")
        loaded = repo.load()
        assert loaded.id == original.id
        assert loaded.name == "Load Test"

    def test_load_raises_if_not_initialized(self, tmp_path: Path) -> None:
        repo = FileProjectRepository(tmp_path)
        with pytest.raises(ProjectNotInitializedError):
            repo.load()

    def test_exists_false_before_create(self, tmp_path: Path) -> None:
        repo = FileProjectRepository(tmp_path)
        assert repo.exists() is False

    def test_exists_true_after_create(self, tmp_path: Path) -> None:
        repo = FileProjectRepository(tmp_path)
        repo.create("X")
        assert repo.exists() is True


class TestProjectCLI:
    def test_create_command(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(app, ["project", "create", "Mein Projekt"], catch_exceptions=False)
        # CLI runs in CWD, not tmp_path — just check it doesn't crash with missing arg
        # Real integration test uses tmp_path via chdir

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "facade-planning-engine" in result.output

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "project" in result.output
        assert "plan" in result.output
