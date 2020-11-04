import asyncio
import logging
from collections import namedtuple
from pathlib import Path
from typing import Any, AsyncIterator, Callable, List, Optional

import pytest
from rich.console import Console, RenderableType
from yarl import URL

import neuromation
from neuromation.api import Cluster, Factory, Preset
from neuromation.api.config import _AuthConfig, _AuthToken, _ConfigData
from neuromation.cli import main
from neuromation.cli.const import EX_OK
from neuromation.cli.root import Root


SysCapWithCode = namedtuple("SysCapWithCode", ["out", "err", "code"])
log = logging.getLogger(__name__)


@pytest.fixture()
def nmrc_path(tmp_path: Path, token: str, auth_config: _AuthConfig) -> Path:
    nmrc_path = tmp_path / "conftest.nmrc"
    cluster_config = Cluster(
        registry_url=URL("https://registry-dev.neu.ro"),
        storage_url=URL("https://storage-dev.neu.ro"),
        users_url=URL("https://users-dev.neu.ro"),
        monitoring_url=URL("https://monitoring-dev.neu.ro"),
        secrets_url=URL("https://secrets-dev.neu.ro"),
        presets={
            "gpu-small": Preset(
                cpu=7, memory_mb=30 * 1024, gpu=1, gpu_model="nvidia-tesla-k80"
            ),
            "gpu-large": Preset(
                cpu=7, memory_mb=60 * 1024, gpu=1, gpu_model="nvidia-tesla-v100"
            ),
            "cpu-small": Preset(cpu=7, memory_mb=2 * 1024),
            "cpu-large": Preset(cpu=7, memory_mb=14 * 1024),
        },
        name="default",
    )
    config = _ConfigData(
        auth_config=auth_config,
        auth_token=_AuthToken.create_non_expiring(token),
        url=URL("https://dev.neu.ro/api/v1"),
        version=neuromation.__version__,
        cluster_name="default",
        clusters={cluster_config.name: cluster_config},
    )
    Factory(nmrc_path)._save(config)
    return nmrc_path


def create_root(config_path: Path) -> Root:
    return Root(
        color=False,
        tty=False,
        disable_pypi_version_check=True,
        network_timeout=60,
        config_path=config_path,
        verbosity=0,
        trace=False,
        trace_hide_token=True,
        command_path="",
        command_params=[],
        skip_gmp_stats=True,
        show_traceback=False,
    )


@pytest.fixture()
async def root(nmrc_path: Path, loop: asyncio.AbstractEventLoop) -> AsyncIterator[Root]:
    root = create_root(config_path=nmrc_path)
    await root.init_client()
    yield root
    await root.client.close()


@pytest.fixture()
async def root_no_logged_in(
    tmp_path: Path, loop: asyncio.AbstractEventLoop
) -> AsyncIterator[Root]:
    root = create_root(config_path=tmp_path)
    assert root._client is None
    yield root
    assert root._client is None


@pytest.fixture()
def run_cli(
    nmrc_path: Path, capfd: Any, tmp_path: Path
) -> Callable[[List[str]], SysCapWithCode]:
    def _run_cli(arguments: List[str]) -> SysCapWithCode:
        log.info("Run 'neuro %s'", " ".join(arguments))
        capfd.readouterr()

        code = EX_OK
        try:
            default_args = [
                "--show-traceback",
                "--disable-pypi-version-check",
                "--color=no",
            ]
            if "--neuromation-config" not in arguments:
                for arg in arguments:
                    if arg.startswith("--neuromation-config="):
                        break
                else:
                    default_args.append(f"--neuromation-config={nmrc_path}")

            main(default_args + arguments)
        except SystemExit as e:
            code = e.code
            pass
        out, err = capfd.readouterr()
        return SysCapWithCode(out.strip(), err.strip(), code)

    return _run_cli


@pytest.fixture()
def click_tty_emulation(monkeypatch: Any) -> None:
    monkeypatch.setattr("click._compat.isatty", lambda stream: True)


def pytest_addoption(parser: Any, pluginmanager: Any) -> None:
    parser.addoption(
        "--rich-gen",
        default=False,
        action="store_true",
        help="Regenerate rich_cmp references from captured texts",
    )


class RichComparator:
    def __init__(self, config: Any) -> None:
        self._regen = config.getoption("--rich-gen")
        self._config = config
        self._reporter = config.pluginmanager.getplugin("terminalreporter")
        assert self._reporter is not None
        self._cwd = Path.cwd()
        self._missing_refs: List[Path] = []
        self._written_refs: List[Path] = []

    def mkref(self, request: Any) -> Path:
        folder = Path(request.fspath).parent
        basename = request.function.__qualname__ + ".ascii"
        return folder / "ascii" / basename

    def check(self, ref: Path, buf: str) -> None:
        __tracebackhide__ = True

        if self._regen:
            rel_ref = self.write_ref(ref, buf)
            if rel_ref is not None:
                pytest.fail(
                    f"Regenerate '{rel_ref}', "
                    "please restart tests without --rich-gen option."
                )
        orig = self.read_ref(ref)
        assert buf == orig

    def read_ref(self, ref: Path) -> str:
        __tracebackhide__ = True
        if not ref.exists():
            if not self._regen:
                rel_ref = ref.relative_to(Path.cwd())
                pytest.fail(
                    f"Original reference {rel_ref} doesn't exist.\n"
                    "Create it yourself or run pytest with '--rich-generate' option."
                )
        else:
            return ref.read_text()

    def write_ref(self, ref: Path, buf: str) -> Optional[Path]:
        if ref.exists():
            orig = ref.read_text()
            if orig == buf:
                return None
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(buf)
        rel_ref = ref.relative_to(self._cwd)
        if self._reporter.verbosity > 0:
            self._reporter.write_line(f"Regenerate {rel_ref}", yellow=True)
        self._written_refs.append(rel_ref)
        return rel_ref

    def summary(self) -> None:
        if self._reporter.verbosity == 0:
            if self._written_refs:
                self._reporter.write_line("Regenerated files:", yellow=True)
                for fname in self._written_refs:
                    self._reporter.write_line(f"  {fname}", yellow=True)


# run after terminalreporter/capturemanager are configured
@pytest.hookimpl(trylast=True)
def pytest_configure(config: Any) -> None:
    comparator = RichComparator(config)
    config.pluginmanager.register(comparator, "rich-comparator")


def pytest_terminal_summary(terminalreporter: Any) -> None:
    config = terminalreporter.config
    comparator = config.pluginmanager.getplugin("rich-comparator")
    comparator.summary()


@pytest.fixture
def rich_cmp(request: Any) -> Callable[..., None]:
    def comparator(
        src: RenderableType,
        ref: Optional[Path] = None,
        *,
        color: bool = True,
        tty: bool = True,
    ) -> None:
        __tracebackhide__ = True
        plugin = request.config.pluginmanager.getplugin("rich-comparator")
        console = Console(
            width=80,
            height=24,
            force_terminal=tty,
            color_system="auto" if color else None,
            record=True,
            highlighter=None,
        )
        with console.capture() as capture:
            console.print(src)
        buf = capture.get()

        if ref is None:
            ref = plugin.mkref(request)

        plugin.check(ref, buf)

    return comparator
