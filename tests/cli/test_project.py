import os
from pathlib import Path
from typing import Optional

import pytest

from neuromation.cli.project import _project_init


@pytest.mark.parametrize("slug", [None, "my-custom-slug"])
def test_project_init(tmp_path: Path, slug: Optional[str]) -> None:
    old_workdir = os.getcwd()
    path = tmp_path / (slug or "neuro-project")
    assert not path.is_dir()
    try:
        os.chdir(str(tmp_path))

        _project_init(slug, no_input=True)
        assert path.is_dir()
        assert "Makefile" in {p.name for p in path.iterdir()}
    finally:
        os.chdir(old_workdir)
