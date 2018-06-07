from unittest.mock import patch

import aiohttp
from aiohttp import web

from neuromation import client
from utils import INFER_RESPONSE, TRAIN_RESPONSE, mocked_async_context_manager

JOB_RESPONSE = {
    'results': 'schema://host/path',
    'status': 'SUCCEEDED',
    'id': 'iddqd',
}


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(web.json_response(TRAIN_RESPONSE)))
def test_train(request, model, loop):
    result = model.train(
        image=client.Image(image='repo/image', command='bash'),
        resources=client.Resources(memory='16G', cpu=1, gpu=1),
        dataset='schema://host/data',
        results='schema://host/results')

    aiohttp.ClientSession.request.assert_called_with(
            method='POST',
            json={
                'resources': {'memory': '16G', 'cpu': 1, 'gpu': 1},
                'image': {'image': 'repo/image', 'command': 'bash'},
                'dataset_storage_uri': 'schema://host/data',
                'result_storage_uri': 'schema://host/results'},
            url='http://127.0.0.1/train')

    assert result == client.JobStatus(
        results='schema://host/path',
        status='PENDING',
        id='iddqd',
        url='http://127.0.0.1',
        session=result.session)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(web.json_response(INFER_RESPONSE)))
def test_infer(request, model, loop):
    result = model.infer(
        image=client.Image(image='repo/image', command='bash'),
        resources=client.Resources(memory='16G', cpu=1, gpu=1),
        model='schema://host/model',
        dataset='schema://host/data',
        results='schema://host/results'
    )

    aiohttp.ClientSession.request.assert_called_with(
            method='POST',
            json={
                'image': {'image': 'repo/image', 'command': 'bash'},
                'dataset_storage_uri': 'schema://host/data',
                'result_storage_uri': 'schema://host/results',
                'model_storage_uri': 'schema://host/model',
                'resources': {'memory': '16G', 'cpu': 1, 'gpu': 1}},
            url='http://127.0.0.1/infer')

    assert result == client.JobStatus(
        session=result.session,
        results='schema://host/path',
        status='PENDING',
        id='iddqd',
        url='http://127.0.0.1')


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(web.json_response(JOB_RESPONSE)))
def test_job_status(request, model, loop):
    job = client.JobStatus(
        url=model._url,
        **{
            **JOB_RESPONSE,
            'status': 'PENDING',
            'session': model._session
        })

    res = job.wait(loop=loop)
    assert res == client.JobStatus(
        url=model._url,
        session=model._session,
        **JOB_RESPONSE)
