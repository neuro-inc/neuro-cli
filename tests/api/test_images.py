import os
import sys
from typing import Any, AsyncIterator, Callable, Dict, Iterator

import asynctest
import pytest
from aiodocker.exceptions import DockerError
from aiohttp import web
from yarl import URL

from neuromation.api import (
    AuthorizationError,
    Client,
    LocalImage,
    RemoteImage,
    TagOption,
)
from neuromation.api.parsing_utils import (
    _as_repo_str,
    _get_url_authority,
    _ImageNameParser,
)
from tests import _TestServerFactory


_MakeClient = Callable[..., Client]


@pytest.fixture()
def patch_docker_host() -> Iterator[None]:
    with asynctest.mock.patch.dict(
        os.environ, values={"DOCKER_HOST": "http://localhost:45678"}
    ):
        yield


class TestImageParser:
    parser = _ImageNameParser(
        default_user="alice",
        default_cluster="test-cluster",
        registry_url=URL("https://reg.neu.ro"),
    )

    @pytest.mark.parametrize(
        "image",
        [
            "image://test-cluster/me/ubuntu:v10.04",
            "image:ubuntu:v10.04",
            "image:///ubuntu:v10.04",
            "image:ubuntu:v10.04",
            "ubuntu:v10.04",
        ],
    )
    def test_has_tag_ok(self, image: str) -> None:
        assert self.parser.has_tag(image)

    def test_has_tag_no_tag(self) -> None:
        image = "ubuntu"
        assert not self.parser.has_tag(image)

    def test_has_tag_no_tag_with_slash(self) -> None:
        image = "library/ubuntu"
        assert not self.parser.has_tag(image)

    def test_has_tag_empty_tag(self) -> None:
        image = "ubuntu:"
        with pytest.raises(ValueError, match="empty tag"):
            self.parser.has_tag(image)

    def test_has_tag_empty_tag_with_slash(self) -> None:
        image = "library/ubuntu:"
        with pytest.raises(ValueError, match="empty tag"):
            self.parser.has_tag(image)

    def test_has_tag_empty_image_name(self) -> None:
        image = ":latest"
        with pytest.raises(ValueError, match="empty name"):
            self.parser.has_tag(image)

    def test_has_tag_too_many_tags(self) -> None:
        image = "ubuntu:v10.04:latest"
        with pytest.raises(ValueError, match="too many tags"):
            self.parser.has_tag(image)

    def test_has_tag_lstrip(self) -> None:
        image = "image:game:latest"
        assert self.parser.has_tag(image)
        image = "image:game:mega"
        assert self.parser.has_tag(image)
        image = "image:game:v2.0:latest"
        with pytest.raises(ValueError, match="too many tags"):
            assert self.parser.has_tag(image)

    @pytest.mark.parametrize(
        "registry_url",
        ["http://reg.neu.ro", "https://reg.neu.ro", "https://reg.neu.ro/bla/bla"],
    )
    def test_get_registry_hostname(self, registry_url: str) -> None:
        parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL(registry_url),
        )
        assert parser._registry == "reg.neu.ro"

    @pytest.mark.parametrize(
        "registry_url", ["http://reg.neu.ro:5000", "http://reg.neu.ro:5000/bla/bla"]
    )
    def test_get_registry_hostname_with_port(self, registry_url: str) -> None:
        parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL(registry_url),
        )
        assert parser._registry == "reg.neu.ro:5000"

    @pytest.mark.parametrize(
        "registry_url",
        ["", "reg.neu.ro", "reg.neu.ro:5000", "https://", "https:///bla/bla"],
    )
    def test_get_registry_hostname__bad_url_empty_hostname(
        self, registry_url: str
    ) -> None:
        with pytest.raises(ValueError, match="Empty hostname in registry URL"):
            _ImageNameParser(
                default_user="alice",
                default_cluster="test-cluster",
                registry_url=URL(registry_url),
            )

    def test_split_image_name_no_tag(self) -> None:
        splitted = self.parser._split_image_name("ubuntu", "latest")
        assert splitted == ("ubuntu", "latest")

    def test_split_image_name_with_tag(self) -> None:
        splitted = self.parser._split_image_name("ubuntu:v10.04", "latest")
        assert splitted == ("ubuntu", "v10.04")

    def test_split_image_name_empty_tag(self) -> None:
        with pytest.raises(ValueError, match="empty tag"):
            self.parser._split_image_name("ubuntu:", "latest")

    def test_split_image_name_two_tags(self) -> None:
        with pytest.raises(ValueError, match="too many tags"):
            self.parser._split_image_name("ubuntu:v10.04:LTS", "latest")

    def test_split_image_name_with_registry_port_no_tag(self) -> None:
        splitted = self.parser._split_image_name("localhost:5000/ubuntu", "latest")
        assert splitted == ("localhost:5000/ubuntu", "latest")

    def test_split_image_name_with_registry_port_with_tag(self) -> None:
        splitted = self.parser._split_image_name(
            "localhost:5000/ubuntu:v10.04", "latest"
        )
        assert splitted == ("localhost:5000/ubuntu", "v10.04")

    def test_split_image_name_with_registry_port_two_tags(self) -> None:
        with pytest.raises(ValueError, match="too many tags"):
            self.parser._split_image_name("localhost:5000/ubuntu:v10.04:LTS", "latest")

    def test_split_image_name_with_registry_port_empty_tag(self) -> None:
        with pytest.raises(ValueError, match="empty tag"):
            self.parser._split_image_name("localhost:5000/ubuntu:", "latest")

    def test_split_image_name_with_registry_port_slash_in_tag(self) -> None:
        with pytest.raises(ValueError, match="invalid tag"):
            self.parser._split_image_name("localhost:5000/ubuntu:v10/04", "latest")

    # public method: parse_local

    @pytest.mark.parametrize(
        "url",
        [
            "image://",
            "image:///",
            "image://test-cluster/bob",
            "image://test-cluster/bob/",
        ],
    )
    def test_parse_as_neuro_image__no_image_name(self, url: str) -> None:
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser.parse_as_neuro_image(url)

    def test_parse_as_local_image_empty_fail(self) -> None:
        image = ""
        with pytest.raises(ValueError, match="empty image name"):
            self.parser.parse_as_local_image(image)

    def test_parse_as_local_image_dash_fail(self) -> None:
        image = "-zxc"
        with pytest.raises(ValueError, match="image cannot start with dash"):
            self.parser.parse_as_local_image(image)

    def test_parse_as_local_image_with_image_scheme_fail(self) -> None:
        image = "image://test-cluster/ubuntu"
        with pytest.raises(
            ValueError, match="scheme 'image://' is not allowed for local images"
        ):
            self.parser.parse_as_local_image(image)

    def test_parse_as_local_image_with_other_scheme_ok(self) -> None:
        image = "http://ubuntu"
        parsed = self.parser.parse_as_local_image(image)
        # instead of parser, the docker client will fail
        assert parsed == LocalImage(name="http://ubuntu", tag="latest")

    def test_parse_as_local_image_no_tag(self) -> None:
        image = "ubuntu"
        parsed = self.parser.parse_as_local_image(image)
        assert parsed == LocalImage(name="ubuntu", tag="latest")

    def test_parse_as_local_image_with_tag(self) -> None:
        image = "ubuntu:v10.04"
        parsed = self.parser.parse_as_local_image(image)
        assert parsed == LocalImage(name="ubuntu", tag="v10.04")

    def test_parse_as_local_image_2_tag_fail(self) -> None:
        image = "ubuntu:v10.04:LTS"
        with pytest.raises(ValueError, match="too many tags"):
            self.parser.parse_as_local_image(image)

    # public method: parse_remote

    @pytest.mark.parametrize(
        "url",
        [
            "image://test-cluster/bob/ubuntu:v10.04?key=value",
            "image://test-cluster/bob/ubuntu?key=value",
            "image:///ubuntu?key=value",
            "image:ubuntu?key=value",
        ],
    )
    def test_parse_as_neuro_image__with_query__fail(self, url: str) -> None:
        with pytest.raises(ValueError, match="query is not allowed"):
            self.parser.parse_as_neuro_image(url)

    @pytest.mark.parametrize(
        "url",
        [
            "image://test-cluster/bob/ubuntu:v10.04#fragment",
            "image://test-cluster/bob/ubuntu#fragment",
            "image:///ubuntu#fragment",
            "image:ubuntu#fragment",
        ],
    )
    def test_parse_as_neuro_image__with_fragment__fail(self, url: str) -> None:
        with pytest.raises(ValueError, match="fragment is not allowed"):
            self.parser.parse_as_neuro_image(url)

    def test_parse_as_neuro_image__with_user__fail(self) -> None:
        url = "image://user@test-cluster/bob/ubuntu"
        with pytest.raises(ValueError, match="user is not allowed"):
            self.parser.parse_as_neuro_image(url)

    def test_parse_as_neuro_image__with_password__fail(self) -> None:
        url = "image://:password@test-cluster/bob/ubuntu"
        with pytest.raises(ValueError, match="password is not allowed"):
            self.parser.parse_as_neuro_image(url)

    def test_parse_as_neuro_image__with_port__fail(self) -> None:
        url = "image://test-cluster:443/bob/ubuntu"
        with pytest.raises(ValueError, match="port is not allowed"):
            self.parser.parse_as_neuro_image(url)

    def test_parse_as_neuro_image_empty_fail__fail(self) -> None:
        image = ""
        with pytest.raises(ValueError, match="empty image name"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_dash_fail__fail(self) -> None:
        image = "-zxc"
        with pytest.raises(ValueError, match="image cannot start with dash"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_fail(self) -> None:
        image = "ubuntu"
        with pytest.raises(
            ValueError, match="scheme 'image://' is required for remote images"
        ):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_invalid_scheme_1_fail(self) -> None:
        image = "ubuntu:latest"
        with pytest.raises(
            ValueError, match="scheme 'image://' is required for remote images"
        ):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_invalid_scheme_2_fail(self) -> None:
        image = "http://ubuntu"
        with pytest.raises(
            ValueError, match="scheme 'image://' is required for remote images"
        ):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_with_user_with_tag(self) -> None:
        image = "image://other-cluster/bob/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="other-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_with_user_with_tag_2(self) -> None:
        image = "image://other-cluster/bob/library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="other-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_with_user_no_tag(self) -> None:
        image = "image://other-cluster/bob/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="latest",
            owner="bob",
            cluster_name="other-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_with_user_no_tag_2(self) -> None:
        image = "image://other-cluster/bob/library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="latest",
            owner="bob",
            cluster_name="other-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_no_slash_no_user_no_tag(self) -> None:
        image = "image:ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="latest",
            owner="alice",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_no_slash_no_user_no_tag_2(self) -> None:
        image = "image:library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="latest",
            owner="alice",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_no_slash_no_user_with_tag(self) -> None:
        image = "image:ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="v10.04",
            owner="alice",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_no_slash_no_user_with_tag_2(self) -> None:
        image = "image:library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="alice",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_1_slash_no_cluster_no_name_no_tag(
        self,
    ) -> None:
        image = "image:/ubuntu"
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_1_slash_no_cluster_no_tag(self) -> None:
        image = "image:/bob/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="latest",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_1_slash_no_cluster_no_tag_2(self) -> None:
        image = "image:/bob/library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="latest",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_1_slash_no_cluster_no_name_with_tag(
        self,
    ) -> None:
        image = "image:/ubuntu:v10.04"
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_1_slash_no_cluster_with_tag(self) -> None:
        image = "image:/bob/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_1_slash_no_cluster_with_tag_2(
        self,
    ) -> None:
        image = "image:/bob/library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_2_slash_cluster_user_no_name_no_tag_fail(
        self,
    ) -> None:
        image = "image://other-cluster/ubuntu"
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_2_slash_cluster_no_user_with_tag_fail(
        self,
    ) -> None:
        image = "image://ubuntu:v10.04"
        with pytest.raises(ValueError, match="port can't be converted to integer"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_3_slash_no_cluster_no_name_no_tag(
        self,
    ) -> None:
        image = "image:///ubuntu"
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_3_slash_no_cluster_no_tag(self) -> None:
        image = "image:///bob/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="latest",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_3_slash_no_cluster_no_tag_2(self) -> None:
        image = "image:///bob/library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="latest",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_3_slash_no_cluster_no_name_with_tag(
        self,
    ) -> None:
        image = "image:///ubuntu:v10.04"
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_3_slash_no_cluster_with_tag(self) -> None:
        image = "image:///bob/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_3_slash_no_cluster_with_tag_2(
        self,
    ) -> None:
        image = "image:///bob/library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_4_slash_no_cluster_no_name_with_tag(
        self,
    ) -> None:
        image = "image:////ubuntu:v10.04"
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_4_slash_no_cluster_with_tag(self) -> None:
        image = "image:////bob/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_4_slash_no_cluster_with_tag_2(
        self,
    ) -> None:
        image = "image:////bob/library/ubuntu:v10.04"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_4_slash_no_cluster_no_name_no_tag(
        self,
    ) -> None:
        image = "image:////ubuntu"
        with pytest.raises(ValueError, match="no image name specified"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_with_scheme_4_slash_no_cluster_no_tag(self) -> None:
        image = "image:////bob/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="latest",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_with_scheme_4_slash_no_cluster_no_tag_2(self) -> None:
        image = "image:////bob/library/ubuntu"
        parsed = self.parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="latest",
            owner="bob",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_no_scheme_no_slash_no_tag_fail(self) -> None:
        image = "ubuntu"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_no_slash_with_tag_fail(self) -> None:
        image = "ubuntu:v10.04"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_1_slash_no_tag_fail(self) -> None:
        image = "library/ubuntu"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_1_slash_with_tag_fail(self) -> None:
        image = "library/ubuntu:v10.04"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_2_slash_no_tag_fail(self) -> None:
        image = "docker.io/library/ubuntu"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_2_slash_with_tag_fail(self) -> None:
        image = "docker.io/library/ubuntu:v10.04"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_no_scheme_3_slash_no_tag_fail(self) -> None:
        image = "something/docker.io/library/ubuntu"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image)

    def test_is_neuro_registry_with_registry_prefix(self) -> None:
        assert self.parser.is_in_neuro_registry("reg.neu.ro/user/image:tag")
        assert not self.parser.is_in_neuro_registry('docker.io/library/ubuntu"')

    def test_parse_as_neuro_image_with_registry_prefix(self) -> None:
        image = self.parser.parse_as_neuro_image("reg.neu.ro/user/image:tag")
        assert str(image) == "image://test-cluster/user/image:tag"

    def test_parse_as_neuro_image_no_scheme_3_slash_with_tag_fail(self) -> None:
        image = "something/docker.io/library/ubuntu:v10.04"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image)

    def test_parse_as_neuro_image_allow_tag_false_with_scheme_no_tag(self) -> None:
        image = "image:ubuntu"
        parsed = self.parser.parse_as_neuro_image(image, tag_option=TagOption.DENY)
        assert parsed == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag=None,
            owner="alice",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_parse_as_neuro_image_allow_tag_false_no_scheme_no_tag(self) -> None:
        image = "ubuntu"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            self.parser.parse_as_neuro_image(image, tag_option=TagOption.DENY)

    def test_parse_as_neuro_image_allow_tag_false_no_scheme_with_tag(self) -> None:
        image = "ubuntu:latest"
        with pytest.raises(ValueError, match="tag is not allowed"):
            self.parser.parse_as_neuro_image(image, tag_option=TagOption.DENY)

    def test_parse_as_neuro_image_allow_tag_false_with_scheme_lstrip(self) -> None:
        image = "image:game:latest"
        with pytest.raises(ValueError, match="tag is not allowed"):
            self.parser.parse_as_neuro_image(image, tag_option=TagOption.DENY)
        image = "image:game:mega"
        with pytest.raises(ValueError, match="tag is not allowed"):
            self.parser.parse_as_neuro_image(image, tag_option=TagOption.DENY)
        image = "image:game:v2.0:latest"
        with pytest.raises(ValueError, match="too many tags"):
            self.parser.parse_as_neuro_image(image, tag_option=TagOption.DENY)

    def test_convert_to_local_image(self) -> None:
        neuro_image = RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="latest",
            owner="artem",
            cluster_name="test-cluster",
            registry="reg.com",
        )
        local_image = self.parser.convert_to_local_image(neuro_image)
        assert local_image == LocalImage(name="ubuntu", tag="latest")

    def test_convert_to_neuro_image(self) -> None:
        local_image = LocalImage(name="ubuntu", tag="latest")
        neuro_image = self.parser.convert_to_neuro_image(local_image)
        assert neuro_image == RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="latest",
            owner="alice",
            cluster_name="test-cluster",
            registry="reg.neu.ro",
        )

    def test_normalize_is_neuro_image(self) -> None:
        image = "image:ubuntu"
        assert (
            self.parser.normalize(image) == "image://test-cluster/alice/ubuntu:latest"
        )

    def test_normalize_is_local_image(self) -> None:
        image = "docker.io/library/ubuntu"
        assert self.parser.normalize(image) == "docker.io/library/ubuntu:latest"

    def test_normalize_invalid_image_name_left_as_is(self) -> None:
        image = "image://test-cluster/ubuntu"
        assert self.parser.normalize(image) == "image://test-cluster/ubuntu"

    # corner case 'image:latest'

    def test_parse_as_neuro_image__ambiguous_case__fail(self) -> None:
        url = "image:latest"
        with pytest.raises(ValueError, match="ambiguous value"):
            self.parser.parse_as_neuro_image(url)

    def test_parse_as_local_image__ambiguous_case__fail(self) -> None:
        url = "image:latest"
        with pytest.raises(ValueError, match="ambiguous value"):
            self.parser.parse_as_local_image(url)

    # other corner cases

    def test_is_in_neuro_registry__registry_has_port__neuro_image(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "image://test-cluster/bob/library/ubuntu:v10.04"
        assert my_parser.is_in_neuro_registry(image) is True

    def test_is_in_neuro_registry__registry_has_port__image_in_good_repo(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "localhost:5000/bob/library/ubuntu:v10.04"
        assert my_parser.is_in_neuro_registry(image) is True

    def test_is_in_neuro_registry__registry_has_port__image_in_bad_repo(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "localhost:9999/bob/library/ubuntu:v10.04"
        assert my_parser.is_in_neuro_registry(image) is False

    def test_is_in_neuro_registry__registry_has_port__local_image(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "ubuntu:v10.04"
        assert my_parser.is_in_neuro_registry(image) is False

    def test_is_in_neuro_registry__registry_has_port(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "ubuntu:v10.04"
        parsed = my_parser.parse_as_local_image(image)
        assert parsed == LocalImage(name="ubuntu", tag="v10.04")

    def test_parse_as_neuro_image__registry_has_port__neuro_image(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "image://test-cluster/bob/library/ubuntu:v10.04"
        parsed = my_parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="localhost:5000",
        )

    def test_parse_as_neuro_image__registry_has_port__image_in_good_repo(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "localhost:5000/bob/library/ubuntu:v10.04"
        parsed = my_parser.parse_as_neuro_image(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="localhost:5000",
        )

    def test_parse_as_neuro_image__registry_has_port__image_in_bad_repo(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "localhost:9999/bob/library/ubuntu:v10.04"
        with pytest.raises(ValueError, match="scheme 'image://' is required"):
            my_parser.parse_as_neuro_image(image)

    def test_parse_remote__registry_has_port__neuro_image(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "image://test-cluster/bob/library/ubuntu:v10.04"
        parsed = my_parser.parse_remote(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="localhost:5000",
        )

    def test_parse_remote__registry_has_port__image_in_good_repo(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "localhost:5000/bob/library/ubuntu:v10.04"
        parsed = my_parser.parse_remote(image)
        assert parsed == RemoteImage.new_neuro_image(
            name="library/ubuntu",
            tag="v10.04",
            owner="bob",
            cluster_name="test-cluster",
            registry="localhost:5000",
        )

    def test_parse_remote__registry_has_port__image_in_other_repo(self) -> None:
        my_parser = _ImageNameParser(
            default_user="alice",
            default_cluster="test-cluster",
            registry_url=URL("http://localhost:5000"),
        )
        image = "example.com:9999/bob/library/ubuntu:v10.04"
        parsed = my_parser.parse_remote(image)
        # NOTE: "owner" is parsed only for images in neuromation registry
        assert parsed == RemoteImage.new_external_image(
            name="bob/library/ubuntu", tag="v10.04", registry="example.com:9999",
        )


class TestRemoteImage:
    def test_as_str_in_neuro_registry_tag_none(self) -> None:
        image = RemoteImage.new_neuro_image(
            name="ubuntu",
            tag=None,
            owner="me",
            cluster_name="test-cluster",
            registry="registry.io",
        )
        assert str(image) == "image://test-cluster/me/ubuntu"
        assert _as_repo_str(image) == "registry.io/me/ubuntu"

    def test_as_str_in_neuro_registry_tag_yes(self) -> None:
        image = RemoteImage.new_neuro_image(
            name="ubuntu",
            tag="v10.04",
            owner="me",
            cluster_name="test-cluster",
            registry="registry.io",
        )
        assert str(image) == "image://test-cluster/me/ubuntu:v10.04"
        assert _as_repo_str(image) == "registry.io/me/ubuntu:v10.04"

    def test_as_str_not_in_neuro_registry_tag_none(self) -> None:
        image = RemoteImage.new_external_image(name="ubuntu")
        assert str(image) == "ubuntu"
        assert _as_repo_str(image) == "ubuntu"

    def test_as_str_not_in_neuro_registry_tag_yes(self) -> None:
        image = RemoteImage.new_external_image(name="ubuntu", tag="v10.04")
        assert str(image) == "ubuntu:v10.04"
        assert _as_repo_str(image) == "ubuntu:v10.04"

    def test_as_docker_url_in_neuro_registry(self) -> None:
        image = RemoteImage(
            name="ubuntu",
            tag="v10.04",
            owner="me",
            cluster_name="test-cluster",
            registry="registry.io",
        )
        assert image.as_docker_url() == "registry.io/me/ubuntu:v10.04"

    def test_as_docker_url_not_in_neuro_registry(self) -> None:
        image = RemoteImage(name="ubuntu", tag="v10.04", owner=None, registry=None)
        assert image.as_docker_url() == "ubuntu:v10.04"


@pytest.mark.usefixtures("patch_docker_host")
class TestImages:
    parser = _ImageNameParser(
        default_user="user",
        default_cluster="test-cluster",
        registry_url=URL("https://registry-dev.neu.ro"),
    )

    @asynctest.mock.patch(
        "aiodocker.Docker.__init__",
        side_effect=ValueError(
            "text Either DOCKER_HOST or local sockets are not available text"
        ),
    )
    async def test_unavailable_docker(
        self, patched_init: Any, make_client: _MakeClient
    ) -> None:
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:bananas"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            with pytest.raises(DockerError, match=r"Docker engine is not available.+"):
                await client.images.pull(image, local_image)

    @asynctest.mock.patch(
        "aiodocker.Docker.__init__", side_effect=ValueError("something went wrong")
    )
    async def test_unknown_docker_error(
        self, patched_init: Any, make_client: _MakeClient
    ) -> None:
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:bananas"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            with pytest.raises(ValueError, match=r"something went wrong"):
                await client.images.pull(image, local_image)

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    async def test_push_non_existent_image(
        self, patched_tag: Any, make_client: _MakeClient
    ) -> None:
        patched_tag.side_effect = DockerError(404, {"message": "Mocked error"})
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:bananas-no-more"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            with pytest.raises(ValueError, match=r"not found"):
                await client.images.push(local_image, image)

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_push_image_to_foreign_repo(
        self, patched_push: Any, patched_tag: Any, make_client: _MakeClient
    ) -> None:
        patched_tag.return_value = True
        patched_push.side_effect = DockerError(403, {"message": "Mocked error"})
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:bananas-no-more"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            with pytest.raises(AuthorizationError):
                await client.images.push(local_image, image)

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_push_image_with_docker_api_error(
        self, patched_push: Any, patched_tag: Any, make_client: _MakeClient
    ) -> None:
        async def error_generator() -> AsyncIterator[Dict[str, Any]]:
            yield {"error": True, "errorDetail": {"message": "Mocked message"}}

        patched_tag.return_value = True
        patched_push.return_value = error_generator()
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:bananas-wrong-food"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            with pytest.raises(DockerError) as exc_info:
                await client.images.push(local_image, image)
        assert exc_info.value.status == 900
        assert exc_info.value.message == "Mocked message"

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_success_push_image(
        self, patched_push: Any, patched_tag: Any, make_client: _MakeClient
    ) -> None:
        async def message_generator() -> AsyncIterator[Dict[str, Any]]:
            yield {}

        patched_tag.return_value = True
        patched_push.return_value = message_generator()
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:bananas-is-here"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            result = await client.images.push(local_image, image)
        assert result == image

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.push")
    async def test_success_push_image_no_target(
        self, patched_push: Any, patched_tag: Any, make_client: _MakeClient
    ) -> None:
        async def message_generator() -> AsyncIterator[Dict[str, Any]]:
            yield {}

        patched_tag.return_value = True
        patched_push.return_value = message_generator()
        image = self.parser.parse_as_neuro_image("image://default/user/bananas:latest")
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            result = await client.images.push(local_image)
        assert result == image

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_non_existent_image(
        self, patched_pull: Any, make_client: _MakeClient
    ) -> None:
        patched_pull.side_effect = DockerError(404, {"message": "Mocked error"})
        async with make_client("https://api.localhost.localdomain") as client:
            image = self.parser.parse_as_neuro_image(
                "image://test-cluster/bob/image:no-bananas-here"
            )
            local_image = self.parser.parse_as_local_image("bananas:latest")
            with pytest.raises(ValueError, match=r"not found"):
                await client.images.pull(image, local_image)

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_image_from_foreign_repo(
        self, patched_pull: Any, make_client: _MakeClient
    ) -> None:
        patched_pull.side_effect = DockerError(403, {"message": "Mocked error"})
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:not-your-bananas"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            with pytest.raises(AuthorizationError):
                await client.images.pull(image, local_image)

    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_pull_image_with_docker_api_error(
        self, patched_pull: Any, make_client: Any
    ) -> None:
        async def error_generator() -> AsyncIterator[Dict[str, Any]]:
            yield {"error": True, "errorDetail": {"message": "Mocked message"}}

        patched_pull.return_value = error_generator()
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:nuts-here"
        )
        async with make_client("https://api.localhost.localdomain") as client:
            with pytest.raises(DockerError) as exc_info:
                await client.images.pull(image, image)
        assert exc_info.value.status == 900
        assert exc_info.value.message == "Mocked message"

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_success_pull_image(
        self, patched_pull: Any, patched_tag: Any, make_client: _MakeClient
    ) -> None:
        async def message_generator() -> AsyncIterator[Dict[str, Any]]:
            yield {}

        patched_tag.return_value = True
        patched_pull.return_value = message_generator()
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/image:bananas"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            result = await client.images.pull(image, local_image)
        assert result == local_image

    @asynctest.mock.patch("aiodocker.images.DockerImages.tag")
    @asynctest.mock.patch("aiodocker.images.DockerImages.pull")
    async def test_success_pull_image_no_target(
        self, patched_pull: Any, patched_tag: Any, make_client: _MakeClient
    ) -> None:
        async def message_generator() -> AsyncIterator[Dict[str, Any]]:
            yield {}

        patched_tag.return_value = True
        patched_pull.return_value = message_generator()
        image = self.parser.parse_as_neuro_image(
            "image://test-cluster/bob/bananas:latest"
        )
        local_image = self.parser.parse_as_local_image("bananas:latest")
        async with make_client("https://api.localhost.localdomain") as client:
            result = await client.images.pull(image)
        assert result == local_image


class TestRegistry:
    @pytest.mark.skipif(
        sys.platform == "win32", reason="aiodocker doesn't support Windows pipes yet"
    )
    async def test_ls_repositories(
        self, aiohttp_server: _TestServerFactory, make_client: _MakeClient
    ) -> None:
        JSON = {"repositories": ["bob/alpine", "jill/bananas"]}

        async def handler(request: web.Request) -> web.Response:
            return web.json_response(JSON)

        app = web.Application()
        app.router.add_get("/v2/_catalog", handler)

        srv = await aiohttp_server(app)
        url = "http://platform"
        registry_url = srv.make_url("/v2/")

        async with make_client(url, registry_url=registry_url) as client:
            ret = await client.images.ls()

        registry = _get_url_authority(registry_url)
        assert registry is not None
        assert set(ret) == {
            RemoteImage.new_neuro_image(
                "alpine",
                tag=None,
                owner="bob",
                cluster_name="default",
                registry=registry,
            ),
            RemoteImage.new_neuro_image(
                "bananas",
                tag=None,
                owner="jill",
                cluster_name="default",
                registry=registry,
            ),
        }

    @pytest.mark.skipif(
        sys.platform == "win32", reason="aiodocker doesn't support Windows pipes yet"
    )
    async def test_tags_bad_image_with_tag(self, make_client: _MakeClient) -> None:
        url = URL("http://whatever")
        registry_url = URL("http://whatever-registry")
        async with make_client(url, registry_url=registry_url) as client:
            image = RemoteImage.new_neuro_image(
                name="ubuntu",
                tag="latest",
                owner="me",
                cluster_name="test-cluster",
                registry="reg",
            )
            with pytest.raises(ValueError, match="tag is not allowed"):
                await client.images.tags(image)

    @pytest.mark.skipif(
        sys.platform == "win32", reason="aiodocker doesn't support Windows pipes yet"
    )
    async def test_tags_bad_image_without_name(self, make_client: _MakeClient) -> None:
        url = URL("http://whatever")
        registry_url = URL("http://whatever-registry")
        async with make_client(url, registry_url=registry_url) as client:
            image = RemoteImage.new_neuro_image(
                name="",
                tag=None,
                owner="me",
                cluster_name="test-cluster",
                registry="reg",
            )
            with pytest.raises(ValueError, match="missing image name"):
                await client.images.tags(image)
