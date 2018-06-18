from unittest.mock import patch

import aiohttp
import pytest
from aiohttp import web

from neuromation import client
from neuromation.client import parse_memory
from utils import (INFER_RESPONSE, TRAIN_RESPONSE, JsonResponse,
                   mocked_async_context_manager)

JOB_RESPONSE = {
    'results': 'schema://host/path',
    'status': 'SUCCEEDED',
    'id': 'iddqd',
}


def test_parse_memory():
    for value in ['1234', '   ', None, '', '-124', 'M', 'K', 'k', '123B']:
        with pytest.raises(ValueError, match=f'Unable parse value: {value}'):
            client.parse_memory(value)

    assert parse_memory('1K') == 1024
    assert parse_memory('2K') == 2048
    assert parse_memory('1kB') == 1000
    assert parse_memory('2kB') == 2000

    assert parse_memory('42M') == 42 * 1024 ** 2
    assert parse_memory('42MB') == 42 * 1000 ** 2

    assert parse_memory('42G') == 42 * 1024 ** 3
    assert parse_memory('42GB') == 42 * 1000 ** 3

    assert parse_memory('42T') == 42 * 1024 ** 4
    assert parse_memory('42TB') == 42 * 1000 ** 4

    assert parse_memory('42P') == 42 * 1024 ** 5
    assert parse_memory('42PB') == 42 * 1000 ** 5

    assert parse_memory('42E') == 42 * 1024 ** 6
    assert parse_memory('42EB') == 42 * 1000 ** 6

    assert parse_memory('42Z') == 42 * 1024 ** 7
    assert parse_memory('42ZB') == 42 * 1000 ** 7

    assert parse_memory('42Y') == 42 * 1024 ** 8
    assert parse_memory('42YB') == 42 * 1000 ** 8


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
                'resources': {'memory_mb': 16384, 'cpu': 1, 'gpu': 1},
                'image': {'image': 'repo/image', 'command': 'bash'},
                'dataset_storage_uri': 'schema://host/data',
                'result_storage_uri': 'schema://host/results'},
            url='http://127.0.0.1/train')

    assert result == client.JobStatus(
        client=model,
        status='PENDING',
        id='iddqd',
        results='schema://host/path')


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(INFER_RESPONSE)))
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
            params=None,
            data=None,
            json={
                'image': {'image': 'repo/image', 'command': 'bash'},
                'dataset_storage_uri': 'schema://host/data',
                'result_storage_uri': 'schema://host/results',
                'model_storage_uri': 'schema://host/model',
                'resources': {'memory_mb': 16384, 'cpu': 1, 'gpu': 1}},
            url='http://127.0.0.1/infer')

    assert result == client.JobStatus(
        client=model,
        results='schema://host/path',
        status='PENDING',
        id='iddqd')


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
