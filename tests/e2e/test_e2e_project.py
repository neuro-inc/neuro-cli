import subprocess
from pathlib import Path

from .conftest import Helper
from .utils import working_directory


def test_project_init(helper: Helper, tmp_path: Path) -> None:
    # depend on `helper` fixture so that `neuro` is already logged-in
    with working_directory(tmp_path):
        project_path = tmp_path / "yes"
        # answer "yes" to all annoying questions and thus set project_name = "yes"
        cmd = "yes yes | neuro project init"
        proc = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        out, err = proc.communicate()
        assert b"project_slug [yes]:" in out
        assert not err
        actual_ls = set(path.name for path in project_path.iterdir())
        assert actual_ls >= {
            "yes",
            "data",
            "notebooks",
            "Makefile",
            "apt.txt",
            "requirements.txt",
            "setup.py",
            "setup.cfg",
        }
