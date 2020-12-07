import asyncio
import socket
import ssl
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import aiohttp
import dateutil.parser
import pytest
import trustme
from aiohttp import web
from aiohttp.abc import AbstractResolver
from aiohttp.test_utils import unused_port

from neuromation.api import Client
from neuromation.cli import version_utils
from neuromation.cli.root import Root


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
            "python-jose (>=3.0.0)",
            "python-dateutil (>=2.7.0)",
            "yarl (>=1.3.0)",
            "aiodocker (>=0.14.0)",
            "click (>=4.0)",
            'dataclasses (>=0.5) ; python_version < "3.7"',
            'async-generator (>=1.5) ; python_version < "3.7"',
        ],
        "requires_python": ">=3.6.0",
        "summary": "Neuro Platform API client",
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
            },
            {
                "comment_text": "",
                "digests": {
                    "md5": "d8cb5a5984c291e69b9b0bf34423c865",
                    "sha256": "046832c04d4e7...38f6514d0e5b9acc4939",
                },
                "downloads": -1,
                "filename": "neuromation-0.2.1.tar.gz",
                "has_sig": False,
                "md5_digest": "af8fea5f3df6f7f81e9c6cbc6dd7c1e8",
                "packagetype": "sdist",
                "python_version": "source",
                "requires_python": None,
                "size": 156721,
                "upload_time": "2019-01-30T00:02:23",
                "url": "https://files.pytho...ation-0.2.1.tar.gz",
            },
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
def tls_certificate_authority() -> Any:
    return trustme.CA()


@pytest.fixture
def tls_certificate(tls_certificate_authority: Any) -> Any:
    return tls_certificate_authority.issue_server_cert("localhost", "127.0.0.1", "::1")


@pytest.fixture
def ssl_ctx(tls_certificate: Any) -> ssl.SSLContext:
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    tls_certificate.configure_cert(ssl_ctx)
    return ssl_ctx


@pytest.fixture
def client_ssl_ctx(tls_certificate_authority: Any) -> ssl.SSLContext:
    ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    tls_certificate_authority.configure_trust(ssl_ctx)
    return ssl_ctx


class FakeResolver(AbstractResolver):
    _LOCAL_HOST = {0: "127.0.0.1", socket.AF_INET: "127.0.0.1", socket.AF_INET6: "::1"}

    def __init__(self, fakes: Dict[str, int]) -> None:
        """fakes -- dns -> port dict"""
        self._fakes = fakes

    async def resolve(
        self, host: str, port: int = 0, family: int = socket.AF_INET
    ) -> List[Dict[str, Any]]:
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
        self.runner: Optional[web.AppRunner] = None
        self.ssl_context = ssl_context
        self.response: Optional[Tuple[int, Dict[str, Any]]] = None

    async def start(self) -> Dict[str, int]:
        port = unused_port()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", port, ssl_context=self.ssl_context)
        await site.start()
        return {"pypi.org": port}

    async def stop(self) -> None:
        assert self.runner is not None
        await self.runner.cleanup()

    async def json_info(self, request: web.Request) -> web.Response:
        assert self.response is not None
        return web.json_response(self.response[1], status=self.response[0])


@pytest.fixture()
async def fake_pypi(
    ssl_ctx: ssl.SSLContext, loop: asyncio.AbstractEventLoop
) -> AsyncIterator[Tuple[FakePyPI, Dict[str, int]]]:
    fake_pypi = FakePyPI(ssl_ctx)
    info = await fake_pypi.start()
    yield fake_pypi, info
    await fake_pypi.stop()


@pytest.fixture()
async def client(fake_pypi: Tuple[FakePyPI, Dict[str, int]], root: Root) -> Client:
    resolver = FakeResolver(fake_pypi[1])
    connector = aiohttp.TCPConnector(resolver=resolver, ssl=False)
    session = aiohttp.ClientSession(connector=connector)
    old_session = root.client._session
    await old_session.close()
    root.client._session = session
    return root.client


@pytest.fixture
def pypi_server(fake_pypi: Tuple[FakePyPI, Dict[str, int]]) -> FakePyPI:
    return fake_pypi[0]


async def test__fetch_pypi(pypi_server: FakePyPI, client: Client) -> None:
    pypi_server.response = (200, PYPI_JSON)

    t0 = time.time()
    record = await version_utils._fetch_package(client._session, "neuromation")
    assert record is not None
    assert record["version"] == "0.2.1"
    assert (
        record["uploaded"] == dateutil.parser.parse("2019-01-30T00:02:23").timestamp()
    )
    assert t0 <= record["checked"] <= time.time()


async def test__fetch_pypi_no_releases(pypi_server: FakePyPI, client: Client) -> None:
    pypi_server.response = (200, {})

    record = await version_utils._fetch_package(client._session, "neuromation")
    assert record is None


async def test__fetch_pypi_non_200(pypi_server: FakePyPI, client: Client) -> None:
    pypi_server.response = (403, {"Status": "Forbidden"})

    record = await version_utils._fetch_package(client._session, "neuromation")
    assert record is None


async def test_run_version_checker(pypi_server: FakePyPI, client: Client) -> None:
    pypi_server.response = (200, PYPI_JSON)

    await version_utils.run_version_checker(client, False)
    with client.config._open_db() as db:
        ret = list(db.execute("SELECT package, version FROM pypi"))
        assert len(ret) == 1
        assert list(ret[0]) == ["neuromation", "0.2.1"]


async def test_run_version_checker_disabled(
    pypi_server: FakePyPI, client: Client
) -> None:
    pypi_server.response = (200, PYPI_JSON)

    with client.config._open_db() as db:
        version_utils._ensure_schema(db)

    await version_utils.run_version_checker(client, True)
    with client.config._open_db() as db:
        ret = list(db.execute("SELECT package, version FROM pypi"))
        assert len(ret) == 0
