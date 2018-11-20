from unittest import mock
from unittest.mock import patch

import aiohttp
import pytest

from neuromation import client
from neuromation.client.jobs import NetworkPortForwarding
from utils import (
    INFER_RESPONSE,
    TRAIN_RESPONSE,
    JsonResponse,
    mocked_async_context_manager,
)


JOB_RESPONSE = {"status": "SUCCEEDED", "id": "iddqd"}


@pytest.mark.asyncio
async def test_train_with_no_gpu(request, model, loop):
    with patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.train(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G", cpu=1.0, gpu=None, shm=None, gpu_model=None
                ),
                dataset="schema://host/data",
                results="schema://host/results",
                network=None,
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            data=None,
            params=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "resources": {"memory_mb": "16384", "cpu": 1.0, "shm": None},
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_train(request, model, loop):
    with patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.train(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G", cpu=1, gpu=1, shm=True, gpu_model="nvidia-tesla-p4"
                ),
                dataset="schema://host/data",
                results="schema://host/results",
                network=None,
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            data=None,
            params=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "resources": {
                        "memory_mb": "16384",
                        "cpu": 1.0,
                        "gpu": 1.0,
                        "gpu_model": "nvidia-tesla-p4",
                        "shm": True,
                    },
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_train_zero_gpu(request, model, loop):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.train(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G", cpu=1, gpu=0, shm=True, gpu_model="nvidia-tesla-p4"
                ),
                dataset="schema://host/data",
                results="schema://host/results",
                network=None,
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            data=None,
            params=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "resources": {"memory_mb": "16384", "cpu": 1.0, "shm": True},
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_train_with_http(request, model, loop):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.train(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G", cpu=1, gpu=1, shm=True, gpu_model="nvidia-tesla-k80"
                ),
                dataset="schema://host/data",
                results="schema://host/results",
                network=NetworkPortForwarding({"http": 7878}),
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            data=None,
            params=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "http": {"port": 7878},
                    "resources": {
                        "memory_mb": "16384",
                        "cpu": 1.0,
                        "gpu": 1.0,
                        "gpu_model": "nvidia-tesla-k80",
                        "shm": True,
                    },
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_train_with_ssh(request, model, loop):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.train(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G", cpu=1, gpu=1, shm=True, gpu_model="nvidia-tesla-v100"
                ),
                dataset="schema://host/data",
                results="schema://host/results",
                network=NetworkPortForwarding({"ssh": 7878}),
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            data=None,
            params=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "ssh": {"port": 7878},
                    "resources": {
                        "memory_mb": "16384",
                        "cpu": 1.0,
                        "gpu": 1.0,
                        "gpu_model": "nvidia-tesla-v100",
                        "shm": True,
                    },
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_train_with_ssh_and_http(request, model, loop):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.train(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G", cpu=1, gpu=1, shm=True, gpu_model="nvidia-tesla-p4"
                ),
                dataset="schema://host/data",
                results="schema://host/results",
                network=NetworkPortForwarding({"ssh": 7878, "http": 8787}),
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            data=None,
            params=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "ssh": {"port": 7878},
                    "http": {"port": 8787},
                    "resources": {
                        "memory_mb": "16384",
                        "cpu": 1.0,
                        "gpu": 1.0,
                        "gpu_model": "nvidia-tesla-p4",
                        "shm": True,
                    },
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        exp = client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )
        assert result == exp, "\n" + str(result) + "\n" + str(exp)


@pytest.mark.asyncio
async def test_train_with_ssh_and_http_no_name(request, model, loop):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.train(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G", cpu=1, gpu=1, shm=True, gpu_model="nvidia-tesla-p4"
                ),
                dataset="schema://host/data",
                results="schema://host/results",
                network=NetworkPortForwarding({"ssh": 7878, "http": 8787}),
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            data=None,
            params=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "ssh": {"port": 7878},
                    "http": {"port": 8787},
                    "resources": {
                        "memory_mb": "16384",
                        "cpu": 1.0,
                        "gpu": 1.0,
                        "gpu_model": "nvidia-tesla-p4",
                        "shm": True,
                    },
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_train_empty_command(request, model, loop):
    with patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.train(
                image=client.Image(image="repo/image", command=None),
                resources=client.Resources(
                    memory="16G", cpu=1, gpu=1, shm=True, gpu_model="nvidia-tesla-p4"
                ),
                dataset="schema://host/data",
                results="schema://host/results",
                network=NetworkPortForwarding({"ssh": 7878, "http": 8787}),
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            data=None,
            params=None,
            json={
                "container": {
                    "image": "repo/image",
                    "ssh": {"port": 7878},
                    "http": {"port": 8787},
                    "resources": {
                        "memory_mb": "16384",
                        "cpu": 1.0,
                        "gpu": 1.0,
                        "gpu_model": "nvidia-tesla-p4",
                        "shm": True,
                    },
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_infer(request, model, loop):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(INFER_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.infer(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G",
                    cpu=1.0,
                    gpu=1.0,
                    shm=False,
                    gpu_model="nvidia-tesla-k80",
                ),
                model="schema://host/model",
                dataset="schema://host/data",
                results="schema://host/results",
                network=None,
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            params=None,
            data=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "resources": {
                        "memory_mb": "16384",
                        "cpu": 1.0,
                        "gpu": 1.0,
                        "gpu_model": "nvidia-tesla-k80",
                        "shm": False,
                    },
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "model_storage_uri": "schema://host/model",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_infer_with_name(request, model, loop):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(INFER_RESPONSE)),
    ) as my_mock:
        async with model as m:
            result = await m.infer(
                image=client.Image(image="repo/image", command="bash"),
                resources=client.Resources(
                    memory="16G",
                    cpu=1.0,
                    gpu=1.0,
                    shm=False,
                    gpu_model="nvidia-tesla-k80",
                ),
                model="schema://host/model",
                dataset="schema://host/data",
                results="schema://host/results",
                network=None,
                description="job description",
            )

        my_mock.assert_called_with(
            method="POST",
            params=None,
            data=None,
            json={
                "container": {
                    "image": "repo/image",
                    "command": "bash",
                    "resources": {
                        "memory_mb": "16384",
                        "cpu": 1.0,
                        "gpu": 1.0,
                        "gpu_model": "nvidia-tesla-k80",
                        "shm": False,
                    },
                },
                "dataset_storage_uri": "schema://host/data",
                "result_storage_uri": "schema://host/results",
                "model_storage_uri": "schema://host/model",
                "description": "job description",
            },
            url="http://127.0.0.1/models",
        )

        assert result == client.JobItem(
            client=model, status="PENDING", id="iddqd", description="job description"
        )


@pytest.mark.asyncio
async def test_job_status(request, model, loop):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(JsonResponse(JOB_RESPONSE)),
    ):
        async with model as m:
            job = client.JobItem(client=m, **{**JOB_RESPONSE, "status": "PENDING"})
            res = await job.wait()
        assert res == client.JobItem(client=model, **JOB_RESPONSE)


@pytest.mark.asyncio
async def test_network_error_is_not_intercepted(storage):
    with mock.patch(
        "aiohttp.ClientSession.request",
        new=mocked_async_context_manager(
            JsonResponse({"error": "blah!"}, error=aiohttp.ClientConnectionError())
        ),
    ):
        with pytest.raises(aiohttp.ClientError):
            async with storage as s:
                await s.ls(path="blah")
