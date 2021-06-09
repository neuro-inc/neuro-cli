import contextlib
import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import certifi
import click
import dateutil.parser
import pkg_resources
from typing_extensions import TypedDict
from yarl import URL

from neuro_sdk import Client

import neuro_cli


class Record(TypedDict):
    package: str
    version: str
    uploaded: float
    checked: float


log = logging.getLogger(__name__)


SCHEMA = {
    "pypi": "CREATE TABLE pypi "
    "(package TEXT, version TEXT, uploaded REAL, checked REAL)",
}
DROP = {"pypi": "DROP TABLE IF EXISTS pypi"}


async def run_version_checker(client: Client, disable_check: bool) -> None:
    if disable_check:
        return
    with client.config._open_db() as db:
        _ensure_schema(db)
        neurocli_db = _read_package(db, "neuro-cli")
        neuromation_db = _read_package(db, "neuromation")
        certifi_db = _read_package(db, "certifi")

    _warn_maybe(neurocli_db, neuromation_db, certifi_db)
    inserts: List[Tuple[str, str, float, float]] = []
    await _add_record(client, "neuromation", neuromation_db, inserts)
    await _add_record(client, "neuro-cli", neuromation_db, inserts)
    await _add_record(client, "certifi", certifi_db, inserts)
    with client.config._open_db() as db:
        db.executemany(
            """
            INSERT INTO pypi (package, version, uploaded, checked)
            VALUES (?, ?, ?, ?)
        """,
            inserts,
        )
        db.execute("DELETE FROM pypi WHERE checked < ?", (time.time() - 7 * 24 * 3600,))
        with contextlib.suppress(sqlite3.OperationalError):
            db.commit()


async def _add_record(
    client: Client,
    package: str,
    record: Optional[Record],
    inserts: List[Tuple[str, str, float, float]],
) -> None:
    if record is None or time.time() - record["checked"] > 10 * 60:
        pypi = await _fetch_package(client._session, package)
        if pypi is None:
            return
        inserts.append(
            (
                pypi["package"],
                pypi["version"],
                pypi["uploaded"],
                pypi["checked"],
            )
        )


def _ensure_schema(db: sqlite3.Connection) -> None:
    cur = db.cursor()
    ok = True
    found = set()
    cur.execute("SELECT type, name, sql from sqlite_master")
    for type, name, sql in cur:
        if type not in ("table", "index"):
            continue
        if name in SCHEMA:
            if SCHEMA[name] != sql:
                ok = False
                break
            else:
                found.add(name)

    if not ok or found < SCHEMA.keys():
        for sql in reversed(list(DROP.values())):
            cur.execute(sql)
        for sql in SCHEMA.values():
            cur.execute(sql)


READ_PACKAGE = """
    SELECT package, version, uploaded, checked
    FROM pypi
    WHERE package = ?
    ORDER BY checked
    LIMIT 1
"""


def _read_package(db: sqlite3.Connection, package: str) -> Optional[Record]:
    cur = db.execute(READ_PACKAGE, (package,))
    return cur.fetchone()


async def _fetch_package(
    session: aiohttp.ClientSession, package: str
) -> Optional[Record]:
    url = URL(f"https://pypi.org/pypi/{package}/json")
    async with session.get(url) as resp:
        if resp.status != 200:
            log.debug("%s status on fetching %s", resp.status, url)
            return None
        pypi_response = await resp.json()
        version = _parse_max_version(pypi_response)
        if version is None:
            return None
        uploaded = _parse_version_upload_time(pypi_response, version)
        return {
            "package": package,
            "version": version,
            "uploaded": uploaded,
            "checked": time.time(),
        }


def _parse_date(value: str) -> float:
    # from format: "2019-08-19"
    return dateutil.parser.parse(value).timestamp()


def _parse_max_version(pypi_response: Dict[str, Any]) -> Optional[str]:
    try:
        ret = [version for version in pypi_response["releases"].keys()]
        return max(
            ver for ver in ret if not pkg_resources.parse_version(ver).is_prerelease
        )
    except (KeyError, ValueError):
        return None


def _parse_version_upload_time(
    pypi_response: Dict[str, Any], target_version: str
) -> float:
    try:
        dates = [
            _parse_date(info["upload_time"])
            for version, info_list in pypi_response["releases"].items()
            for info in info_list
            if version == target_version
        ]
        return max(dates)
    except (KeyError, ValueError):
        return 0


def _warn_maybe(
    neurocli_db: Optional[Record],
    neuromation_db: Optional[Record],
    certifi_db: Optional[Record],
    *,
    certifi_warning_delay: int = 14 * 3600 * 24,
) -> None:

    if neurocli_db is not None:
        current = pkg_resources.parse_version(neuro_cli.__version__)
        pypi = pkg_resources.parse_version(neurocli_db["version"])
        if current < pypi:
            update_command = "pip install --upgrade neuro-cli"
            click.secho(
                f"You are using Neuro Platform Client {current}, "
                f"however {pypi} is available.\n"
                f"You should consider upgrading via "
                f"the '{update_command}' command.",
                err=True,
                fg="yellow",
            )
    elif neuromation_db is not None:
        current = pkg_resources.parse_version(neuro_cli.__version__)
        pypi = pkg_resources.parse_version(neuromation_db["version"])
        if current < pypi:
            update_command = "pip install --upgrade neuromation"
            click.secho(
                f"You are using Neuro Platform Client {current}, "
                f"however {pypi} is available.\n"
                f"You should consider upgrading via "
                f"the '{update_command}' command.",
                err=True,
                fg="yellow",
            )

    if certifi_db is not None:
        current = pkg_resources.parse_version(certifi.__version__)  # type: ignore
        pypi = pkg_resources.parse_version(certifi_db["version"])
        if (
            current < pypi
            and time.time() - certifi_db["uploaded"] > certifi_warning_delay
        ):
            pip_update_command = "pip install --upgrade certifi"
            conda_update_command = "conda update certifi"
            click.secho(
                f"Your root certificates are out of date.\n"
                f"You are using certifi {current}, "
                f"however {pypi} is available.\n"
                f"Please consider upgrading certifi package, e.g.\n"
                f"    {pip_update_command}\n"
                f"or\n"
                f"    {conda_update_command}",
                err=True,
                fg="red",
            )
