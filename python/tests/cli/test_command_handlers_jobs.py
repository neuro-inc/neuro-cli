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
                image="test-image",
                gpu="1",
                gpu_model="test-gpu",
                cpu="1.2",
                memory="1G",
                extshm="False",
                cmd=["test-command"],
                http="8183",
                ssh="25",
                volumes=[volumes],
                jobs=partial_mocked_job,
                is_preemptible=False,
                description="job description",
                env=None,
            )

        assert partial_mocked_job().submit.call_count == 0

    def test_job_submit_happy_path(self, partial_mocked_job) -> None:
        job = JobHandlerOperations("alice")
        job.submit(
            image="test-image",
            gpu="1",
            gpu_model="test-gpu",
            cpu="1.2",
            memory="1G",
            extshm="False",
            cmd=["test-command"],
            http="8183",
            ssh="25",
            volumes=[
                "storage://bob/data:/cob/data:ro",
                "storage://bob/data0:/cob/data0",
                "storage://bob/data1:/cob/data1:rw",
            ],
            jobs=partial_mocked_job,
            is_preemptible=False,
            description="job description",
            env={"var": "val"},
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
            is_preemptible=False,
            description="job description",
            env={"var": "val"},
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
            {"variable": "value"},
            partial_mocked_job,
            is_preemptible=False,
            description="job description",
        )

        partial_mocked_job().submit.assert_called_once()

        partial_mocked_job().submit.assert_called_with(
            image=Image(image="test-image", command="test-command"),
            network=NetworkPortForwarding({"http": 8183, "ssh": 25}),
            resources=Resources.create("1.2", "1", "test-gpu", "1G", "False"),
            volumes=None,
            is_preemptible=False,
            description="job description",
            env={"variable": "value"},
        )

    def test_job_submit_no_volumes_preemptible(self, partial_mocked_job) -> None:
        job = JobHandlerOperations("alice")
        job.submit(
            image="test-image",
            gpu="1",
            gpu_model="test-gpu",
            cpu="1.2",
            memory="1G",
            extshm="False",
            cmd=["test-command"],
            http="8183",
            ssh="25",
            volumes=[],
            env={"var": "val"},
            jobs=partial_mocked_job,
            is_preemptible=True,
            description="job description",
        )

        partial_mocked_job().submit.assert_called_once()

        partial_mocked_job().submit.assert_called_with(
            image=Image(image="test-image", command="test-command"),
            network=NetworkPortForwarding({"http": 8183, "ssh": 25}),
            resources=Resources.create("1.2", "1", "test-gpu", "1G", "False"),
            volumes=None,
            is_preemptible=True,
            description="job description",
            env={"var": "val"},
        )
