# Google Measurement Protocol

import json
import logging
import sqlite3
import time
import uuid
from typing import Dict, List, Optional
from urllib.parse import quote as urlquote, urlencode

from yarl import URL

import neuromation
from neuromation.api import Client


logger = logging.getLogger(__name__)

GA_URL = URL("https://www.google-analytics.com/batch")

# Google Analytics supports up to 20 records in a batch
GA_CACHE_LIMIT = 20

SCHEMA = {
    "stats": "CREATE TABLE stats (cmd TEXT, args TEXT, timestamp REAL, version TEXT)",
    "uid": "CREATE TABLE uid (uid TEXT)",
}
DROP = {"stats": "DROP TABLE IF EXISTS stats", "uid": "DROP TABLE IF EXISTS uid"}


def ensure_schema(db: sqlite3.Connection) -> str:
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
    cur.execute("SELECT uid FROM uid")
    lst = list(cur)
    if len(lst) > 0:
        return lst[0][0]
    else:
        uid = str(uuid.uuid4())
        cur.execute("INSERT INTO uid (uid) VALUES (?)", (uid,))
        db.commit()
    return uid


def add_usage(
    db: sqlite3.Connection, cmd: str, args: List[Dict[str, Optional[str]]]
) -> None:
    cur = db.cursor()
    cur.execute(
        "INSERT INTO stats (cmd, args, timestamp, version) VALUES (?, ?, ?, ?)",
        (cmd, urlquote(json.dumps(args)), time.time(), neuromation.__version__),
    )


def _make_record(uid: str, url: URL, cmd: str, args: str, version: str) -> str:
    ret = {
        "v": "1",
        "t": "event",
        "tid": "UA-106571369-3",
        "cid": uid,
        "ec": "CLI",
        "ea": cmd,
        "el": args,
        "av": version,
        "aid": str(url),
    }
    return urlencode(ret, quote_via=urlquote)


async def send(client: Client, uid: str, data: List[sqlite3.Row]) -> None:
    if not data:
        return
    payload = "\n".join(
        _make_record(
            uid, client.config.api_url, row["cmd"], row["args"], row["version"]
        )
        for row in data
    )
    async with client._session.post(GA_URL, data=payload) as resp:
        resp


async def upload_gmp_stats(
    client: Client,
    cmd: str,
    args: List[Dict[str, Optional[str]]],
    skip_gmp_stats: bool,
) -> None:
    if skip_gmp_stats:
        return
    try:
        with client.config._open_db() as db:
            uid = ensure_schema(db)
            # oldest 20 records
            old = list(
                db.execute(
                    """
                    SELECT ROWID, cmd, args, timestamp, version
                    FROM stats ORDER BY ROWID ASC LIMIT ?
                    """,
                    (GA_CACHE_LIMIT,),
                )
            )
            if (
                old
                and len(old) < GA_CACHE_LIMIT
                and old[-1]["timestamp"] > time.time() - 3600
            ):
                # A few data, the last recored is younger that one hour old;
                # don't send these data to google server
                old = []
            add_usage(db, cmd, args)
            db.commit()
        await send(client, uid, old)
        with client.config._open_db() as db:
            db.executemany(
                "DELETE FROM stats WHERE ROWID = ?", [[row["ROWID"]] for row in old]
            )
            db.commit()
    except sqlite3.DatabaseError as exc:
        if str(exc) != "database is locked":
            logger.warning("Cannot send the usage statistics: %s", repr(exc))
        else:
            logger.debug("Cannot send the usage statistics: %s", repr(exc))
