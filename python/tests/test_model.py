import asyncio
from dataclasses import replace
from unittest.mock import patch

import pytest
from aiohttp import web

from neuromation import JobItem, Resources
from neuromation.client import Image
from utils import TRAIN_RESPONSE, JsonResponse, mocked_async_context_manager


JOB_ARGS = {
    "resources": Resources(
        memory="64M", cpu=1, gpu=1, shm=False, gpu_model="nvidia-tesla-v100"
    ),
    "image": Image(image="test/image", command="bash"),
    "dataset": "storage://~/dataset",
    "results": "storage://~/results",
    "network": None,
    "is_preemptible": True,
    "description": "test job description",
}

JOB_TIMEOUT_SEC = 0.005


def train_or_infer_value_errors(func, args):
    with pytest.raises(TypeError):
        func()

    with pytest.raises(ValueError, match=r"Invalid image path: .*"):
        func(**{**args, "image": Image(image="invalid  image path", command="bash")})

    with pytest.raises(ValueError, match=r"Invalid resource request: .*"):
        func(**{**args, "resources": None})

    with pytest.raises(ValueError, match=r"Invalid resource request: .*"):
        func(**{**args, "resources": Resources(memory="foo", cpu=1, gpu=1)})

    with pytest.raises(ValueError, match=r"Invalid resource request: .*"):
        func(**{**args, "resources": Resources(memory="64M", cpu=-1, gpu=1)})

    with pytest.raises(ValueError, match=r"Invalid resource request: .*"):
        func(**{**args, "resources": Resources(memory="64M", cpu=1, gpu=-1)})

    with pytest.raises(ValueError, match=r"Invalid uri: .*"):
        func(**{**args, "dataset": "bad-uri"})

    with pytest.raises(ValueError, match=r"Invalid uri: .*"):
        func(**{**args, "results": "bad-uri"})


async def _call(self):
    await asyncio.sleep(0.006)
    return self


@pytest.mark.parametrize(
    "job,cmd,model_uri",
    [
        ("train", 'bash -c "echo foo"', None),
        ("train", ["bash", "-c", "echo foo"], None),
    ],
)
@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)),
)
@patch("neuromation.client.JobItem._call", _call)
def test_job(job, cmd, model_uri, model, loop):
    args = JOB_ARGS if model_uri is None else {**JOB_ARGS, "model": model_uri}

    func = getattr(model, job)
    job_status = func(**args)
    assert job_status == JobItem(
        status="PENDING",
        id=job_status.id,
        client=model,
        description="test job description",
    ), str(job_status)

    with pytest.raises(TimeoutError):
        job_status.wait(timeout=JOB_TIMEOUT_SEC)

    status = job_status.wait()

    assert replace(status, id=None) == JobItem(
        status="PENDING", id=None, client=model, description="test job description"
    )


@patch(
    "aiohttp.ClientSession.request",
    new=mocked_async_context_manager(web.json_response(TRAIN_RESPONSE)),
)
def test_train_errors(request, model):
    pass
    # TODO (artyom, 06/07/2018): implement input validation and uncomment tests
    # train_or_infer_value_errors(model.train, JOB_ARGS)
