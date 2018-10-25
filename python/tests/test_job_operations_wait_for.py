from unittest.mock import MagicMock, Mock

import pytest

from neuromation.cli.command_handlers import JobHandlerOperations
from neuromation.client.jobs import Job, JobDescription


@pytest.fixture
def jobs_mock(loop):
    data = {"count": 2}

    def jobs_(id) -> JobDescription:
        if data["count"]:
            data["count"] = data["count"] - 1
            return JobDescription(
                status="pending", id=id, client=None, image="ubuntu", command="shell"
            )
        else:
            return JobDescription(
                status="running", id=id, client=None, image="ubuntu", command="shell"
            )

    mock = MagicMock(Job(url="no-url", token="notoken", loop=loop))
    mock.__enter__ = Mock(return_value=mock)
    mock.__exit__ = Mock(return_value=False)
    mock.status = jobs_

    def mock_():
        return mock

    return mock_


def test_job_status_query(jobs_mock):
    jobs = JobHandlerOperations().wait_job_transfer_from("id0", "pending", jobs_mock)
    assert jobs == JobDescription(
        status="running", id="id0", client=None, image="ubuntu", command="shell"
    )
