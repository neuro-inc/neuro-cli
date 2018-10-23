import subprocess
from unittest import mock

import pytest

from neuromation.cli.command_handlers import ModelHandlerOperations
from neuromation.client.jobs import JobDescription, JobItem


@pytest.fixture()
def alice_model():
    return ModelHandlerOperations('alice')


class TestSSHConnectionPaths:

    def job_status(self, desired: str):
        def jobs_(id):
            return JobDescription(status=desired,
                                  id=id,
                                  client=None,
                                  image='ubuntu',
                                  command='shell',
                                  ssh='ssh://my-test-host:22')

        return jobs_

    @pytest.mark.parametrize(
        'ssh, jump, ucont, kcont, det',
        [
            (None, 'jump.key', 'user', 'container.key', 'no-ssh-specified'),
            (334, None, 'user', 'container.key', 'no-jump-key-specified'),
            (334, 'jump.key', None, 'container.key', 'no-user-specified'),
            (334, 'jump.key', 'user', None, 'no-container-key-specified'),
        ])
    def test_model_develop_validate_required(self, alice_model,
                                             ssh, jump, ucont, kcont, det):
        with pytest.raises(ValueError):
            alice_model.develop(
                'ubuntu:tf_2.0_beta',
                'storage:///data/set.txt',
                'storage://~/results/result1.txt',
                0, 1, 100, False,
                None, None,
                http=None, ssh=ssh,
                jump_host_rsa=jump,
                container_user=ucont, container_key_path=kcont
            )

    def test_model_submit_ok_job_failed(self, alice_model,
                                        partial_mocked_model,
                                        partial_mocked_job):
        partial_mocked_job().status = self.job_status('failed')

        with mock.patch('subprocess.run') as runMock:
            runMock.side_effect = subprocess.CalledProcessError(
                returncode=2,
                cmd='no command')

            with pytest.raises(ValueError):
                alice_model.develop(
                    'ubuntu:tf_2.0_beta',
                    'storage:///data/set.txt',
                    'storage://~/results/result1.txt',
                    0, 1, 100, False,
                    partial_mocked_model, partial_mocked_job,
                    http=None, ssh=334,
                    jump_host_rsa='/user/some/path.id.rsa',
                    container_user='container-user',
                    container_key_path='container-key-path'
                )

            assert runMock.call_count == 0

    def test_model_submit_ok_no_ssh_client(self, alice_model,
                                           partial_mocked_model,
                                           partial_mocked_job):
        partial_mocked_job().status = self.job_status('running')

        with mock.patch('subprocess.run') as runMock:
            runMock.side_effect = subprocess.CalledProcessError(
                returncode=2,
                cmd='no command')

            alice_model.develop(
                'ubuntu:tf_2.0_beta',
                'storage:///data/set.txt',
                'storage://~/results/result1.txt',
                0, 1, 100, False,
                partial_mocked_model, partial_mocked_job,
                http=None, ssh=334,
                jump_host_rsa='/user/some/path.id.rsa',
                container_user='container-user',
                container_key_path='container-key-path'
            )

            assert runMock.call_count == 1

    def test_model_submit_ok(self, alice_model, partial_mocked_model,
                             partial_mocked_job):
        partial_mocked_job().status = self.job_status('running')

        my_test_job_id = "my-test-job"

        def train_(**kwargs) -> JobItem:
            return JobItem("pending", my_test_job_id, client=None)

        partial_mocked_model().train = train_

        with mock.patch('subprocess.run') as runMock:
            alice_model.develop(
                'ubuntu:tf_2.0_beta',
                'storage:///data/set.txt',
                'storage://~/results/result1.txt',
                0, 1, 100, False,
                partial_mocked_model, partial_mocked_job,
                http=None, ssh=334,
                jump_host_rsa='/user/some/path.id.rsa',
                container_user='container-user',
                container_key_path='container-key-path'
            )

            assert runMock.call_count == 1
            proxy_command = f'ProxyCommand=ssh -i /user/some/path.id.rsa ' \
                            f'alice@my-test-host nc {my_test_job_id}' \
                            f'.default 31022'
            runMock.assert_any_call(args=['ssh', '-o', proxy_command,
                                          '-i', 'container-key-path',
                                          f'container-user@{my_test_job_id}'
                                          f'.default'],
                                    check=True)
