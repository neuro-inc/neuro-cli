import pytest

from neuromation.cli.command_handlers import JobHandlerOperations
from neuromation.client.jobs import Job, JobDescription
from tests.conftest import AsyncContextManagerMock


@pytest.fixture
def jobs_mock_wait(loop):
    data = {"count": 2}

    async def jobs_(id) -> JobDescription:
        if data["count"]:
            data["count"] = data["count"] - 1
            return JobDescription(
                status="pending", id=id, client=None, image="ubuntu", command="shell"
            )
        else:
            return JobDescription(
                status="running", id=id, client=None, image="ubuntu", command="shell"
            )

    mock = AsyncContextManagerMock(Job(url="no-url", token="notoken", loop=loop))
    mock.status = jobs_

    def mock_():
        return mock

    return mock_


@pytest.mark.asyncio
async def test_job_status_query(jobs_mock_wait):
    jobs = await JobHandlerOperations("test-user").wait_job_transfer_from(
        "id0", "pending", jobs_mock_wait
    )
    assert jobs == JobDescription(
        status="running", id="id0", client=None, image="ubuntu", command="shell"
    )
