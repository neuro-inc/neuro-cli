import subprocess
from typing import Optional
from unittest import mock
from unittest.mock import MagicMock

import pytest

from neuromation.cli.command_handlers import (
    JobHandlerOperations,
    ModelHandlerOperations,
)
from neuromation.client.jobs import JobDescription
from neuromation.http import BadRequestError


@pytest.fixture()
def alice_model():
    return ModelHandlerOperations("alice")


class TestSSHConnectionToJob:
    @pytest.mark.parametrize(
        "ssh, jump, ucont, kcont, det",
        [
            (None, "jump.key", "user", "container.key", "no-ssh-specified"),
            (334, None, "user", "container.key", "no-jump-key-specified"),
            (334, "jump.key", None, "container.key", "no-user-specified"),
            (334, "jump.key", "user", None, "no-container-key-specified"),
        ],
    )
    def test_model_develop_validate_required(
        self, partial_mocked_job, ssh, jump, ucont, kcont, det
    ):
        with pytest.raises(ValueError):
            jh = JobHandlerOperations("no-token")
            jh.connect_ssh("test-job-id", jump, ucont, kcont, partial_mocked_job)

    def job_status(self, desired_state: str, ssh: Optional[str]):
        def jobs_(id):
            return JobDescription(
                status=desired_state,
                id=id,
                client=None,
                image="ubuntu",
                command="shell",
                ssh=ssh,
            )

        return jobs_

    def test_ssh_to_non_existing_job(
        self, alice_model, partial_mocked_model, partial_mocked_job
    ) -> None:
        def not_found(id: str):
            raise BadRequestError("Job not found.")

        partial_mocked_job().status = not_found
        mock = MagicMock()

        with pytest.raises(ValueError):
            jh = JobHandlerOperations("no-token")
            jh.start_ssh = mock
            jh.connect_ssh(
                "not-found", "jump_hst_key", "root", "key_paths", partial_mocked_job
            )
        assert mock.call_count == 0

    def test_ssh_to_non_running_job(
        self, alice_model, partial_mocked_model, partial_mocked_job
    ) -> None:
        partial_mocked_job().status = self.job_status("failed", "no.ssh.path")
        mock = MagicMock()

        with pytest.raises(ValueError, match=f"Job is not running."):
            jh = JobHandlerOperations("no-token")
            jh.start_ssh = mock
            jh.connect_ssh(
                "not-found", "jump_hst_key", "root", "key_paths", partial_mocked_job
            )
        assert mock.call_count == 0

    def test_ssh_to_running_job_no_ssh(
        self, alice_model, partial_mocked_model, partial_mocked_job
    ) -> None:
        partial_mocked_job().status = self.job_status("running", None)
        mock = MagicMock()

        with pytest.raises(
            ValueError, match=f"Job should be started with SSH support."
        ):
            jh = JobHandlerOperations("no-token")
            jh.start_ssh = mock
            jh.connect_ssh(
                "not-found", "jump_hst_key", "root", "key_paths", partial_mocked_job
            )
        assert mock.call_count == 0

    def test_ssh_to_running_job_ssh(
        self, alice_model, partial_mocked_model, partial_mocked_job
    ) -> None:
        partial_mocked_job().status = self.job_status("running", "ssh://test.server:22")

        jh = JobHandlerOperations("no-token")
        jh.start_ssh = MagicMock()
        jh.connect_ssh(
            "my-job-id", "jump_hst_key", "root", "key_paths", partial_mocked_job
        )

        jh.start_ssh.assert_any_call(
            "my-job-id", "server", "no-token", "jump_hst_key", "root", "key_paths"
        )

    def test_tunnel_to_running_job_ssh_not_exists(
        self, alice_model, partial_mocked_model, partial_mocked_job
    ) -> None:
        def not_found(id: str):
            raise BadRequestError("Job not found.")

        partial_mocked_job().status = not_found

        with pytest.raises(ValueError):
            alice_model.python_remote_debug(
                "my-job-id", "jump_hst_key", 32121, partial_mocked_job
            )

    def test_tunnel_to_running_job_ssh_no_key(self, alice_model, partial_mocked_job):
        with pytest.raises(ValueError):
            alice_model.python_remote_debug(
                "my-job-id", None, 32121, partial_mocked_job
            )

    def test_tunnel_to_running_job_ssh(
        self, alice_model, partial_mocked_model, partial_mocked_job
    ) -> None:
        partial_mocked_job().status = self.job_status("running", "ssh://test.server:22")

        with mock.patch("subprocess.run") as runMock:
            alice_model.python_remote_debug(
                "my-job-id", "jump_hst_key", 32121, partial_mocked_job
            )

            runMock.assert_any_call(
                args=[
                    "ssh",
                    "-i",
                    "jump_hst_key",
                    "alice@server",
                    "-f",
                    "-N",
                    "-L",
                    f"32121:my-job-id:22",
                ],
                check=True,
            )

    def test_tunnel_to_running_job_ssh_exec_fail(
        self, alice_model, partial_mocked_model, partial_mocked_job
    ) -> None:
        partial_mocked_job().status = self.job_status("running", "ssh://test.server:22")

        with mock.patch("subprocess.run") as runMock:
            runMock.side_effect = subprocess.CalledProcessError(
                returncode=2, cmd="no command"
            )

            alice_model.python_remote_debug(
                "my-job-id", "jump_hst_key", 32121, partial_mocked_job
            )
