import os
from pathlib import Path

import pytest

from neuromation.api import NoProjectRoot, find_project_root


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    project_root = tmp_path / "neuro-project"
    os.mkdir(project_root)
    with open(project_root / ".neuro.toml", "w"):
        pass
    return project_root


def test_find_root_in_root_dir(project_root: Path) -> None:
    old_workdir = os.getcwd()
    try:
        os.chdir(project_root)
        assert find_project_root() == project_root
    finally:
        os.chdir(old_workdir)


def test_find_root_in_subdir(project_root: Path) -> None:
    old_workdir = os.getcwd()
    try:
        os.mkdir(project_root / "foo")
        os.chdir(project_root / "foo")
        assert find_project_root() == project_root
    finally:
        os.chdir(old_workdir)


def test_find_root_not_in_project(tmp_path: Path) -> None:
    old_workdir = os.getcwd()
    try:
        os.chdir(tmp_path)
        with pytest.raises(NoProjectRoot):
            find_project_root()
    finally:
        os.chdir(old_workdir)
