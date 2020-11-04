import asyncio
import dataclasses
import logging
from collections import namedtuple
from difflib import ndiff
from pathlib import Path
from typing import Any, AsyncIterator, Callable, List, Optional

import click
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


@dataclasses.dataclass(eq=False)
class Guard:
    arg: str
    path: Path

    def __eq__(self, other: "Guard") -> bool:
        return self.arg == other.arg


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
        basename = request.function.__qualname__ + ".ref"
        return folder / "ascii" / basename

    def rel(self, ref: Path) -> Path:
        return ref.relative_to(self._cwd)

    def check(self, ref: Path, buf: str) -> None:
        __tracebackhide__ = True

        if self._regen:
            regen = self.write_ref(ref, buf)
            if regen:
                rel_ref = self.rel(ref)
                pytest.fail(
                    f"Regenerated {rel_ref}, "
                    "please restart tests without --rich-gen option.",
                    pytrace=False,
                )
        else:
            orig = self.read_ref(ref)
            tmp = ref.with_suffix(".orig")
            self.write_file(tmp, buf)
            assert Guard(buf, tmp) == Guard(orig, ref)

    def read_ref(self, ref: Path) -> str:
        __tracebackhide__ = True
        if not ref.exists():
            rel_ref = self.rel(ref)
            pytest.fail(
                f"The reference {rel_ref} doesn't exist.\n"
                "Create it yourself or run pytest with '--rich-gen' option."
            )
        else:
            return ref.read_text()

    def write_file(self, ref: Path, buf: str) -> None:
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text(buf)

    def write_ref(self, ref: Path, buf: str) -> bool:
        if ref.exists():
            orig = ref.read_text()
            if orig == buf:
                return False
        self.write_file(ref, buf)
        if self._reporter.verbosity > 0:
            rel_ref = self.rel(ref)
            self._reporter.write_line(f"Regenerate {rel_ref}", yellow=True)
        self._written_refs.append(ref)
        return True

    def summary(self) -> None:
        if self._reporter.verbosity == 0:
            if self._written_refs:
                self._reporter.write_line("Regenerated files:", yellow=True)
                for fname in self._written_refs:
                    rel_ref = self.rel(fname)
                    self._reporter.write_line(f"  {rel_ref}", yellow=True)

    def diff(self, lft: Guard, rgt: Guard) -> List[str]:
        # The same as _diff_text from
        # https://github.com/pytest-dev/pytest/blob/master/src/_pytest/assertion/util.py#L200-L245 plus a few extra lines with additional instructions.  # noqa
        explanation: List[str] = []

        left = click.unstyle(lft.arg)
        right = click.unstyle(rgt.arg)

        if self._reporter.verbosity < 1:
            i = 0  # just in case left or right has zero length
            for i in range(min(len(left), len(right))):
                if left[i] != right[i]:
                    break
            if i > 42:
                i -= 10  # Provide some context
                explanation = [
                    "Skipping %s identical leading characters in diff, use -v to show"
                    % i
                ]
                left = left[i:]
                right = right[i:]
            if len(left) == len(right):
                for i in range(len(left)):
                    if left[-i] != right[-i]:
                        break
                if i > 42:
                    i -= 10  # Provide some context
                    explanation += [
                        "Skipping {} identical trailing "
                        "characters in diff, use -v to show".format(i)
                    ]
                    left = left[:-i]
                    right = right[:-i]

        keepends = True
        if left.isspace() or right.isspace():
            left = repr(str(left))
            right = repr(str(right))
            explanation += [
                "Strings contain only whitespace, escaping them using repr()"
            ]
        # "right" is the expected base against which we compare "left",
        # see https://github.com/pytest-dev/pytest/issues/3333
        explanation += [
            line.strip("\n")
            for line in ndiff(right.splitlines(keepends), left.splitlines(keepends))
        ]
        explanation.append("")
        explanation.append(f"'cat {self.rel(lft.path)}' to see the test output.")
        explanation.append(f"'cat {self.rel(rgt.path)}' to see the reference.")
        explanation.append(
            f"Use 'pytest ... --rich-gen' to regenerate reference files "
            "from values calculated by tests"
        )
        return explanation


def pytest_assertrepr_compare(
    config: Any, op: str, left: object, right: object
) -> Optional[List[str]]:
    if isinstance(left, Guard) and isinstance(right, Guard):
        plugin = config.pluginmanager.getplugin("rich-comparator")
        return plugin.diff(left, right)
    return None


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
