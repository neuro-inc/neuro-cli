# Test sets defined to ensure proper payload is being sent to the server
# API calls are mocked, tests ensure that client side wrappers pass correct json
# and properly read response from server side
from typing import List
from unittest.mock import patch

import aiohttp

from neuromation.client import Image
from neuromation.client.jobs import NetworkPortForwarding, Resources
from neuromation.client.requests import VolumeDescriptionPayload
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
        method="GET", url="http://127.0.0.1/jobs/1", params=None, data=None, json=None
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
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
                        "gpu_model": "nvidia-tesla-p4",
                    },
                },
                "http_url": "http://my_host:8889",
                "ssh_server": "ssh://my_host.ssh:22",
            }
        )
    ),
)
def test_job_submit(jobs):
    image = Image(image="submit-image-name", command="submit-command")
    network = NetworkPortForwarding({"http": 8181, "ssh": 22})
    resources = Resources.create("7", "1", "test-gpu-model", "4G", "true")
    volumes: List[VolumeDescriptionPayload] = [
        VolumeDescriptionPayload(
            "storage://test-user/path_read_only", "/container/read_only", True
        ),
        VolumeDescriptionPayload(
            "storage://test-user/path_read_write", "/container/path_read_write", False
        ),
    ]
    jobs.submit(
        image=image,
        resources=resources,
        network=network,
        volumes=volumes,
        job_name="test-job-name",
    )

    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        url="http://127.0.0.1/jobs",
        params=None,
        data=None,
        json={
            "container": {
                "image": "submit-image-name",
                "command": "submit-command",
                "http": {"port": 8181},
                "ssh": {"port": 22},
                "resources": {
                    "memory_mb": "4096",
                    "cpu": 7.0,
                    "shm": True,
                    "gpu": 1,
                    "gpu_model": "test-gpu-model",
                },
                "volumes": [
                    {
                        "src_storage_uri": "storage://test-user/path_read_only",
                        "dst_path": "/container/read_only",
                        "read_only": True,
                    },
                    {
                        "src_storage_uri": "storage://test-user/path_read_write",
                        "dst_path": "/container/path_read_write",
                        "read_only": False,
                    },
                ],
            },
            "name": "test-job-name",
        },
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(
        JsonResponse(
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
                        "gpu_model": "nvidia-tesla-p4",
                    },
                },
                "http_url": "http://my_host:8889",
                "ssh_server": "ssh://my_host.ssh:22",
            }
        )
    ),
)
def test_job_submit_no_volumes(jobs):
    image = Image(image="submit-image-name", command="submit-command")
    network = NetworkPortForwarding({"http": 8181, "ssh": 22})
    resources = Resources.create("7", "1", "test-gpu-model", "4G", "true")
    volumes: List[VolumeDescriptionPayload] = None
    jobs.submit(
        image=image,
        resources=resources,
        network=network,
        volumes=volumes,
        job_name="test-job-name",
    )

    aiohttp.ClientSession.request.assert_called_with(
        method="POST",
        url="http://127.0.0.1/jobs",
        params=None,
        data=None,
        json={
            "container": {
                "image": "submit-image-name",
                "command": "submit-command",
                "http": {"port": 8181},
                "ssh": {"port": 22},
                "resources": {
                    "memory_mb": "4096",
                    "cpu": 7.0,
                    "shm": True,
                    "gpu": 1,
                    "gpu_model": "test-gpu-model",
                },
                "volumes": [],
            },
            "name": "test-job-name",
        },
    )
