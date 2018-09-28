from unittest.mock import patch

import aiohttp
import pytest

from neuromation.client import ClientError, ResourceNotFound
from neuromation.client.jobs import JobItem
from utils import (BinaryResponse, JsonResponse, PlainResponse,
                   mocked_async_context_manager)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        {'error': 'blah!'},
        error=aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=404,
            message='ah!')
    )))
def test_jobnotfound_error(jobs):
    with pytest.raises(ResourceNotFound):
        jobs.kill('blah')


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        {'error': 'blah!'},
        error=aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=405,
            message='ah!')
    )))
def test_kill_already_killed_job_error(jobs):
    with pytest.raises(ClientError):
        jobs.kill('blah')


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        {'error': 'blah!'},
        error=aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=404,
            message='ah!')
    )))
def test_monitor_notexistent_job(jobs):
    with pytest.raises(ResourceNotFound):
        with jobs.monitor('blah') as stream:
            stream.read()


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
            'status': 'running',
            'id': 'foo',
            'history': {
                'created_at': '2018-08-29T12:23:13.981621+00:00',
                'started_at': '2018-08-29T12:23:15.988054+00:00'
            }
        },
    )))
def test_status_runing(jobs):
    expected = {
            'status': 'running',
            'id': 'foo',
            'history': {
                'created_at': '2018-08-29T12:23:13.981621+00:00',
                'started_at': '2018-08-29T12:23:15.988054+00:00'
            }
    }
    res = jobs.status('1')
    assert {
            'status': res.status,
            'id': 'foo',
            'history': {
                'created_at': res.history.created_at,
                'started_at': res.history.started_at,
            }
           } == expected

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        url='http://127.0.0.1/jobs/1',
        params=None,
        data=None,
        json=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        {
            'status': 'failed',
            'id': 'foo',
            'history': {
                'created_at': '2018-08-29T12:23:13.981621+00:00',
                'started_at': '2018-08-29T12:23:15.988054+00:00',
                'finished_at': '2018-08-29T12:59:31.427795+00:00',
                'reason': 'ContainerCannotRun',
                'description': 'Not enough coffee'
            }
        },
    )))
def test_status_failed(jobs):
    expected = {
            'status': 'failed',
            'id': 'foo',
            'history': {
                'created_at': '2018-08-29T12:23:13.981621+00:00',
                'started_at': '2018-08-29T12:23:15.988054+00:00',
                'finished_at': '2018-08-29T12:59:31.427795+00:00',
                'reason': 'ContainerCannotRun',
                'description': 'Not enough coffee'
            }
    }
    res = jobs.status('1')
    assert {
            'status': res.status,
            'id': 'foo',
            'history': {
                'created_at': res.history.created_at,
                'started_at': res.history.started_at,
                'finished_at': res.history.finished_at,
                'reason': res.history.reason,
                'description': res.history.description,

            }
           } == expected

    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        url='http://127.0.0.1/jobs/1',
        params=None,
        data=None,
        json=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({
        'jobs': [{
                    'status': 'RUNNING',
                    'id': 'foo'
                },
                {
                    'status': 'STARTING',
                    'id': 'bar'
                }]
            })))
def test_list(jobs):
    assert jobs.list() == [
        JobItem(client=jobs, id='foo', status='RUNNING'),
        JobItem(client=jobs, id='bar', status='STARTING')
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
