from unittest.mock import patch

import aiohttp

from utils import JsonResponse, mocked_async_context_manager


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "status": "failed",
                "id": "foo",
                "description": "This is job description, not a history description",
                "history": {
                    "created_at": "2018-08-29T12:23:13.981621+00:00",
                    "started_at": "2018-08-29T12:23:15.988054+00:00",
                    "finished_at": "2018-08-29T12:59:31.427795+00:00",
                    "reason": "ContainerCannotRun",
                    "description": "Not enough coffee",
                },
            }
        )
    ),
)
def test_status_failed(jobs):
    expected = {
        "status": "failed",
        "id": "foo",
        "description": "This is job description, not a history description",
        "history": {
            "created_at": "2018-08-29T12:23:13.981621+00:00",
            "started_at": "2018-08-29T12:23:15.988054+00:00",
            "finished_at": "2018-08-29T12:59:31.427795+00:00",
            "reason": "ContainerCannotRun",
            "description": "Not enough coffee",
        },
    }
    res = jobs.status("1")
    assert {
        "status": res.status,
        "id": res.id,
        "description": res.description,
        "history": {
            "created_at": res.history.created_at,
            "started_at": res.history.started_at,
            "finished_at": res.history.finished_at,
            "reason": res.history.reason,
            "description": res.history.description,
        },
    } == expected

    aiohttp.ClientSession.request.assert_called_with(
        method="GET",
        url="http://127.0.0.1/jobs/1",
        params=None,
        headers=None,
        data=None,
        json=None,
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "status": "failed",
                "id": "foo",
                "description": "This is job description, not a history description",
                "http_url": "http://my_host:8889",
                "ssh_server": "ssh://my_host.ssh:22",
                "history": {
                    "created_at": "2018-08-29T12:23:13.981621+00:00",
                    "started_at": "2018-08-29T12:23:15.988054+00:00",
                    "finished_at": "2018-08-29T12:59:31.427795+00:00",
                    "reason": "ContainerCannotRun",
                    "description": "Not enough coffee",
                },
            }
        )
    ),
)
def test_status_with_ssh_and_http(jobs):
    expected = {
        "status": "failed",
        "id": "foo",
        "description": "This is job description, not a history description",
        "http_url": "http://my_host:8889",
        "ssh": "ssh://my_host.ssh:22",
        "history": {
            "created_at": "2018-08-29T12:23:13.981621+00:00",
            "started_at": "2018-08-29T12:23:15.988054+00:00",
            "finished_at": "2018-08-29T12:59:31.427795+00:00",
            "reason": "ContainerCannotRun",
            "description": "Not enough coffee",
        },
    }
    res = jobs.status("1")
    assert {
        "status": res.status,
        "id": "foo",
        "description": res.description,
        "http_url": res.url,
        "ssh": res.ssh,
        "history": {
            "created_at": res.history.created_at,
            "started_at": res.history.started_at,
            "finished_at": res.history.finished_at,
            "reason": res.history.reason,
            "description": res.history.description,
        },
    } == expected

    aiohttp.ClientSession.request.assert_called_with(
        method="GET",
        url="http://127.0.0.1/jobs/1",
        params=None,
        headers=None,
        data=None,
        json=None,
    )
