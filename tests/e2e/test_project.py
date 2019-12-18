import pathlib
import shutil

import pytest

from tests.e2e import Helper


@pytest.mark.e2e
def test_project_init(helper: Helper) -> None:
    path = pathlib.Path(f"./name-of-the-project")
    assert not path.exists()
    helper.run_cli(["project", "init", "--no-input"])
    assert path.exists()
    assert path.is_dir()
    try:
        shutil.rmtree(path)
    except Exception:
        # ignore errors, the directory may not exist legitimately
        pass


@pytest.mark.e2e
def test_project_init_custom_slug(helper: Helper) -> None:
    path = pathlib.Path("./my-custom-slug")
    assert not path.exists()
    helper.run_cli(["project", "init", "--no-input", "my-custom-slug"])
    assert path.exists()
    assert path.is_dir()
    try:
        shutil.rmtree(path)
    except Exception:
        # ignore errors, the directory may not exist legitimately
        pass
