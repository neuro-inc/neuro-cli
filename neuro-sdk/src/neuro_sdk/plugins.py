import numbers
from typing import Any, Dict, List, Mapping, Tuple, Type, Union

from .errors import ConfigError


class ConfigBuilder:
    _config_spec: Dict[str, Any]

    def __init__(self) -> None:
        self._config_spec = dict()

    def _define_param(
        self,
        section: str,
        name: str,
        type: Union[
            Type[bool],
            Type[numbers.Real],
            Type[numbers.Integral],
            Type[str],
            Tuple[Type[List[Any]], Type[bool]],
            Tuple[Type[List[Any]], Type[str]],
            Tuple[Type[List[Any]], Type[numbers.Real]],
            Tuple[Type[List[Any]], Type[numbers.Integral]],
        ],
    ) -> None:
        if section == "alias":
            raise ConfigError("Registering aliases is not supported yet.")
        if section in self._config_spec and name in self._config_spec[section]:
            raise ConfigError(f"Config parameter {section}.{name} already registered")
        self._config_spec.setdefault(section, dict())
        self._config_spec[section][name] = type

    def _get_spec(self) -> Mapping[str, Any]:
        return self._config_spec

    def define_int(self, section: str, name: str) -> None:
        self._define_param(section, name, numbers.Integral)

    def define_bool(self, section: str, name: str) -> None:
        self._define_param(section, name, bool)

    def define_str(self, section: str, name: str) -> None:
        self._define_param(section, name, str)

    def define_float(self, section: str, name: str) -> None:
        self._define_param(section, name, numbers.Real)

    def define_int_list(self, section: str, name: str) -> None:
        self._define_param(section, name, (list, numbers.Integral))

    def define_bool_list(self, section: str, name: str) -> None:
        self._define_param(section, name, (list, bool))

    def define_str_list(self, section: str, name: str) -> None:
        self._define_param(section, name, (list, str))

    def define_float_list(self, section: str, name: str) -> None:
        self._define_param(section, name, (list, numbers.Real))


class PluginManager:

    _config: ConfigBuilder

    def __init__(self) -> None:
        self._config = ConfigBuilder()

    @property
    def config(self) -> ConfigBuilder:
        return self._config
