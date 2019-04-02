import asyncio
import socket
import ssl
from pathlib import Path
from typing import Dict, Tuple

import aiohttp
import pkg_resources
import pytest
import trustme
from aiohttp import web
from aiohttp.abc import AbstractResolver
from aiohttp.test_utils import unused_port

from neuromation.cli.rc import ConfigFactory
from neuromation.cli.version_utils import VersionChecker


@pytest.fixture
def nmrc(tmp_path):
    return tmp_path / ".nmrc"


@pytest.fixture
def patch_home_for_test(monkeypatch, nmrc):
    def home():
        return nmrc.parent

    monkeypatch.setattr(Path, "home", home)


PYPI_JSON = {
    "info": {
        "author": "Neuromation Team",
        "author_email": "pypi@neuromation.io",
        "bugtrack_url": None,
        "classifiers": [
            "Development Status :: 4 - Beta",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "Intended Audience :: Information Technology",
            "Intended Audience :: Science/Research",
            "License :: Other/Proprietary License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Software Development",
            "Topic :: Utilities",
        ],
        "description": "blablabla this is description",
        "description_content_type": "text/markdown",
        "docs_url": None,
        "download_url": "",
        "downloads": {"last_day": -1, "last_month": -1, "last_week": -1},
        "home_page": "https://neuromation.io/",
        "keywords": "",
        "license": "",
        "maintainer": "",
        "maintainer_email": "",
        "name": "neuromation",
        "package_url": "https://pypi.org/project/neuromation/",
        "platform": "",
        "project_url": "https://pypi.org/project/neuromation/",
        "project_urls": {"Homepage": "https://neuromation.io/"},
        "release_url": "https://pypi.org/project/neuromation/0.2.1/",
        "requires_dist": [
            "aiohttp (>=3.0)",
            "pyyaml (>=3.0)",
            "python-jose (>=3.0.0)",
            "python-dateutil (>=2.7.0)",
            "yarl (>=1.3.0)",
            "aiodocker (>=0.14.0)",
            "click (>=4.0)",
            'dataclasses (>=0.5) ; python_version < "3.7"',
            'async-generator (>=1.5) ; python_version < "3.7"',
        ],
        "requires_python": ">=3.6.0",
        "summary": "Neuromation Platform API client",
        "version": "0.2.1",
    },
    "last_serial": 4757285,
    "releases": {
        "0.2.0b0": [
            {
                "comment_text": "",
                "digests": {
                    "md5": "bc66247d61fcedb18e6dcc87f4f2bbbe",
                    "sha256": "6747274972648...abe9d8ba44f59635bac6e",
                },
                "downloads": -1,
                "filename": "neuromation-0.2.0b0-py3-none-any.whl",
                "has_sig": False,
                "md5_digest": "bc66247d61fcedb18e6dcc87f4f2bbbe",
                "packagetype": "bdist_wheel",
                "python_version": "py3",
                "requires_python": ">=3.6.0",
                "size": 47043,
                "upload_time": "2019-01-28T20:01:21",
                "url": "https://files.pytho...ation-0.2.1-py3-none-any.whl",
            }
        ],
        "0.2.1": [
            {
                "comment_text": "",
                "digests": {
                    "md5": "8dd303ee04215ff7f5c2e7f03a6409da",
                    "sha256": "fd50b1f904c4...af6213c363ec5a83f3168aae1b8",
                },
                "downloads": -1,
                "filename": "neuromation-0.2.1-py3-none-any.whl",
                "has_sig": False,
                "md5_digest": "8dd303ee04215ff7f5c2e7f03a6409da",
                "packagetype": "bdist_wheel",
                "python_version": "py3",
                "requires_python": ">=3.6.0",
                "size": 48633,
                "upload_time": "2019-01-29T23:45:22",
                "url": "https://files.pytho...ation-0.2.1-py3-none-any.whl",
            }
        ],
    },
    "urls": [
        {
            "comment_text": "",
            "digests": {
                "md5": "8dd303ee04215ff7f5c2e7f03a6409da",
                "sha256": "fd50b1f90c...c5a83f3168aae1b8",
            },
            "downloads": -1,
            "filename": "neuromation-0.2.1-py3-none-any.whl",
            "has_sig": False,
            "md5_digest": "8dd303ee04215ff7f5c2e7f03a6409da",
            "packagetype": "bdist_wheel",
            "python_version": "py3",
            "requires_python": ">=3.6.0",
            "size": 48633,
            "upload_time": "2019-01-29T23:45:22",
            "url": "https://files.pytho...ation-0.2.1-py3-none-any.whl",
        }
    ],
}


@pytest.fixture
def tls_certificate_authority():
    return trustme.CA()


@pytest.fixture
def tls_certificate(tls_certificate_authority):
    return tls_certificate_authority.issue_server_cert("localhost", "127.0.0.1", "::1")


@pytest.fixture
def ssl_ctx(tls_certificate):
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    tls_certificate.configure_cert(ssl_ctx)
    return ssl_ctx


@pytest.fixture
def client_ssl_ctx(tls_certificate_authority):
    ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    tls_certificate_authority.configure_trust(ssl_ctx)
    return ssl_ctx


class FakeResolver(AbstractResolver):
    _LOCAL_HOST = {0: "127.0.0.1", socket.AF_INET: "127.0.0.1", socket.AF_INET6: "::1"}

    def __init__(self, fakes):
        """fakes -- dns -> port dict"""
        self._fakes = fakes

    async def resolve(self, host, port=0, family=socket.AF_INET):
        return [
            {
                "hostname": host,
                "host": "127.0.0.1",
                "port": self._fakes["pypi.org"],
                "family": family,
                "proto": 0,
                "flags": socket.AI_NUMERICHOST,
            }
        ]

    async def close(self) -> None:
        pass


class FakePyPI:
    def __init__(self, ssl_context: ssl.SSLContext) -> None:
        self.app = web.Application()
        self.app.router.add_routes([web.get("/pypi/neuromation/json", self.json_info)])
        self.runner = None
        self.ssl_context = ssl_context
        self.response = None

    async def start(self):
        port = unused_port()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", port, ssl_context=self.ssl_context)
        await site.start()
        return {"pypi.org": port}

    async def stop(self):
        await self.runner.cleanup()

    async def json_info(self, request):
        return web.json_response(self.response[1], status=self.response[0])


@pytest.fixture()
async def fake_pypi(ssl_ctx: ssl.SSLContext, loop: asyncio.AbstractEventLoop) -> None:
    fake_pypi = FakePyPI(ssl_ctx)
    info = await fake_pypi.start()
    yield fake_pypi, info
    await fake_pypi.stop()


@pytest.fixture()
async def connector(fake_pypi: Tuple[FakePyPI, Dict[str, int]]) -> aiohttp.TCPConnector:
    resolver = FakeResolver(fake_pypi[1])
    async with aiohttp.TCPConnector(resolver=resolver, ssl=False) as connector:
        yield connector


@pytest.fixture
def pypi_server(fake_pypi: Tuple[FakePyPI, Dict[str, int]]):
    return fake_pypi[0]


async def test__fetch_pypi(pypi_server, connector: aiohttp.TCPConnector) -> None:
    pypi_server.response = (200, PYPI_JSON)

    async with VersionChecker(connector=connector) as checker:
        version = await checker._fetch_pypi()
        assert version == pkg_resources.parse_version("0.2.1")


async def test__fetch_pypi_no_releases(
    pypi_server, connector: aiohttp.TCPConnector
) -> None:
    pypi_server.response = (200, {})

    async with VersionChecker(connector=connector) as checker:
        version = await checker._fetch_pypi()
        assert version == pkg_resources.parse_version("0.0.0")


async def test__fetch_pypi_non_200(
    pypi_server, connector: aiohttp.TCPConnector
) -> None:
    pypi_server.response = (403, {"Status": "Forbidden"})

    async with VersionChecker(connector=connector) as checker:
        version = await checker._fetch_pypi()
        assert version == pkg_resources.parse_version("0.0.0")


async def test_update_latest_version(
    pypi_server, connector: aiohttp.TCPConnector, patch_home_for_test
) -> None:
    pypi_server.response = (200, PYPI_JSON)

    async with VersionChecker(connector=connector) as checker:
        await checker.update_latest_version()

    cfg = ConfigFactory.load()
    assert cfg.pypi.pypi_version == pkg_resources.parse_version("0.2.1")


async def test_run(
    pypi_server, connector: aiohttp.TCPConnector, patch_home_for_test
) -> None:
    pypi_server.response = (200, PYPI_JSON)

    checker = VersionChecker(connector=connector)
    await checker.run()

    cfg = ConfigFactory.load()
    assert cfg.pypi.pypi_version == pkg_resources.parse_version("0.2.1")


async def test_run_cancelled(
    pypi_server, connector: aiohttp.TCPConnector, patch_home_for_test
) -> None:
    loop = asyncio.get_event_loop()
    pypi_server.response = (200, PYPI_JSON)

    checker = VersionChecker(connector=connector)
    task = loop.create_task(checker.run())
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    cfg = ConfigFactory.load()
    assert cfg.pypi.pypi_version == pkg_resources.parse_version("0.0.0")


async def test_run_cancelled_with_delay(
    pypi_server, connector: aiohttp.TCPConnector, patch_home_for_test
) -> None:
    loop = asyncio.get_event_loop()
    pypi_server.response = (200, PYPI_JSON)

    checker = VersionChecker(connector=connector)
    task = loop.create_task(checker.run())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    cfg = ConfigFactory.load()
    assert cfg.pypi.pypi_version == pkg_resources.parse_version("0.0.0")


async def test_run_no_server(patch_home_for_test) -> None:
    port = unused_port()
    resolver = FakeResolver({"pypi.org": port})
    connector = aiohttp.TCPConnector(resolver=resolver, ssl=False)

    checker = VersionChecker(connector=connector)
    await checker.run()

    cfg = ConfigFactory.load()
    assert cfg.pypi.pypi_version == pkg_resources.parse_version("0.0.0")
