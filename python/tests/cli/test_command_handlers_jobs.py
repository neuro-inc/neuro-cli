# unit tests ensure that handlers properly pass details to the underlying client
# layer code
import pytest

from neuromation.cli.command_handlers import JobHandlerOperations
from neuromation.client import Image
from neuromation.client.jobs import NetworkPortForwarding, Resources
from neuromation.client.requests import VolumeDescriptionPayload


class TestJobSubmit:
    @pytest.mark.parametrize(
        "volumes",
        [("storage:///"), (":"), ("::::"), (""), ("storage:///data/:/data/rest:wrong")],
    )
    def test_failed_volume(self, partial_mocked_job, volumes) -> None:
        with pytest.raises(ValueError):
            job = JobHandlerOperations("alice")
            job.submit(
                "test-image",
                "1",
                "test-gpu",
                "1.2",
                "1G",
                "False",
                ["test-command"],
                "8183",
                "25",
                [volumes],
                partial_mocked_job,
            )

        assert partial_mocked_job().submit.call_count == 0

    def test_job_submit_happy_path(self, partial_mocked_job) -> None:
        job = JobHandlerOperations("alice")
        job.submit(
            "test-image",
            "1",
            "test-gpu",
            "1.2",
            "1G",
            "False",
            ["test-command"],
            "8183",
            "25",
            [
                "storage://bob/data:/cob/data:ro",
                "storage://bob/data0:/cob/data0",
                "storage://bob/data1:/cob/data1:rw",
            ],
            partial_mocked_job,
        )

        partial_mocked_job().submit.assert_called_once()

        partial_mocked_job().submit.assert_called_with(
            image=Image(image="test-image", command="test-command"),
            network=NetworkPortForwarding({"http": 8183, "ssh": 25}),
            resources=Resources.create("1.2", "1", "test-gpu", "1G", "False"),
            volumes=[
                VolumeDescriptionPayload(
                    storage_path="storage://bob/data",
                    container_path="/cob/data",
                    read_only=True,
                ),
                VolumeDescriptionPayload(
                    storage_path="storage://bob/data0",
                    container_path="/cob/data0",
                    read_only=False,
                ),
                VolumeDescriptionPayload(
                    storage_path="storage://bob/data1",
                    container_path="/cob/data1",
                    read_only=False,
                ),
            ],
            job_name=None,
        )

    def test_job_submit_no_volumes(self, partial_mocked_job) -> None:
        job = JobHandlerOperations("alice")
        job.submit(
            "test-image",
            "1",
            "test-gpu",
            "1.2",
            "1G",
            "False",
            ["test-command"],
            "8183",
            "25",
            [],
            partial_mocked_job,
        )

        partial_mocked_job().submit.assert_called_once()

        partial_mocked_job().submit.assert_called_with(
            image=Image(image="test-image", command="test-command"),
            network=NetworkPortForwarding({"http": 8183, "ssh": 25}),
            resources=Resources.create("1.2", "1", "test-gpu", "1G", "False"),
            volumes=None,
            job_name=None,
        )
