from unittest.mock import patch

import aiohttp
import pytest

from neuromation.cli.command_handlers import JobHandlerOperations
from neuromation.client import ClientError, ResourceNotFound
from neuromation.client.jobs import JobDescription, Resources
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
        JobDescription(client=jobs, id='foo', status='RUNNING'),
        JobDescription(client=jobs, id='bar', status='STARTING')
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/jobs',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({
        'jobs': [{
            "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            "status": "failed",
            "history": {
                "status": "failed",
                "reason": "Error",
                "description": "Mounted on Avail\\n/dev/shm     "
                               "64M\\n\\nExit code: 1",
                "created_at": "2018-09-25T12:28:21.298672+00:00",
                "started_at": "2018-09-25T12:28:59.759433+00:00",
                "finished_at": "2018-09-25T12:28:59.759433+00:00"
            },
            "container": {
                "image": "gcr.io/light-reality-205619/ubuntu:latest",
                "command": "bash -c \" / bin / df--block - size M--output "
                           "= target, avail / dev / shm;false\"",
                "resources": {
                    "cpu": 1.0,
                    "memory_mb": 16384,
                    "gpu": 1,
                    "shm": False
                }
            }
        }]
    })))
def test_list_extended_output(jobs):
    assert jobs.list() == [
        JobDescription(client=jobs,
                       id='job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f',
                       status='failed',
                       image="gcr.io/light-reality-205619/ubuntu:latest",
                       command="bash -c \" / bin / df--block - size M--output"
                               " = target, avail / dev / shm;false\"",
                       resources=Resources(
                           memory=16384,
                           cpu=1.0,
                           gpu=1,
                           shm=False
                       )),
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/jobs',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({
        'jobs': [{
            "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            "status": "failed",
            "history": {
                "status": "failed",
                "reason": "Error",
                "description": "Mounted on Avail\\n/dev/shm"
                               "     64M\\n\\nExit code: 1",
                "created_at": "2018-09-25T12:28:21.298672+00:00",
                "started_at": "2018-09-25T12:28:59.759433+00:00",
                "finished_at": "2018-09-25T12:28:59.759433+00:00"
            },
            "container": {
                "image": "gcr.io/light-reality-205619/ubuntu:latest",
                "command": "bash -c \" / bin / df--block - size M--output = "
                           "target, avail / dev / shm;false\"",
                "resources": {
                    "cpu": 1.0,
                    "memory_mb": 16384,
                    "gpu": 1
                }
            }
        }]
    })))
def test_list_extended_output_no_shm(jobs):
    assert jobs.list() == [
        JobDescription(client=jobs,
                       id='job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f',
                       status='failed',
                       image="gcr.io/light-reality-205619/ubuntu:latest",
                       command="bash -c \" / bin / df--block - size M--output "
                               "= target, avail / dev / shm;false\"",
                       resources=Resources(
                           memory=16384,
                           cpu=1.0,
                           gpu=1,
                           shm=None
                       )),
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/jobs',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({
        'jobs': [{
            "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            "status": "failed",
            "history": {
                "status": "failed",
                "reason": "Error",
                "description": "Mounted on Avail\\n/dev/shm"
                               "     64M\\n\\nExit code: 1",
                "created_at": "2018-09-25T12:28:21.298672+00:00",
                "started_at": "2018-09-25T12:28:59.759433+00:00",
                "finished_at": "2018-09-25T12:28:59.759433+00:00"
            },
            "container": {
                "image": "gcr.io/light-reality-205619/ubuntu:latest",
                "command": "bash -c \" / bin / df--block - size M--output = "
                           "target, avail / dev / shm;false\"",
                "resources": {
                    "cpu": 1.0,
                    "memory_mb": 16384,
                }
            }
        }]
    })))
def test_list_extended_output_no_gpu(jobs):
    assert jobs.list() == [
        JobDescription(client=jobs,
                       id='job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f',
                       status='failed',
                       image="gcr.io/light-reality-205619/ubuntu:latest",
                       command="bash -c \" / bin / df--block - size M--output "
                               "= target, avail / dev / shm;false\"",
                       resources=Resources(
                           memory=16384,
                           cpu=1.0,
                           gpu=None,
                           shm=None
                       )),
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/jobs',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse({
        'jobs': [{
            "id": "job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f",
            "status": "pending",
            "history": {
                "status": "failed",
                "reason": "Error",
                "description": "Mounted on Avail\\n/dev/shm     "
                               "64M\\n\\nExit code: 1",
                "created_at": "2018-09-25T12:28:21.298672+00:00",
                "started_at": "2018-09-25T12:28:59.759433+00:00",
                "finished_at": "2018-09-25T12:28:59.759433+00:00"
            },
            "container": {
                "resources": {
                    "cpu": 1.0,
                    "memory_mb": 16384,
                    "gpu": 1
                }
            }
        }]
    })))
def test_list_extended_output_no_image(jobs):
    assert jobs.list() == [
        JobDescription(client=jobs,
                       id='job-cf519ed3-9ea5-48f6-a8c5-492b810eb56f',
                       status='pending',
                       image=None,
                       command=None,
                       resources=Resources(
                           memory=16384,
                           cpu=1.0,
                           gpu=1,
                           shm=None
                       )),
    ]
    aiohttp.ClientSession.request.assert_called_with(
        method='GET',
        json=None,
        url='http://127.0.0.1/jobs',
        params=None,
        data=None)


@patch(
    'aiohttp.ClientSession.request',
    new=mocked_async_context_manager(JsonResponse(
        {"jobs": [
            {"id": "job-002075cd-ebd4-4614-b58a-42e7514405ef", "owner": "truskovskiyk",
             "status": "succeeded",
             "history": {"status": "succeeded", "reason": None, "description": None,
                         "created_at": "2018-10-11T10:00:50.970695+00:00",
                         "started_at": "2018-10-11T10:00:55.225978+00:00",
                         "finished_at": "2018-10-11T10:27:30.571684+00:00"},
             "container": {
                 "image": "registry.staging.neuromation.io/truskovskiyk/inclusiveimages:latest",
                 "env": {"NP_DATASET_PATH": "/var/storage/home",
                         "NP_RESULT_PATH": "/var/storage/home/inclusiveimages/dataset"},
                 "volumes": [{"src_storage_uri": "storage://home",
                              "dst_path": "/var/storage/home", "read_only": True}, {
                                 "src_storage_uri": "storage://home/inclusiveimages/dataset",
                                 "dst_path": "/var/storage/home/inclusiveimages/dataset",
                                 "read_only": False}],
                 "command": "python experiments/dataset_to_hdf5.py --config_path ./configs/platform/dataset_to_hdf5_64x64.json",
                 "resources": {"cpu": 1.0, "memory_mb": 4096, "gpu": 0, "shm": True}}},
            {"id": "job-468f2ad6-b325-4068-9a9c-696bc068e698", "owner": "truskovskiyk",
             "status": "running",
             "history": {"status": "running", "reason": None, "description": None,
                         "created_at": "2018-10-11T10:45:27.675309+00:00",
                         "started_at": "2018-10-11T10:46:57.639120+00:00"},
             "container": {
                 "image": "registry.staging.neuromation.io/truskovskiyk/inclusiveimages:latest",
                 "env": {"NP_DATASET_PATH": "/var/storage/home",
                         "NP_RESULT_PATH": "/var/storage/home/inclusiveimages/dataset"},
                 "volumes": [{"src_storage_uri": "storage://home",
                              "dst_path": "/var/storage/home", "read_only": True}, {
                                 "src_storage_uri": "storage://home/inclusiveimages/dataset",
                                 "dst_path": "/var/storage/home/inclusiveimages/dataset",
                                 "read_only": False}],
                 "command": "python experiments/dataset_to_hdf5.py --config_path ./configs/platform/dataset_to_hdf5_64x64.json",
                 "resources": {"cpu": 1.0, "memory_mb": 4096, "gpu": 0, "shm": True}}},
            {"id": "job-5c7106ab-96e6-44a2-ab2f-6a3c27adc491", "owner": "truskovskiyk",
             "status": "succeeded",
             "history": {"status": "succeeded", "reason": None, "description": None,
                         "created_at": "2018-10-11T09:51:28.096341+00:00",
                         "started_at": "2018-10-11T09:51:31.878803+00:00",
                         "finished_at": "2018-10-11T09:58:34.654577+00:00"},
             "container": {
                 "image": "registry.staging.neuromation.io/truskovskiyk/inclusiveimages:latest",
                 "env": {"NP_DATASET_PATH": "/var/storage/home",
                         "NP_RESULT_PATH": "/var/storage/home/inclusiveimages/dataset"},
                 "volumes": [{"src_storage_uri": "storage://home",
                              "dst_path": "/var/storage/home", "read_only": True}, {
                                 "src_storage_uri": "storage://home/inclusiveimages/dataset",
                                 "dst_path": "/var/storage/home/inclusiveimages/dataset",
                                 "read_only": False}],
                 "command": "python experiments/dataset_to_hdf5.py --config_path ./configs/platform/dataset_to_hdf5_64x64.json",
                 "resources": {"cpu": 1.0, "memory_mb": 4096, "gpu": 0, "shm": True}}},
            {"id": "job-0c5e0cb3-1c41-4029-8a10-4a85565a898f", "owner": "truskovskiyk",
             "status": "running",
             "history": {"status": "running", "reason": None, "description": None,
                         "created_at": "2018-10-11T10:48:25.666636+00:00",
                         "started_at": "2018-10-11T10:48:31.716838+00:00"},
             "container": {
                 "image": "registry.staging.neuromation.io/truskovskiyk/inclusiveimages:latest",
                 "env": {"NP_DATASET_PATH": "/var/storage/home",
                         "NP_RESULT_PATH": "/var/storage/home/inclusiveimages/dataset"},
                 "volumes": [{"src_storage_uri": "storage://home",
                              "dst_path": "/var/storage/home", "read_only": True}, {
                                 "src_storage_uri": "storage://home/inclusiveimages/dataset",
                                 "dst_path": "/var/storage/home/inclusiveimages/dataset",
                                 "read_only": False}],
                 "command": "python experiments/dataset_to_hdf5.py --config_path ./configs/platform/dataset_to_hdf5_224x224.json",
                 "resources": {"cpu": 1.0, "memory_mb": 4096, "gpu": 0, "shm": True}}},
            {"id": "job-d29f17ef-85c8-4464-8cab-1a9b90885182", "owner": "truskovskiyk",
             "status": "running",
             "history": {"status": "running", "reason": None, "description": None,
                         "created_at": "2018-10-11T10:46:30.526070+00:00",
                         "started_at": "2018-10-11T10:49:14.524621+00:00"},
             "container": {
                 "image": "registry.staging.neuromation.io/truskovskiyk/inclusiveimages:latest",
                 "env": {"NP_DATASET_PATH": "/var/storage/home",
                         "NP_RESULT_PATH": "/var/storage/home/inclusiveimages/dataset"},
                 "volumes": [{"src_storage_uri": "storage://home",
                              "dst_path": "/var/storage/home", "read_only": True}, {
                                 "src_storage_uri": "storage://home/inclusiveimages/dataset",
                                 "dst_path": "/var/storage/home/inclusiveimages/dataset",
                                 "read_only": False}],
                 "command": "python experiments/dataset_to_hdf5.py --config_path ./configs/platform/dataset_to_hdf5_128x128.json",
                 "resources": {"cpu": 1.0, "memory_mb": 4096, "gpu": 0, "shm": True}}},
            {"id": "job-34061a95-1321-4ce9-ab92-84239f196d19", "owner": "truskovskiyk",
             "status": "succeeded",
             "history": {"status": "succeeded", "reason": None, "description": None,
                         "created_at": "2018-10-11T09:26:15.474808+00:00",
                         "started_at": "2018-10-11T09:31:07.720672+00:00",
                         "finished_at": "2018-10-11T09:34:20.852620+00:00"},
             "container": {
                 "image": "registry.staging.neuromation.io/truskovskiyk/inclusiveimages:latest",
                 "env": {"NP_DATASET_PATH": "/var/storage/home",
                         "NP_RESULT_PATH": "/var/storage/home/inclusiveimages/dataset"},
                 "volumes": [{"src_storage_uri": "storage://home",
                              "dst_path": "/var/storage/home", "read_only": True}, {
                                 "src_storage_uri": "storage://home/inclusiveimages/dataset",
                                 "dst_path": "/var/storage/home/inclusiveimages/dataset",
                                 "read_only": False}],
                 "command": "python experiments/dataset_to_hdf5.py --config_path ./configs/platform/dataset_to_hdf5_64x64.json",
                 "resources": {"cpu": 1.0, "memory_mb": 4096, "gpu": 0, "shm": True}}},
            {"id": "job-f22ead34-45fc-4b7b-a1d1-3b6775548793", "owner": "truskovskiyk",
             "status": "succeeded",
             "history": {"status": "succeeded", "reason": None, "description": None,
                         "created_at": "2018-10-11T09:41:39.645896+00:00",
                         "started_at": "2018-10-11T09:44:06.836913+00:00",
                         "finished_at": "2018-10-11T09:47:18.013986+00:00"},
             "container": {
                 "image": "registry.staging.neuromation.io/truskovskiyk/inclusiveimages:latest",
                 "env": {"NP_DATASET_PATH": "/var/storage/home",
                         "NP_RESULT_PATH": "/var/storage/home/inclusiveimages/dataset"},
                 "volumes": [{"src_storage_uri": "storage://home",
                              "dst_path": "/var/storage/home", "read_only": True}, {
                                 "src_storage_uri": "storage://home/inclusiveimages/dataset",
                                 "dst_path": "/var/storage/home/inclusiveimages/dataset",
                                 "read_only": False}],
                 "command": "python experiments/dataset_to_hdf5.py --config_path ./configs/platform/dataset_to_hdf5_64x64.json",
                 "resources": {"cpu": 1.0, "memory_mb": 4096, "gpu": 0, "shm": True}}}]})))
def test_list_extended_output_no_image_v2(jobs):
    def jobs_():
        return jobs
    jobs = JobHandlerOperations().list_jobs(None, jobs_)
    assert jobs


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
