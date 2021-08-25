import os
from pathlib import Path
from typing import Optional

import pytest

from neuro_cli.project import _project_init


@pytest.mark.parametrize("dir_name", [None, "my-custom-slug"])
def test_project_init(tmp_path: Path, dir_name: Optional[str]) -> None:
    old_workdir = os.getcwd()
    path = tmp_path / (dir_name or "neuro project")
    assert not path.is_dir()
    try:
        os.chdir(str(tmp_path))

        _project_init(dir_name, no_input=True)
        assert path.is_dir()
        assert "Dockerfile" in {p.name for p in path.iterdir()}
    finally:
        os.chdir(old_workdir)
