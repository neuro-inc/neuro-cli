from unittest import mock
from unittest.mock import MagicMock

import pytest
from docker import DockerClient
from docker.errors import APIError

from neuromation.cli.rc import ConfigFactory


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = """url: http://platform.dev.neuromation.io/api/v1
auth: {token}"""

UBUNTU_IMAGE_NAME = "ubuntu:latest"

JWT_HDR = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
JWT_CLAIM = "eyJpZGVudGl0eSI6Im5ldXJvbWF0aW9uLWlzLWF3ZXNvbWUhIn0"
JWT_SIG = "5T0RGa9aWv_XVFHQKjlrJEZ_5S8kHkxmzIvj4tnBOis"

CUSTOM_TOKEN_FOR_TESTS = f"{JWT_HDR}.{JWT_CLAIM}.{JWT_SIG}"

format_list = "{type:<15}{size:<15,}{name:<}".format


def docker_throw_error(*args, **kwargs):
    raise APIError(message="test")


def test_no_docker(run, monkeypatch):
    with mock.patch("docker.from_env") as mocked_client:
        docker_client = MagicMock(DockerClient)
        mocked_client.return_value = docker_client
        docker_client.ping.side_effect = docker_throw_error

        _, captured = run(["config", "auth", CUSTOM_TOKEN_FOR_TESTS])
        assert docker_client.login.call_count == 0
        assert docker_client.ping.call_count == 1

        _, captured = run(["image", "push", "abrakadabra"])
        assert docker_client.images.get.call_count == 0
        assert docker_client.ping.call_count == 2

        _, captured = run(["image", "pull", "abrakadabra"])
        assert docker_client.images.get.call_count == 0
        assert docker_client.ping.call_count == 3

    assert CUSTOM_TOKEN_FOR_TESTS == ConfigFactory.load().auth


def test_docker_config_with_docker(run, monkeypatch):
    with mock.patch("docker.from_env") as mocked_client:
        docker_client = MagicMock(DockerClient)
        mocked_client.return_value = docker_client

        _, captured = run(["config", "auth", CUSTOM_TOKEN_FOR_TESTS])

        assert docker_client.ping.call_count == 1
        assert docker_client.login.call_count == 1

    assert CUSTOM_TOKEN_FOR_TESTS == ConfigFactory.load().auth


def test_docker_push_with_docker(run, monkeypatch):
    with mock.patch("docker.from_env") as mocked_client:
        docker_client = MagicMock(DockerClient)
        mocked_client.return_value = docker_client

        _, captured = run(["image", "push", "abrakadabra"])

        assert docker_client.ping.call_count == 1
        assert docker_client.images.get.call_count == 1
        assert docker_client.images.push.call_count == 1


def test_docker_pull_with_docker(run, monkeypatch):
    with mock.patch("docker.from_env") as mocked_client:
        docker_client = MagicMock(DockerClient)
        mocked_client.return_value = docker_client

        _, captured = run(["image", "pull", "abrakadabra"])

        assert docker_client.ping.call_count == 1
        assert docker_client.images.get.call_count == 0
        assert docker_client.images.pull.call_count == 1


def test_docker_error_scenarios(run, monkeypatch):
    with mock.patch("docker.from_env") as mocked_client:
        docker_client = MagicMock(DockerClient)
        mocked_client.return_value = docker_client

        with pytest.raises(SystemExit):
            old_value = docker_client.login
            docker_client.login = docker_throw_error
            _, captured = run(["config", "auth", CUSTOM_TOKEN_FOR_TESTS])
            docker_client.login = old_value

        with pytest.raises(SystemExit):
            old_value = docker_client.images.get
            docker_client.images.get = docker_throw_error
            _, captured = run(["image", "push", "abrakadabra"])
            docker_client.images.get = old_value

        with pytest.raises(SystemExit):
            old_value = docker_client.images.pull
            docker_client.images.pull = docker_throw_error
            _, captured = run(["image", "pull", "abrakadabra"])
            docker_client.images.pull = old_value
