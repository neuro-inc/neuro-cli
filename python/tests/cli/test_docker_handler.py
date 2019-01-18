import os

import asynctest
import pytest
from aiodocker.exceptions import DockerError
from yarl import URL

from neuromation.cli.docker_handler import (
    STATUS_CUSTOM_ERROR,
    STATUS_FORBIDDEN,
    STATUS_NOT_FOUND,
    DockerHandler,
    Image,
)
from neuromation.client import AuthorizationError


@pytest.fixture()
def patch_docker_host():
    with asynctest.mock.patch.dict(
        os.environ, values={"DOCKER_HOST": "http://localhost:45678"}
    ):
        yield


class TestImage:
    @pytest.mark.parametrize(
        "test_url,expected_url,expected_local",
        [
            (URL("image://bob/php:7-fpm"), URL("image://bob/php:7-fpm"), "php:7-fpm"),
            (URL("image://bob/php"), URL("image://bob/php:latest"), "php:latest"),
            (URL("image:php:7-fpm"), URL("image://bob/php:7-fpm"), "php:7-fpm"),
            (URL("image:php"), URL("image://bob/php:latest"), "php:latest"),
            (
                URL("image://bob/project/php:7-fpm"),
                URL("image://bob/project/php:7-fpm"),
                "project/php:7-fpm",
            ),
            (
                URL("image:project/php"),
                URL("image://bob/project/php:latest"),
                "project/php:latest",
            ),
        ],
    )
    def test_correct_url(self, test_url, expected_url, expected_local):
        image = Image.from_url(test_url, "bob")
        assert image.url == expected_url
        assert image.local == expected_local

    def test_from_empty_url(self):
        with pytest.raises(ValueError, match="Image URL cannot be empty"):
            Image.from_url(url=URL(""), username="bob")
        pass

    def test_from_invalid_scheme_url(self):
        with pytest.raises(ValueError, match=r"Invalid scheme"):
            Image.from_url(
                url=URL("http://neuromation.io/what/does/the/fox/say"), username="ylvis"
            )
        pass

    def test_empty_path_url(self):
        with pytest.raises(ValueError, match=r"Image URL cannot be empty"):
            Image.from_url(url=URL("image:"), username="bob")
        with pytest.raises(ValueError, match=r"Invalid image"):
            Image.from_url(url=URL("image:///"), username="bob")
        pass

    def test_url_with_query(self):
        with pytest.raises(ValueError, match=r"Invalid image"):
            Image.from_url(url=URL("image://bob/image?bad=idea"), username="bob")
        pass

    def test_url_with_user(self):
        with pytest.raises(ValueError, match=r"Invalid image"):
            Image.from_url(url=URL("image://alien@bob/image"), username="bob")
        pass

    def test_url_with_port(self):
        with pytest.raises(ValueError, match=r"Invalid image"):
            Image.from_url(url=URL("image://bob:80/image"), username="bob")
        pass

    def test_url_with_few_colons(self):
        with pytest.raises(ValueError, match=r"only one colon allowed"):
            Image.from_url(url=URL("image://bob/image:tag1:tag2"), username="bob")
        pass

    @pytest.mark.parametrize(
        "test_local,expected_url,expected_local",
        [
            ("php:7-fpm", URL("image://bob/php:7-fpm"), "php:7-fpm"),
            ("php", URL("image://bob/php:latest"), "php:latest"),
            (
                "project/php:7-fpm",
                URL("image://bob/project/php:7-fpm"),
                "project/php:7-fpm",
            ),
            (
                "project/php",
                URL("image://bob/project/php:latest"),
                "project/php:latest",
            ),
        ],
    )
    def test_correct_local(self, test_local, expected_url, expected_local):
        image = Image.from_local(test_local, "bob")
        assert image.url == expected_url
        assert image.local == expected_local

    def test_local_with_few_colons(self):
        with pytest.raises(ValueError, match=r"only one colon allowed"):
            Image.from_local("image:tag1:tag2", "bob")

    def test_repo(self):
        image = Image.from_url(URL("image:php:5"), "bob")
        assert (
            image.to_repo("registry.neuromation.io")
            == "registry.neuromation.io/bob/php:5"
        )


@pytest.mark.usefixtures("patch_docker_host")
class TestDockerHandler:
    @asynctest.mock.patch(
        "aiodocker.Docker.__init__",
        side_effect=ValueError(
            "text Either DOCKER_HOST or local sockets are not available text"
        ),
    )
    async def test_unavailable_docker(self, patched_init):
        with pytest.raises(DockerError, match=r"Docker engine is not available.+"):
            DockerHandler("bob", "X-Token", URL("http://mock.registry.neuromation.io"))

    @asynctest.mock.patch(
        "aiodocker.Docker.__init__", side_effect=ValueError("something went wrong")
    )
    async def test_unknown_docker_error(self, patched_init):
        with pytest.raises(ValueError, match=r"something went wrong"):
            DockerHandler("bob", "X-Token", URL("http://mock.registry.neuromation.io"))

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    async def test_push_non_existent_image(self, patched_tag):
        patched_tag.side_effect = DockerError(
            STATUS_NOT_FOUND, {"message": "Mocked error"}
        )
        handler = DockerHandler(
            "bob", "X-Token", URL("http://mock.registry.neuromation.io")
        )
        with pytest.raises(ValueError, match=r"not found"):
            await handler.push("php:7", "")

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_push_image_to_foreign_repo(self, patched_push, patched_tag):
        patched_tag.return_value = True
        patched_push.side_effect = DockerError(
            STATUS_FORBIDDEN, {"message": "Mocked error"}
        )
        handler = DockerHandler(
            "bob", "X-Token", URL("http://mock.registry.neuromation.io")
        )
        with pytest.raises(AuthorizationError):
            await handler.push("php:7", "image://jane/java")

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_push_image_with_docker_api_error(self, patched_push, patched_tag):
        async def error_generator():
            yield {"error": True, "errorDetail": {"message": "Mocked message"}}

        patched_tag.return_value = True
        patched_push.return_value = error_generator()
        handler = DockerHandler(
            "bob", "X-Token", URL("http://mock.registry.neuromation.io")
        )
        with pytest.raises(DockerError) as exc_info:
            await handler.push("php:7", "")
        assert exc_info.value.status == STATUS_CUSTOM_ERROR
        assert exc_info.value.message == "Mocked message"

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_success_push_image(self, patched_push, patched_tag):
        async def message_generator():
            yield {}

        patched_tag.return_value = True
        patched_push.return_value = message_generator()
        handler = DockerHandler(
            "bob", "X-Token", URL("http://mock.registry.neuromation.io")
        )
        result = await handler.push("php:7", "image://bob/php:7")
        assert result == URL("image://bob/php:7")

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_non_existent_image(self, patched_pull):
        patched_pull.side_effect = DockerError(
            STATUS_NOT_FOUND, {"message": "Mocked error"}
        )
        handler = DockerHandler(
            "bob", "X-Token", URL("http://mock.registry.neuromation.io")
        )
        with pytest.raises(ValueError, match=r"not found"):
            await handler.pull("image:php:7", "")

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_image_from_foreign_repo(self, patched_pull):
        patched_pull.side_effect = DockerError(
            STATUS_FORBIDDEN, {"message": "Mocked error"}
        )
        handler = DockerHandler(
            "bob", "X-Token", URL("http://mock.registry.neuromation.io")
        )
        with pytest.raises(AuthorizationError):
            await handler.pull("image://jane/java", "")

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_image_with_docker_api_error(self, patched_pull):
        async def error_generator():
            yield {"error": True, "errorDetail": {"message": "Mocked message"}}

        patched_pull.return_value = error_generator()
        handler = DockerHandler(
            "bob", "X-Token", URL("http://mock.registry.neuromation.io")
        )
        with pytest.raises(DockerError) as exc_info:
            await handler.pull("image://jane/java", "")
        assert exc_info.value.status == STATUS_CUSTOM_ERROR
        assert exc_info.value.message == "Mocked message"

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_success_pull_image(self, patched_pull, patched_tag):
        async def message_generator():
            yield {}

        patched_tag.return_value = True
        patched_pull.return_value = message_generator()
        handler = DockerHandler(
            "bob", "X-Token", URL("http://mock.registry.neuromation.io")
        )
        result = await handler.pull("image:php:7", "php:7")
        assert result == "php:7"
