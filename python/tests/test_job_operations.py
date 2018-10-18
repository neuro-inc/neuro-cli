from typing import List
from unittest.mock import MagicMock, Mock

import pytest

from neuromation.cli.command_handlers import JobHandlerOperations
from neuromation.client.jobs import Job, JobDescription


@pytest.fixture
def jobs_mock(loop):
    def jobs_() -> List[JobDescription]:
        jobs = [
            JobDescription(status='running',
                           id='id0',
                           client=None,
                           image='ubuntu',
                           command='shell')
        ]
        return jobs

    def jobs_status(id) -> JobDescription:
        return JobDescription(status='running',
                              id=id,
                              client=None,
                              image='ubuntu',
                              command='shell')

    mock = MagicMock(Job(url='no-url', token='notoken', loop=loop))
    mock.__enter__ = Mock(return_value=mock)
    mock.__exit__ = Mock(return_value=False)
    mock.list = jobs_
    mock.status = jobs_status

    def mock_():
        return mock
    return mock_


def test_job_filter_all(jobs_mock):
    jobs = JobHandlerOperations().list_jobs(None, jobs_mock)
    assert jobs


def test_job_filter_running(jobs_mock):
    jobs = JobHandlerOperations().list_jobs('running', jobs_mock)
    assert jobs


def test_job_filter_failed(jobs_mock):
    jobs = JobHandlerOperations().list_jobs('failed', jobs_mock)
    assert not jobs


def test_job_status_query(jobs_mock):
    jobs = JobHandlerOperations().status('id0', jobs_mock)
    assert jobs == JobDescription(status='running',
                                  id='id0',
                                  client=None,
                                  image='ubuntu',
                                  command='shell')
