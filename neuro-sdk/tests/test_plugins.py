import numbers
from typing import Any

import pytest

from neuro_sdk import ConfigError
from neuro_sdk.plugins import ConfigBuilder


@pytest.mark.parametrize(
    "define_method_name,expected_type",
    [
        ("define_int", numbers.Integral),
        ("define_float", numbers.Real),
        ("define_str", str),
        ("define_bool", bool),
        ("define_int_list", (list, numbers.Integral)),
        ("define_float_list", (list, numbers.Real)),
        ("define_str_list", (list, str)),
        ("define_bool_list", (list, bool)),
    ],
)
def test_config_builder(define_method_name: str, expected_type: Any) -> None:
    config = ConfigBuilder()
    getattr(config, define_method_name)("foo", "bar")
    assert config._get_spec()["foo"]["bar"], bool


def test_cannot_config_parameter_under_alias_section() -> None:
    config = ConfigBuilder()
    with pytest.raises(ConfigError):
        config.define_str("alias", "foo")


def test_cannot_add_parameter_twice() -> None:
    config = ConfigBuilder()
    config.define_str("foo", "bar")
    with pytest.raises(ConfigError):
        config.define_str("foo", "bar")
