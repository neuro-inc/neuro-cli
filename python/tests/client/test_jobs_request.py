# Test sets defined to ensure proper payload is being sent to the server
# API calls are mocked, tests ensure that client side wrappers pass correct json
# and properly read response from server side
from unittest.mock import patch

import aiohttp

from tests.utils import JsonResponse, mocked_async_context_manager


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "status": "running",
                "id": "foo",
                "history": {
                    "created_at": "2018-08-29T12:23:13.981621+00:00",
                    "started_at": "2018-08-29T12:23:15.988054+00:00",
                },
            }
        )
    ),
)
def test_status_running(jobs):
    expected = {
        "status": "running",
        "id": "foo",
        "history": {
            "created_at": "2018-08-29T12:23:13.981621+00:00",
            "started_at": "2018-08-29T12:23:15.988054+00:00",
        },
    }
    res = jobs.status("1")
    assert {
        "status": res.status,
        "id": "foo",
        "history": {
            "created_at": res.history.created_at,
            "started_at": res.history.started_at,
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
