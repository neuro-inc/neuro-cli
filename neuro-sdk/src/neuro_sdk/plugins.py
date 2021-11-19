import enum
import numbers
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Tuple, Type, Union

from .errors import ConfigError


class ConfigScope(enum.Flag):
    GLOBAL = enum.auto()
    LOCAL = enum.auto()
    ALL = GLOBAL | LOCAL


_ParamType = Union[
    Type[bool],
    Type[numbers.Real],
    Type[numbers.Integral],
    Type[str],
    Tuple[Type[List[Any]], Type[bool]],
    Tuple[Type[List[Any]], Type[str]],
    Tuple[Type[List[Any]], Type[numbers.Real]],
    Tuple[Type[List[Any]], Type[numbers.Integral]],
]


class ConfigBuilder:
    _config_spec: Dict[str, Dict[str, Tuple[_ParamType, ConfigScope]]]

    def __init__(self) -> None:
        self._config_spec = dict()

    def _define_param(
        self,
        section: str,
        name: str,
        type: _ParamType,
        scope: ConfigScope,
    ) -> None:
        if section == "alias":
            raise ConfigError("Registering aliases is not supported yet.")
        if section in self._config_spec and name in self._config_spec[section]:
            raise ConfigError(f"Config parameter {section}.{name} already registered")
        self._config_spec.setdefault(section, dict())
        self._config_spec[section][name] = (type, scope)

    def _get_spec(self) -> Mapping[str, Mapping[str, Tuple[_ParamType, ConfigScope]]]:
        return self._config_spec

    def define_int(
        self, section: str, name: str, *, scope: ConfigScope = ConfigScope.ALL
    ) -> None:
        self._define_param(section, name, numbers.Integral, scope)

    def define_bool(
        self, section: str, name: str, *, scope: ConfigScope = ConfigScope.ALL
    ) -> None:
        self._define_param(section, name, bool, scope)

    def define_str(
        self, section: str, name: str, *, scope: ConfigScope = ConfigScope.ALL
    ) -> None:
        self._define_param(section, name, str, scope)

    def define_float(
        self, section: str, name: str, *, scope: ConfigScope = ConfigScope.ALL
    ) -> None:
        self._define_param(section, name, numbers.Real, scope)

    def define_int_list(
        self, section: str, name: str, *, scope: ConfigScope = ConfigScope.ALL
    ) -> None:
        self._define_param(section, name, (list, numbers.Integral), scope)

    def define_bool_list(
        self, section: str, name: str, *, scope: ConfigScope = ConfigScope.ALL
    ) -> None:
        self._define_param(section, name, (list, bool), scope)

    def define_str_list(
        self, section: str, name: str, *, scope: ConfigScope = ConfigScope.ALL
    ) -> None:
        self._define_param(section, name, (list, str), scope)

    def define_float_list(
        self, section: str, name: str, *, scope: ConfigScope = ConfigScope.ALL
    ) -> None:
        self._define_param(section, name, (list, numbers.Real), scope)


@dataclass(frozen=True)
class _VersionRecord:
    package: str
    update_text: Callable[[str, str], str]
    exclusive: bool
    delay: float


class VersionChecker:
    def __init__(self) -> None:
        self._records: Dict[str, _VersionRecord] = {}

    def register(
        self,
        package: str,
        update_text: Callable[[str, str], str],
        *,
        exclusive: bool = False,
        delay: float = 0,
    ) -> None:
        record = _VersionRecord(package, update_text, exclusive, delay)
        if exclusive and any(rec.exclusive for rec in self._records.values()):
            pkgs = [rec.package for rec in self._records.values() if rec.exclusive]
            raise ConfigError(f"Exclusive record for package {pkgs[0]} already exists")
        self._records[package] = record


class PluginManager:

    _config: ConfigBuilder
    _version_checker: VersionChecker

    def __init__(self) -> None:
        self._config = ConfigBuilder()
        self._version_checker = VersionChecker()

    @property
    def config(self) -> ConfigBuilder:
        return self._config

    @property
    def version_checker(self) -> VersionChecker:
        return self._version_checker
