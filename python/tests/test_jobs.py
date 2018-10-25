from unittest.mock import patch

import aiohttp
import pytest

from neuromation.client import ClientError, ResourceNotFound
from neuromation.client.jobs import JobDescription, Resources
from utils import (
    BinaryResponse,
    JsonResponse,
    PlainResponse,
    mocked_async_context_manager,
)


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {"error": "blah!"},
            error=aiohttp.ClientResponseError(
                request_info=None, history=None, status=404, message="ah!"
            ),
        )
    ),
)
def test_jobnotfound_error(jobs):
    with pytest.raises(ResourceNotFound):
        jobs.kill("blah")


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {"error": "blah!"},
            error=aiohttp.ClientResponseError(
                request_info=None, history=None, status=405, message="ah!"
            ),
        )
    ),
)
def test_kill_already_killed_job_error(jobs):
    with pytest.raises(ClientError):
        jobs.kill("blah")


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {"error": "blah!"},
            error=aiohttp.ClientResponseError(
                request_info=None, history=None, status=404, message="ah!"
            ),
        )
    ),
)
def test_monitor_notexistent_job(jobs):
    with pytest.raises(ResourceNotFound):
        with jobs.monitor("blah") as stream:
            stream.read()


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(PlainResponse(text="")),
)
def test_kill(jobs):
    assert jobs.kill("1")

    aiohttp.ClientSession.request.assert_called_with(
        method="DELETE",
        url="http://127.0.0.1/jobs/1",
        params=None,
        data=None,
        json=None,
    )


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
def test_status_runing(jobs):
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
        method="GET", url="http://127.0.0.1/jobs/1", params=None, data=None, json=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "status": "failed",
                "id": "foo",
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
        "history": {
            "created_at": res.history.created_at,
            "started_at": res.history.started_at,
            "finished_at": res.history.finished_at,
            "reason": res.history.reason,
            "description": res.history.description,
        },
    } == expected

    aiohttp.ClientSession.request.assert_called_with(
        method="GET", url="http://127.0.0.1/jobs/1", params=None, data=None, json=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "status": "failed",
                "id": "foo",
                "http_url": "http://my_host:8889",
                "ssh_connection": "ssh://my_host.ssh:22",
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
        method="GET", url="http://127.0.0.1/jobs/1", params=None, data=None, json=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "jobs": [
                    {"status": "RUNNING", "id": "foo"},
                    {"status": "STARTING", "id": "bar"},
                ]
            }
        )
    ),
)
def test_list(jobs):
    assert jobs.list() == [
        JobDescription(client=jobs, id="foo", status="RUNNING"),
        JobDescription(client=jobs, id="bar", status="STARTING"),
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method="GET", json=None, url="http://127.0.0.1/jobs", params=None, data=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "jobs": [
                    {
                        "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
                        "status": "failed",
                        "history": {
                            "status": "failed",
                            "reason": "Error",
                            "description": "Mounted on Avail\\n/dev/shm     "
                            "64M\\n\\nExit code: 1",
                            "created_at": "2018-09-25T12:28:21.298672+00:00",
                            "started_at": "2018-09-25T12:28:59.759433+00:00",
                            "finished_at": "2018-09-25T12:28:59.759433+00:00",
                        },
                        "container": {
                            "image": "gcr.io/light-reality-205619/ubuntu:latest",
                            "command": 'bash -c " / bin / df--block - size M--output '
                            '= target, avail / dev / shm;false"',
                            "resources": {
                                "cpu": 1.0,
                                "memory_mb": 16384,
                                "gpu": 1,
                                "shm": False,
                            },
                        },
                    }
                ]
            }
        )
    ),
)
def test_list_extended_output(jobs):
    assert jobs.list() == [
        JobDescription(
            client=jobs,
            id="job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            status="failed",
            image="gcr.io/light-reality-205619/ubuntu:latest",
            command='bash -c " / bin / df--block - size M--output'
            ' = target, avail / dev / shm;false"',
            resources=Resources(memory=16384, cpu=1.0, gpu=1, shm=False),
        )
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method="GET", json=None, url="http://127.0.0.1/jobs", params=None, data=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "jobs": [
                    {
                        "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
                        "status": "failed",
                        "history": {
                            "status": "failed",
                            "reason": "Error",
                            "description": "Mounted on Avail\\n/dev/shm     "
                            "64M\\n\\nExit code: 1",
                            "created_at": "2018-09-25T12:28:21.298672+00:00",
                            "started_at": "2018-09-25T12:28:59.759433+00:00",
                            "finished_at": "2018-09-25T12:28:59.759433+00:00",
                        },
                        "container": {
                            "image": "gcr.io/light-reality-205619/ubuntu:latest",
                            "command": 'bash -c " / bin / df--block - size M--output '
                            '= target, avail / dev / shm;false"',
                            "resources": {
                                "cpu": 1.0,
                                "memory_mb": 16384,
                                "gpu": 1,
                                "shm": False,
                            },
                        },
                        "http_url": "http://my_host:8889",
                        "ssh_connection": "ssh://my_host.ssh:22",
                    }
                ]
            }
        )
    ),
)
def test_list_extended_output_with_http_url(jobs):
    assert jobs.list() == [
        JobDescription(
            client=jobs,
            id="job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            status="failed",
            url="http://my_host:8889",
            ssh="ssh://my_host.ssh:22",
            image="gcr.io/light-reality-205619/ubuntu:latest",
            command='bash -c " / bin / df--block - size M--output'
            ' = target, avail / dev / shm;false"',
            resources=Resources(memory=16384, cpu=1.0, gpu=1, shm=False),
        )
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method="GET", json=None, url="http://127.0.0.1/jobs", params=None, data=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "jobs": [
                    {
                        "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
                        "status": "failed",
                        "history": {
                            "status": "failed",
                            "reason": "Error",
                            "description": "Mounted on Avail\\n/dev/shm"
                            "     64M\\n\\nExit code: 1",
                            "created_at": "2018-09-25T12:28:21.298672+00:00",
                            "started_at": "2018-09-25T12:28:59.759433+00:00",
                            "finished_at": "2018-09-25T12:28:59.759433+00:00",
                        },
                        "container": {
                            "image": "gcr.io/light-reality-205619/ubuntu:latest",
                            "command": 'bash -c " / bin / df--block - size M--output = '
                            'target, avail / dev / shm;false"',
                            "resources": {"cpu": 1.0, "memory_mb": 16384, "gpu": 1},
                        },
                    }
                ]
            }
        )
    ),
)
def test_list_extended_output_no_shm(jobs):
    assert jobs.list() == [
        JobDescription(
            client=jobs,
            id="job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            status="failed",
            image="gcr.io/light-reality-205619/ubuntu:latest",
            command='bash -c " / bin / df--block - size M--output '
            '= target, avail / dev / shm;false"',
            resources=Resources(memory=16384, cpu=1.0, gpu=1, shm=None),
        )
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method="GET", json=None, url="http://127.0.0.1/jobs", params=None, data=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "jobs": [
                    {
                        "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
                        "status": "failed",
                        "history": {
                            "status": "failed",
                            "reason": "Error",
                            "description": "Mounted on Avail\\n/dev/shm"
                            "     64M\\n\\nExit code: 1",
                            "created_at": "2018-09-25T12:28:21.298672+00:00",
                            "started_at": "2018-09-25T12:28:59.759433+00:00",
                            "finished_at": "2018-09-25T12:28:59.759433+00:00",
                        },
                        "container": {
                            "image": "gcr.io/light-reality-205619/ubuntu:latest",
                            "command": 'bash -c " / bin / df--block - size M--output = '
                            'target, avail / dev / shm;false"',
                            "resources": {"cpu": 1.0, "memory_mb": 16384},
                        },
                    }
                ]
            }
        )
    ),
)
def test_list_extended_output_no_gpu(jobs):
    assert jobs.list() == [
        JobDescription(
            client=jobs,
            id="job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            status="failed",
            image="gcr.io/light-reality-205619/ubuntu:latest",
            command='bash -c " / bin / df--block - size M--output '
            '= target, avail / dev / shm;false"',
            resources=Resources(memory=16384, cpu=1.0, gpu=None, shm=None),
        )
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method="GET", json=None, url="http://127.0.0.1/jobs", params=None, data=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
            {
                "jobs": [
                    {
                        "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
                        "status": "pending",
                        "history": {
                            "status": "failed",
                            "reason": "Error",
                            "description": "Mounted on Avail\\n/dev/shm     "
                            "64M\\n\\nExit code: 1",
                            "created_at": "2018-09-25T12:28:21.298672+00:00",
                            "started_at": "2018-09-25T12:28:59.759433+00:00",
                            "finished_at": "2018-09-25T12:28:59.759433+00:00",
                        },
                        "container": {
                            "resources": {"cpu": 1.0, "memory_mb": 16384, "gpu": 1}
                        },
                    }
                ]
            }
        )
    ),
)
def test_list_extended_output_no_image(jobs):
    assert jobs.list() == [
        JobDescription(
            client=jobs,
            id="job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            status="pending",
            image=None,
            command=None,
            resources=Resources(memory=16384, cpu=1.0, gpu=1, shm=None),
        )
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method="GET", json=None, url="http://127.0.0.1/jobs", params=None, data=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(BinaryResponse(data=b"bar")),
)
def test_monitor(jobs):
    with jobs.monitor(id="1") as f:
        assert f.read() == b"bar"
        aiohttp.ClientSession.request.assert_called_with(
            method="GET",
            url="http://127.0.0.1/jobs/1/log",
            params=None,
            json=None,
            data=None,
        )
