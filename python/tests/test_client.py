from unittest.mock import patch

import aiohttp
from aiohttp import web

from neuromation import client
from utils import mocked_async_context_manager

TRAIN_RESPONSE = {
    'results': 'schema://host/path',
    'status': 'PENDING',
    'id': 'iddqd'
}


INFER_RESPONSE = {
    'results': 'schema://host/path',
    'status': 'PENDING',
    'id': 'iddqd'
}


JOB_RESPONSE = {
    'results': 'schema://host/path',
    'status': 'SUCCEEDED',
    'id': 'iddqd',
    'url': 'http://127.0.0.1'
}


@patch(
    'aiohttp.ClientSession.post',
    new=mocked_async_context_manager(web.json_response(TRAIN_RESPONSE)))
def test_train(request, model, loop):
    result = model.train(
        image=client.Image(image='repo/image', CMD='bash'),
        resources=client.Resources(memory='16G', cpu=1, gpu=1),
        dataset='schema://host/data',
        results='schema://host/results',
        loop=loop
    )

    aiohttp.ClientSession.post.assert_called_with(
            json={
                'resources': {'memory': '16G', 'cpu': 1, 'gpu': 1},
                'image': {'image': 'repo/image', 'CMD': 'bash'},
                'dataset_storage_uri': 'schema://host/data',
                'result_storage_uri': 'schema://host/results'},
            url='http://127.0.0.1/train')

    assert result == client.JobStatus(
        results='schema://host/path',
        status='PENDING',
        id='iddqd',
        url='http://127.0.0.1')


@patch(
    'aiohttp.ClientSession.post',
    new=mocked_async_context_manager(web.json_response(INFER_RESPONSE)))
def test_infer(request, model, loop):
    result = model.infer(
        image=client.Image(image='repo/image', CMD='bash'),
        resources=client.Resources(memory='16G', cpu=1, gpu=1),
        model='schema://host/model',
        dataset='schema://host/data',
        results='schema://host/results',
        loop=loop
    )

    aiohttp.ClientSession.post.assert_called_with(
            json={
                'image': {'image': 'repo/image', 'CMD': 'bash'},
                'dataset_storage_uri': 'schema://host/data',
                'result_storage_uri': 'schema://host/results',
                'model_storage_uri': 'schema://host/model',
                'resources': {'memory': '16G', 'cpu': 1, 'gpu': 1}},
            url='http://127.0.0.1/infer')

    assert result == client.JobStatus(
        results='schema://host/path',
        status='PENDING',
        id='iddqd',
        url='http://127.0.0.1')


@patch(
    'aiohttp.ClientSession.get',
    new=mocked_async_context_manager(web.json_response(JOB_RESPONSE)))
def test_job_status(request, model, loop):
    job = client.JobStatus(
        **{**JOB_RESPONSE, 'status': 'PENDING'})
    res = job.wait(loop=loop)
    assert res == client.JobStatus(**JOB_RESPONSE)
