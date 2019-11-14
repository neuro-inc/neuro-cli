import pytest

import neuromation
from tests.e2e import Helper


@pytest.mark.e2e
def test_print_version(helper: Helper) -> None:
    expected_out = f"Neuromation Platform Client {neuromation.__version__}"

    captured = helper.run_cli(["--version"])
    assert not captured.err
    assert captured.out == expected_out


@pytest.mark.e2e
def test_print_options(helper: Helper) -> None:
    captured = helper.run_cli(["--options"])
    assert not captured.err
    assert "Options" in captured.out


@pytest.mark.e2e
def test_print_config(helper: Helper) -> None:
    captured = helper.run_cli(["config", "show"])
    assert not captured.err
    assert "API URL: https://dev.neu.ro/api/v1" in captured.out


@pytest.mark.e2e
def test_print_config_token(helper: Helper) -> None:
    captured = helper.run_cli(["config", "show-token"])
    assert not captured.err
    assert captured.out  # some secure information was printed


@pytest.mark.e2e
def test_root_trace_hide_token_default_true(helper: Helper) -> None:
    captured = helper.run_cli(["--trace", "ls"])
    assert "Authorization: Bearer " in captured.err
    assert "<hidden " in captured.err
    assert " chars>" in captured.err


@pytest.mark.e2e
def test_root_trace_hide_token_explicit_true(helper: Helper) -> None:
    captured = helper.run_cli(["--trace", "--hide-token", "ls"])
    assert "Authorization: Bearer " in captured.err
    assert "<hidden " in captured.err
    assert " chars>" in captured.err


@pytest.mark.e2e
def test_root_trace_hide_token_explicit_false(helper: Helper) -> None:
    captured = helper.run_cli(["--trace", "--no-hide-token", "ls"])
    assert "Authorization: Bearer " in captured.err
    assert "<hidden " not in captured.err
    assert " chars>" not in captured.err


@pytest.mark.e2e
def test_root_hide_token_true_without_trace_not_allowed(helper: Helper) -> None:
    captured = helper.run_cli(["--hide-token", "ls"], raise_for_returncode=False)
    assert captured.code == 2
    assert "--hide-token requires --trace" in captured.err


@pytest.mark.e2e
def test_root_hide_token_false_without_trace_not_allowed(helper: Helper) -> None:
    captured = helper.run_cli(["--no-hide-token", "ls"], raise_for_returncode=False)
    assert captured.code == 2
    assert "--no-hide-token requires --trace" in captured.err
