import pytest

from neuromation.strings.parse import DockerImageNameParser


class TestDockerImageNameParser:
    parse = DockerImageNameParser.parse_image_name

    async def test_no_repo_no_name_no_label(self):
        value = "archlinux"
        actual = self.parse(
            value, neuromation_repo="registry.dev", neuromation_user="user"
        )
        assert actual == "docker.io/library/archlinux:latest"

    async def test_no_repo_no_name_with_label(self):
        value = "archlinux:1.0.6"
        actual = self.parse(
            value, neuromation_repo="registry.dev", neuromation_user="user"
        )
        assert actual == "docker.io/library/archlinux:1.0.6"

    async def test_no_repo_with_name_no_label(self):
        value = "base/archlinux"
        actual = self.parse(
            value, neuromation_repo="registry.dev", neuromation_user="user"
        )
        assert actual == "docker.io/base/archlinux:latest"

    async def test_no_repo_with_name_with_label(self):
        value = "base/archlinux:pre-latest"
        actual = self.parse(
            value, neuromation_repo="registry.dev", neuromation_user="user"
        )
        assert actual == "docker.io/base/archlinux:pre-latest"

    async def test_with_repo_with_name_no_label(self):
        value = "repository.com/base/archlinux"
        actual = self.parse(
            value, neuromation_repo="registry.dev", neuromation_user="user"
        )
        assert actual == "repository.com/base/archlinux:latest"

    async def test_with_repo_with_name_with_label(self):
        value = "repository.com/base/archlinux:v1.2"
        actual = self.parse(
            value, neuromation_repo="registry.dev", neuromation_user="user"
        )
        assert actual == "repository.com/base/archlinux:v1.2"

    async def test_with_home_dir_no_repo_no_name_no_label(self):
        value = "~/archlinux"
        actual = self.parse(
            value, neuromation_repo="registry.dev", neuromation_user="user"
        )
        assert actual == "registry.dev/user/archlinux:latest"

    async def test_with_home_dir_no_repo_no_name_with_label(self):
        value = "~/archlinux:v1.2"
        actual = self.parse(
            value, neuromation_repo="registry.dev", neuromation_user="user"
        )
        assert actual == "registry.dev/user/archlinux:v1.2"

    async def test_no_repo_no_name_empty_label__fail(self):
        value = "archlinux:"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_no_repo_empty_name_no_label__fail(self):
        value = "/archlinux"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_no_repo_empty_name_empty_label__fail(self):
        value = "/archlinux:"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_with_repo_with_slashes_in_name_no_label__fail(self):
        value = "a/repo/user/archlinux"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_with_repo_no_name_no_label__fail(self):
        value = "repo//archlinux"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_with_repo_no_name_with_label__fail(self):
        value = "repo//archlinux:latest"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_with_repo_no_name_empty_label__fail(self):
        value = "repo//archlinux:"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_empty_repo_with_name_no_label__fail(self):
        value = "/user/archlinux"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_empty_repo_with_name_with_label__fail(self):
        value = "/user/archlinux:latest"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")

    async def test_empty_repo_with_name_empty_label__fail(self):
        value = "/user/archlinux:"
        with pytest.raises(ValueError, match="Invalid image name"):
            self.parse(value, neuromation_repo="registry.dev", neuromation_user="user")
