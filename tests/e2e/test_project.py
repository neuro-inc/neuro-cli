import pathlib
import shutil

import pytest

from tests.e2e import Helper


@pytest.mark.e2e
def test_project_init(helper: Helper) -> None:
    path = pathlib.Path(f"./name-of-the-project")
    assert not path.exists()
    try:
        helper.run_cli(["project", "init", "-q"])
        assert path.exists()
        assert path.is_dir()
    finally:
        shutil.rmtree(path)


@pytest.mark.e2e
def test_project_init_custom_slug(helper: Helper) -> None:
    path = pathlib.Path("./my-custom-slug")
    assert not path.exists()
    try:
        helper.run_cli(["project", "init", "-q", "my-custom-slug"])
        assert path.exists()
        assert path.is_dir()
    finally:
        shutil.rmtree(path)
