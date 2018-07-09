from unittest.mock import patch

import aiohttp

from neuromation import client
from utils import (INFER_RESPONSE, TRAIN_RESPONSE, JsonResponse,
                   mocked_async_context_manager)

JOB_RESPONSE = {
    'status': 'SUCCEEDED',
    'job_id': 'iddqd',
}


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(TRAIN_RESPONSE)))
def test_train(request, model, loop):
    result = model.train(
        image=client.Image(image='repo/image', command='bash'),
        resources=client.Resources(memory='16G', cpu=1, gpu=1),
        dataset='schema://host/data',
        results='schema://host/results')

    aiohttp.ClientSession.request.assert_called_with(
            method='POST',
            data=None,
            params=None,
            json={
                'container': {
                    'image': 'repo/image',
                    'command': 'bash',
                    'resources': {'memory_mb': 16384, 'cpu': 1.0, 'gpu': 1.0},
                },
                'dataset_storage_uri': 'schema://host/data',
                'result_storage_uri': 'schema://host/results'},
            url='http://127.0.0.1/models')

    assert result == client.JobStatus(
        client=model,
        status='PENDING',
        job_id='iddqd')


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(INFER_RESPONSE)))
def test_infer(request, model, loop):
    result = model.infer(
        image=client.Image(image='repo/image', command='bash'),
        resources=client.Resources(memory='16G', cpu=1.0, gpu=1.0),
        model='schema://host/model',
        dataset='schema://host/data',
        results='schema://host/results'
    )

    aiohttp.ClientSession.request.assert_called_with(
            method='POST',
            params=None,
            data=None,
            json={
                'container': {
                    'image': 'repo/image',
                    'command': 'bash',
                    'resources': {'memory_mb': 16384, 'cpu': 1.0, 'gpu': 1.0}},
                'dataset_storage_uri': 'schema://host/data',
                'result_storage_uri': 'schema://host/results',
                'model_storage_uri': 'schema://host/model'},
            url='http://127.0.0.1/models')

    assert result == client.JobStatus(
        client=model,
        status='PENDING',
        job_id='iddqd')


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(JOB_RESPONSE)))
def test_job_status(request, model, loop):
    job = client.JobStatus(
        client=model,
        **{
            **JOB_RESPONSE,
            'status': 'PENDING',
        })

    res = job.wait()
    assert res == client.JobStatus(client=model, **JOB_RESPONSE)
