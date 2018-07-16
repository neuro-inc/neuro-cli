from unittest.mock import patch

import aiohttp

from neuromation.client.jobs import JobStatus
from utils import (BinaryResponse, JsonResponse, PlainResponse,
                   mocked_async_context_manager)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(PlainResponse(text='')))
def test_kill(jobs):
    assert jobs.kill('1')

    aiohttp.ClientSession.request.assert_called_with(
        method='DELETE',
        url='http://127.0.0.1/jobs/1',
        params=None,
        data=None,
        json=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        {
            'status': 'RUNNING',
            'job_id': 'foo'
        },
    )))
def test_status(jobs):
    expected = {
            'status': 'RUNNING',
            'job_id': 'foo'
    }
    res = jobs.status('1')
    assert {
            'status': res.status,
            'job_id': 'foo'
           } == expected

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        url='http://127.0.0.1/jobs/1',
        params=None,
        data=None,
        json=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse([
            {
                'status': 'RUNNING',
                'job_id': 'foo'
            },
            {
                'status': 'STARTING',
                'job_id': 'bar'
            }
        ])))
def test_list(jobs):
    assert jobs.list() == [
        JobStatus(client=jobs, job_id='foo', status='RUNNING'),
        JobStatus(client=jobs, job_id='bar', status='STARTING')
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/jobs',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(BinaryResponse(data=b'bar')))
def test_monitor(jobs):
    with jobs.monitor(id='1') as f:
        assert f.read() == b'bar'
        aiohttp.ClientSession.request.assert_called_with(
            method='GET',
            url='http://127.0.0.1/jobs/1/log',
            params=None,
            json=None,
            data=None)
