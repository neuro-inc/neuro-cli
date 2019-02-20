import os

import asynctest
import pytest
from aiodocker.exceptions import DockerError
from aiohttp import web
from yarl import URL

from neuromation.cli.command_spinner import SpinnerBase
from neuromation.client import AuthorizationError, Client, ImageParser
from neuromation.client.images import (
    STATUS_CUSTOM_ERROR,
    STATUS_FORBIDDEN,
    STATUS_NOT_FOUND,
    DockerImage,
)


@pytest.fixture()
def patch_docker_host():
    with asynctest.mock.patch.dict(
        os.environ, values={"DOCKER_HOST": "http://localhost:45678"}
    ):
        yield


class TestImageParser:
    parser = ImageParser(default_user="alice", registry_url="https://reg.neu.ro")

    @pytest.mark.parametrize(
        "registry_url",
        [
            "http://reg.neu.ro",
            "https://reg.neu.ro",
            "http://reg.neu.ro:5000",
            "https://reg.neu.ro/bla/bla",
            "http://reg.neu.ro:5000/bla/bla",
        ],
    )
    def test__get_registry_hostname(self, registry_url):
        registry = self.parser._get_registry_hostname(registry_url)
        assert registry == "reg.neu.ro"

    @pytest.mark.parametrize(
        "registry_url",
        ["", "reg.neu.ro", "reg.neu.ro:5000", "https://", "https:///bla/bla"],
    )
    def test__get_registry_hostname_bad_registry_url(self, registry_url):
        with pytest.raises(ValueError, match="Empty hostname in registry URL"):
            self.parser._get_registry_hostname(registry_url)

    def test__split_image_name_no_colon(self):
        splitted = self.parser._split_image_name("ubuntu")
        assert splitted == ("ubuntu", "latest")

    def test__split_image_name_1_colon(self):
        splitted = self.parser._split_image_name("ubuntu:v10.04")
        assert splitted == ("ubuntu", "v10.04")

    def test__split_image_name_2_colon(self):
        with pytest.raises(ValueError, match="too many tags"):
            self.parser._split_image_name("ubuntu:v10.04:LTS")

    @pytest.mark.parametrize(
        "url", ["", "/", "image://", "image:///", "image://bob", "image://bob/"]
    )
    def test__check_allowed_uri_elements__no_path(self, url):
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser._check_allowed_uri_elements(URL(url))

    @pytest.mark.parametrize(
        "url",
        [
            "image://bob/ubuntu:v10.04?key=value",
            "image://bob/ubuntu?key=value",
            "image:///ubuntu?key=value",
            "image:ubuntu?key=value",
        ],
    )
    def test__check_allowed_uri_elements__with_query(self, url):
        with pytest.raises(ValueError, match="query is not allowed"):
            self.parser._check_allowed_uri_elements(URL(url))

    @pytest.mark.parametrize(
        "url",
        [
            "image://bob/ubuntu:v10.04#fragment",
            "image://bob/ubuntu#fragment",
            "image:///ubuntu#fragment",
            "image:ubuntu#fragment",
        ],
    )
    def test__check_allowed_uri_elements__with_fragment(self, url):
        with pytest.raises(ValueError, match="fragment is not allowed"):
            self.parser._check_allowed_uri_elements(URL(url))

    def test__check_allowed_uri_elements__with_user(self):
        url = "image://user@bob/ubuntu"
        with pytest.raises(ValueError, match="user is not allowed"):
            self.parser._check_allowed_uri_elements(URL(url))

    def test__check_allowed_uri_elements__with_password(self):
        url = "image://:password@bob/ubuntu"
        with pytest.raises(ValueError, match="password is not allowed"):
            self.parser._check_allowed_uri_elements(URL(url))

    def test__check_allowed_uri_elements__with_port(self):
        url = "image://bob:443/ubuntu"
        with pytest.raises(ValueError, match="port is not allowed"):
            self.parser._check_allowed_uri_elements(URL(url))

    # public method: parse_local

    def test_parse_as_docker_image_empty_fail(self):
        image = ""
        with pytest.raises(ValueError, match="empty image name"):
            self.parser.parse_as_docker_image(image)

    def test_parse_as_docker_image_none_fail(self):
        image = None
        with pytest.raises(ValueError, match="empty image name"):
            self.parser.parse_as_docker_image(image)

    def test_parse_as_docker_image_with_image_scheme_fail(self):
        image = "image://ubuntu"
        msg = "scheme 'image://' is not allowed for local images"
        with pytest.raises(ValueError, match=msg):
            self.parser.parse_as_docker_image(image)

    def test_parse_as_docker_image_with_other_scheme_ok(self):
        image = "http://ubuntu"
        parsed = self.parser.parse_as_docker_image(image)
        # instead of parser, the docker client will fail
        assert parsed == DockerImage(name="http", tag="//ubuntu")

    def test_parse_as_docker_image_no_tag(self):
        image = "ubuntu"
        parsed = self.parser.parse_as_docker_image(image)
        assert parsed == DockerImage(name="ubuntu", tag="latest")

    def test_parse_as_docker_image_with_tag(self):
        image = "ubuntu:v10.04"
        parsed = self.parser.parse_as_docker_image(image)
        assert parsed == DockerImage(name="ubuntu", tag="v10.04")

    def test_parse_as_docker_image_2_tag_fail(self):
        image = "ubuntu:v10.04:LTS"
        msg = "cannot parse image name 'ubuntu:v10.04:LTS': too many tags"
        with pytest.raises(ValueError, match=msg):
            self.parser.parse_as_docker_image(image)

    # public method: parse_remote

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_empty_fail(self, require_scheme):
        image = ""
        with pytest.raises(ValueError, match="empty image name"):
            self.parser.parse_as_neuro_image(image)

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_none_fail(self, require_scheme):
        image = None
        with pytest.raises(ValueError, match="empty image name"):
            self.parser.parse_as_neuro_image(image)

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_with_user_with_tag(self, require_scheme):
        image = "image://bob/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="v10.04", owner="bob", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_with_user_with_tag_2(
        self, require_scheme
    ):
        image = "image://bob/library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="v10.04", owner="bob", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_with_user_no_tag(self, require_scheme):
        image = "image://bob/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="latest", owner="bob", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_with_user_no_tag_2(self, require_scheme):
        image = "image://bob/library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="latest", owner="bob", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_no_slash_no_user_no_tag(
        self, require_scheme
    ):
        image = "image:ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_no_slash_no_user_no_tag_2(
        self, require_scheme
    ):
        image = "image:library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_no_slash_no_user_with_tag(
        self, require_scheme
    ):
        image = "image:ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_no_slash_no_user_with_tag_2(
        self, require_scheme
    ):
        image = "image:library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_1_slash_no_user_no_tag(
        self, require_scheme
    ):
        image = "image:/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_1_slash_no_user_no_tag_2(
        self, require_scheme
    ):
        image = "image:/library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_1_slash_no_user_with_tag(
        self, require_scheme
    ):
        image = "image:/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_1_slash_no_user_with_tag_2(
        self, require_scheme
    ):
        image = "image:/library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_2_slash_user_no_tag_fail(
        self, require_scheme
    ):
        image = "image://ubuntu"
        with pytest.raises(ValueError, match="no image name specified"):
            parsed = self.parser.parse_as_neuro_image(image)

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_2_slash_user_with_tag_fail(
        self, require_scheme
    ):
        image = "image://ubuntu:v10.04"
        with pytest.raises(ValueError, match="port can't be converted to integer"):
            parsed = self.parser.parse_as_neuro_image(image)

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_3_slash_no_user_no_tag(
        self, require_scheme
    ):
        image = "image:///ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_3_slash_no_user_no_tag_2(
        self, require_scheme
    ):
        image = "image:///library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_3_slash_no_user_with_tag(
        self, require_scheme
    ):
        image = "image:///ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_3_slash_no_user_with_tag_2(
        self, require_scheme
    ):
        image = "image:///library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_4_slash_no_user_with_tag(
        self, require_scheme
    ):
        image = "image:////ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_4_slash_no_user_with_tag_2(
        self, require_scheme
    ):
        image = "image:////library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_4_slash_no_user_no_tag_2(
        self, require_scheme
    ):
        image = "image:////ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_4_slash_no_user_no_tag_2(
        self, require_scheme
    ):
        image = "image:////library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_tilde_user_no_tag(self, require_scheme):
        image = "image://~/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_tilde_user_no_tag_2(self, require_scheme):
        image = "image://~/library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="latest", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_tilde_user_with_tag(self, require_scheme):
        image = "image://~/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    @pytest.mark.parametrize("require_scheme", [True, False])
    def test_parse_as_neuro_image_with_scheme_tilde_user_with_tag_2(
        self, require_scheme
    ):
        image = "image://~/library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == DockerImage(
            name="library/ubuntu", tag="v10.04", owner="alice", registry="reg.neu.ro"
        )

    def test_parse_as_neuro_image_no_scheme_no_slash_no_tag_fail(self):
        image = "ubuntu"
        msg = "scheme 'image://' is required"
        with pytest.raises(ValueError, match=msg):
            parsed = self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_no_slash_with_tag_fail(self):
        image = "ubuntu:v10.04"
        msg = "scheme 'image://' expected, found: 'ubuntu://'"
        with pytest.raises(ValueError, match=msg):
            parsed = self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_1_slash_no_tag_fail(self):
        image = "library/ubuntu"
        msg = "scheme 'image://' is required"
        with pytest.raises(ValueError, match=msg):
            parsed = self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_1_slash_with_tag_fail(self):
        image = "library/ubuntu:v10.04"
        msg = "scheme 'image://' is required"
        with pytest.raises(ValueError, match=msg):
            parsed = self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_2_slash_no_tag_fail(self):
        image = "docker.io/library/ubuntu"
        msg = "scheme 'image://' is required"
        with pytest.raises(ValueError, match=msg):
            parsed = self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_2_slash_with_tag_fail(self):
        image = "docker.io/library/ubuntu:v10.04"
        msg = "scheme 'image://' is required"
        with pytest.raises(ValueError, match=msg):
            parsed = self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_3_slash_no_tag_fail(self):
        image = "something/docker.io/library/ubuntu"
        msg = "scheme 'image://' is required"
        with pytest.raises(ValueError, match=msg):
            parsed = self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_3_slash_with_tag_fail(self):
        image = "something/docker.io/library/ubuntu:v10.04"
        msg = "scheme 'image://' is required"
        with pytest.raises(ValueError, match=msg):
            parsed = self.parser.parse_as_neuro_image(image)


@pytest.mark.usefixtures("patch_docker_host")
class TestImages:
    parser = ImageParser(default_user="bob", registry_url="https://reg.neu.ro")

    @pytest.fixture()
    def spinner(self) -> SpinnerBase:
        return SpinnerBase.create_spinner(False)

    @asynctest.mock.patch(
        "aiodocker.Docker.__init__",
        side_effect=ValueError(
            "text Either DOCKER_HOST or local sockets are not available text"
        ),
    )
    async def test_unavailable_docker(self, patched_init, token, spinner):
        image = self.parser.parse_as_neuro_image(f"image://bob/image:bananas")
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            with pytest.raises(DockerError, match=r"Docker engine is not available.+"):
                await client.images.pull(image, image, spinner)

    @asynctest.mock.patch(
        "aiodocker.Docker.__init__", side_effect=ValueError("something went wrong")
    )
    async def test_unknown_docker_error(self, patched_init, token, spinner):
        image = self.parser.parse_as_neuro_image(f"image://bob/image:bananas")
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            with pytest.raises(ValueError, match=r"something went wrong"):
                await client.images.pull(image, image, spinner)

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    async def test_push_non_existent_image(self, patched_tag, token, spinner):
        patched_tag.side_effect = DockerError(
            STATUS_NOT_FOUND, {"message": "Mocked error"}
        )
        image = self.parser.parse_as_neuro_image(f"image://bob/image:bananas-no-more")
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            with pytest.raises(ValueError, match=r"not found"):
                await client.images.push(image, image, spinner)

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_push_image_to_foreign_repo(
        self, patched_push, patched_tag, token, spinner
    ):
        patched_tag.return_value = True
        patched_push.side_effect = DockerError(
            STATUS_FORBIDDEN, {"message": "Mocked error"}
        )
        image = self.parser.parse_as_neuro_image(f"image://bob/image:bananas-no-more")
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            with pytest.raises(AuthorizationError):
                await client.images.push(image, image, spinner)

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_push_image_with_docker_api_error(
        self, patched_push, patched_tag, token, spinner
    ):
        async def error_generator():
            yield {"error": True, "errorDetail": {"message": "Mocked message"}}

        patched_tag.return_value = True
        patched_push.return_value = error_generator()
        image = self.parser.parse_as_neuro_image(
            f"image://bob/image:bananas-wrong-food"
        )
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            with pytest.raises(DockerError) as exc_info:
                await client.images.push(image, image, spinner)
        assert exc_info.value.status == STATUS_CUSTOM_ERROR
        assert exc_info.value.message == "Mocked message"

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_success_push_image(self, patched_push, patched_tag, token, spinner):
        async def message_generator():
            yield {}

        patched_tag.return_value = True
        patched_push.return_value = message_generator()
        image = self.parser.parse_as_neuro_image(f"image://bob/image:bananas-is-here")
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            result = await client.images.push(image, image, spinner)
        assert result == image

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_non_existent_image(self, patched_pull, token, spinner):
        patched_pull.side_effect = DockerError(
            STATUS_NOT_FOUND, {"message": "Mocked error"}
        )
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            image = self.parser.parse_as_neuro_image(
                f"image://bob/image:no-bananas-here"
            )
            with pytest.raises(ValueError, match=r"not found"):
                await client.images.pull(image, image, spinner)

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_image_from_foreign_repo(self, patched_pull, token, spinner):
        patched_pull.side_effect = DockerError(
            STATUS_FORBIDDEN, {"message": "Mocked error"}
        )
        image = self.parser.parse_as_neuro_image(f"image://bob/image:not-your-bananas")
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            with pytest.raises(AuthorizationError):
                await client.images.pull(image, image, spinner)

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_image_with_docker_api_error(self, patched_pull, token, spinner):
        async def error_generator():
            yield {"error": True, "errorDetail": {"message": "Mocked message"}}

        patched_pull.return_value = error_generator()
        image = self.parser.parse_as_neuro_image(f"image://bob/image:nuts-here")
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            with pytest.raises(DockerError) as exc_info:
                await client.images.pull(image, image, spinner)
        assert exc_info.value.status == STATUS_CUSTOM_ERROR
        assert exc_info.value.message == "Mocked message"

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_success_pull_image(self, patched_pull, patched_tag, token, spinner):
        async def message_generator():
            yield {}

        patched_tag.return_value = True
        patched_pull.return_value = message_generator()
        image = self.parser.parse_as_neuro_image(f"image://bob/image:bananas")
        async with Client(URL("https://api.localhost.localdomain"), token) as client:
            result = await client.images.pull(image, image, spinner)
        assert result == image


class TestRegistry:
    async def test_ls(self, aiohttp_server, token):
        JSON = {"repositories": ["image://bob/alpine", "image://jill/bananas"]}

        async def handler(request):
            return web.json_response(JSON)

        app = web.Application()
        app.router.add_get("/v2/_catalog", handler)

        srv = await aiohttp_server(app)
        url = "http://platform"
        registry_url = srv.make_url("/v2/")
        async with Client(url, registry_url=registry_url, token=token) as client:
            ret = await client.images.ls()
        assert ret == [URL(image) for image in JSON["repositories"]]
