import pytest

from tests.e2e import Helper


@pytest.mark.e2e
def test_project_init(helper: Helper) -> None:
    captured = helper.run_cli(["project", "init"])
    assert captured.out is None
