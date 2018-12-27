from unittest import mock
from unittest.mock import MagicMock

import pytest
from docker import APIClient
from docker.errors import APIError

from neuromation.cli.rc import ConfigFactory


BLOCK_SIZE_MB = 16
FILE_COUNT = 1
FILE_SIZE_MB = 16
GENERATION_TIMEOUT_SEC = 120
RC_TEXT = """url: https://platform.dev.neuromation.io/api/v1
auth: {token}"""

UBUNTU_IMAGE_NAME = "ubuntu:latest"

JWT_HDR = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
JWT_CLAIM = "eyJpZGVudGl0eSI6Im5ldXJvbWF0aW9uLWlzLWF3ZXNvbWUhIn0"
JWT_SIG = "5T0RGa9aWv_XVFHQKjlrJEZ_5S8kHkxmzIvj4tnBOis"

CUSTOM_TOKEN_FOR_TESTS = f"{JWT_HDR}.{JWT_CLAIM}.{JWT_SIG}"

format_list = "{type:<15}{size:<15,}{name:<}".format


def docker_throw_error(*args, **kwargs):
    raise APIError(message="test")


def docker_return_false(*args, **kwargs):
    return False


@pytest.mark.e2e
def test_no_docker(run, monkeypatch):
    with mock.patch("docker.APIClient") as mocked_client:
        docker_client = MagicMock(APIClient)
        mocked_client.return_value = docker_client
        docker_client.ping.side_effect = docker_throw_error

        _, captured = run(["config", "auth", CUSTOM_TOKEN_FOR_TESTS])
        assert docker_client.login.call_count == 0
        assert docker_client.ping.call_count == 0

        _, captured = run(["image", "push", "abrakadabra"])
        assert docker_client.images.get.call_count == 0
        assert docker_client.ping.call_count == 1

        _, captured = run(["image", "pull", "abrakadabra"])
        assert docker_client.images.get.call_count == 0
        assert docker_client.ping.call_count == 2

    assert CUSTOM_TOKEN_FOR_TESTS == ConfigFactory.load().auth


@pytest.mark.e2e
def test_docker_config_with_docker(run, monkeypatch):
    with mock.patch("docker.APIClient") as mocked_client:
        docker_client = MagicMock(APIClient)
        mocked_client.return_value = docker_client

        _, captured = run(["config", "auth", CUSTOM_TOKEN_FOR_TESTS])

        assert docker_client.ping.call_count == 0
        assert docker_client.login.call_count == 0

    assert CUSTOM_TOKEN_FOR_TESTS == ConfigFactory.load().auth


@pytest.mark.e2e
def test_docker_push_with_docker(run, monkeypatch):
    with mock.patch("docker.APIClient") as mocked_client:
        docker_client = MagicMock(APIClient)
        mocked_client.return_value = docker_client

        _, captured = run(["image", "push", "abrakadabra:latest"])

        assert docker_client.ping.call_count == 1
        assert docker_client.tag.call_count == 1
        assert docker_client.push.call_count == 1


@pytest.mark.e2e
def test_docker_push_with_docker_no_tag(run, monkeypatch):
    with mock.patch("docker.APIClient") as mocked_client:
        docker_client = MagicMock(APIClient)
        mocked_client.return_value = docker_client

        _, captured = run(["image", "push", "abrakadabra"])

        assert docker_client.ping.call_count == 1
        assert docker_client.tag.call_count == 1
        assert docker_client.push.call_count == 1


@pytest.mark.e2e
def test_docker_pull_with_docker(run, monkeypatch):
    with mock.patch("docker.APIClient") as mocked_client:
        docker_client = MagicMock(APIClient)
        mocked_client.return_value = docker_client

        _, captured = run(["image", "pull", "abrakadabra:2"])

        assert docker_client.ping.call_count == 1
        assert docker_client.pull.call_count == 1


@pytest.mark.e2e
def test_docker_pull_with_docker_no_tag(run, monkeypatch):
    with mock.patch("docker.APIClient") as mocked_client:
        docker_client = MagicMock(APIClient)
        mocked_client.return_value = docker_client

        _, captured = run(["image", "pull", "abrakadabra"])

        assert docker_client.ping.call_count == 1
        assert docker_client.pull.call_count == 1


@pytest.mark.e2e
def test_docker_too_many_image_tags(run, monkeypatch):
    with mock.patch("docker.APIClient") as mocked_client:
        docker_client = MagicMock(APIClient)
        mocked_client.return_value = docker_client

        with pytest.raises(SystemExit):
            _, captured = run(["image", "pull", "abrakadabra:tag1:tag2"])

        with pytest.raises(SystemExit):
            _, captured = run(["image", "push", "abrakadabra:tag1:tag2"])

        with pytest.raises(SystemExit):
            _, captured = run(["image", "pull", ":tag"])  # no image name

        with pytest.raises(SystemExit):
            _, captured = run(["image", "push", ":tag"])  # no image name


@pytest.mark.e2e
def test_docker_error_scenarios(run, monkeypatch):
    with mock.patch("docker.APIClient") as mocked_client:
        docker_client = MagicMock(APIClient)
        mocked_client.return_value = docker_client

        with pytest.raises(SystemExit):
            old_value = docker_client.tag
            docker_client.tag = docker_throw_error
            _, captured = run(["image", "push", "abrakadabra:2"])
            docker_client.get = old_value

        with pytest.raises(SystemExit):
            old_value = docker_client.tag
            docker_client.tag = docker_return_false
            _, captured = run(["image", "push", "abrakadabra:2"])
            docker_client.get = old_value

        with pytest.raises(SystemExit):
            old_value = docker_client.images.pull
            docker_client.pull = docker_throw_error
            _, captured = run(["image", "pull", "abrakadabra:2"])
            docker_client.images.pull = old_value
