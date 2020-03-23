import enum
from dataclasses import dataclass
from typing import Optional, Tuple

from yarl import URL


class TagOption(enum.Enum):
    ALLOW = enum.auto()
    DENY = enum.auto()
    DEFAULT = enum.auto()


@dataclass(frozen=True)
class RemoteImage:
    name: str
    tag: Optional[str] = None
    owner: Optional[str] = None
    registry: Optional[str] = None
    cluster_name: Optional[str] = None

    def __post_init__(self) -> None:
        if self.registry:
            if self.owner:
                if not self.cluster_name:
                    raise ValueError("required cluster name")
            else:
                if self.cluster_name:
                    raise ValueError("required owner")
        else:
            if self.owner or self.cluster_name:
                raise ValueError("required registry")

    def as_docker_url(self) -> str:
        if _is_in_neuro_registry(self):
            name = f"https://{self.registry}/{self.owner}/{self.name}"
            tag = f":{self.tag}" if self.tag else ""
            return name + tag
        else:
            return str(self)

    def __str__(self) -> str:
        pre = (
            f"image://{self.cluster_name}/{self.owner}/"
            if _is_in_neuro_registry(self)
            else ""
        )
        post = f":{self.tag}" if self.tag else ""
        return pre + self.name + post


def _is_in_neuro_registry(image: RemoteImage) -> bool:
    return bool(image.registry and image.owner and image.cluster_name)


def _as_repo_str(image: RemoteImage) -> str:
    pre = f"{image.registry}/{image.owner}/" if _is_in_neuro_registry(image) else ""
    post = f":{image.tag}" if image.tag else ""
    return pre + image.name + post


@dataclass(frozen=True)
class LocalImage:
    name: str
    tag: Optional[str] = None

    def __str__(self) -> str:
        post = f":{self.tag}" if self.tag else ""
        return self.name + post


class _ImageNameParser:
    def __init__(self, default_user: str, default_cluster: str, registry_url: URL):
        self._default_user = default_user
        self._default_cluster = default_cluster
        if not registry_url.host:
            raise ValueError(
                f"Empty hostname in registry URL '{registry_url}': "
                "please consider updating configuration"
            )
        self._registry = _get_url_authority(registry_url)

    def parse_as_local_image(self, image: str) -> LocalImage:
        try:
            self._validate_image_name(image)
            return self._parse_as_local_image(image)
        except ValueError as e:
            raise ValueError(f"Invalid local image '{image}': {e}") from e

    def parse_as_neuro_image(
        self, image: str, *, tag_option: TagOption = TagOption.DEFAULT
    ) -> RemoteImage:
        try:
            self._validate_image_name(image)
            tag: Optional[str]
            if tag_option == TagOption.DEFAULT:
                tag = "latest"
            else:
                if tag_option == TagOption.DENY and self.has_tag(image):
                    raise ValueError("tag is not allowed")
                tag = None
            return self._parse_as_neuro_image(image, default_tag=tag)
        except ValueError as e:
            raise ValueError(f"Invalid remote image '{image}': {e}") from e

    def parse_remote(
        self, value: str, *, tag_option: TagOption = TagOption.DEFAULT
    ) -> RemoteImage:
        if self.is_in_neuro_registry(value):
            return self.parse_as_neuro_image(value, tag_option=tag_option)
        else:
            img = self.parse_as_local_image(value)
            name = img.name
            registry = None
            if ":" in name:
                msg = "here name must contain slash(es). checked by _split_image_name()"
                assert "/" in name, msg
                registry, name = name.split("/", 1)

            return RemoteImage(name=name, tag=img.tag, registry=registry)

    def is_in_neuro_registry(self, image: str) -> bool:
        # not use URL here because URL("ubuntu:v1") is parsed as scheme=ubuntu path=v1
        return image.startswith("image:") or image.startswith(f"{self._registry}/")

    def convert_to_neuro_image(self, image: LocalImage) -> RemoteImage:
        return RemoteImage(
            name=image.name,
            tag=image.tag,
            owner=self._default_user,
            cluster_name=self._default_cluster,
            registry=self._registry,
        )

    def convert_to_local_image(self, image: RemoteImage) -> LocalImage:
        return LocalImage(name=image.name, tag=image.tag)

    def normalize(self, image: str) -> str:
        try:
            if self.is_in_neuro_registry(image):
                remote_image = self.parse_as_neuro_image(image)
                image_normalized = str(remote_image)
            else:
                local_image = self.parse_as_local_image(image)
                image_normalized = str(local_image)
        except ValueError:
            image_normalized = image
        return image_normalized

    def has_tag(self, image: str) -> bool:
        prefix = "image:"
        if image.startswith(prefix):
            image = image.lstrip(prefix).lstrip("/")
        name, tag = self._split_image_name(image, default_tag=None)
        return bool(tag)

    def _validate_image_name(self, image: str) -> None:
        if not image:
            raise ValueError("empty image name")
        if image.startswith("-"):
            raise ValueError(f"image cannot start with dash")
        if image == "image:latest":
            raise ValueError(
                "ambiguous value: valid as both local and remote image name"
            )

    def _parse_as_local_image(self, image: str) -> LocalImage:
        if self.is_in_neuro_registry(image):
            raise ValueError("scheme 'image://' is not allowed for local images")
        name, tag = self._split_image_name(image, "latest")
        return LocalImage(name=name, tag=tag)

    def _parse_as_neuro_image(
        self, image: str, default_tag: Optional[str]
    ) -> RemoteImage:
        if not self.is_in_neuro_registry(image):
            raise ValueError("scheme 'image://' is required for remote images")

        if image.startswith(f"{self._registry}/"):
            path = image[len(f"{self._registry}/") :]
            image = f"image://{self._default_cluster}/{path}"

        url = URL(image)

        if url.scheme and url.scheme != "image":
            # image with port in registry: `localhost:5000/owner/ubuntu:latest`
            url = URL(f"//{url}")

        if not url.scheme:
            parts = url.path.split("/")
            url = URL.build(
                scheme="image",
                host=parts[1],
                path="/".join([""] + parts[2:]),
                query=url.query,
            )

        self._check_allowed_uri_elements(url)

        registry = self._registry
        name, tag = self._split_image_name(url.path.lstrip("/"), default_tag)
        if url.host:
            cluster_name = url.host
            owner, _, name = name.partition("/")
            if not name:
                raise ValueError("no image name specified")
        else:
            owner = self._default_user
            cluster_name = self._default_cluster
        return RemoteImage(
            name=name,
            tag=tag,
            registry=registry,
            owner=owner,
            cluster_name=cluster_name,
        )

    def _split_image_name(
        self, image: str, default_tag: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        if image.endswith(":") or image.startswith(":"):
            # case `ubuntu:`, `:latest`
            raise ValueError("empty name or empty tag")
        colon_count = image.count(":")
        if colon_count == 0:
            # case `ubuntu`
            name, tag = image, default_tag
        elif colon_count == 1:
            # case `ubuntu:latest`
            name, tag = image.split(":")
            if "/" in tag:
                # case `localhost:5000/ubuntu`
                name, tag = image, default_tag
        elif colon_count == 2:
            # case `localhost:9000/owner/ubuntu:latest`
            if "/" not in image:
                # case `localhost:9000:latest`
                raise ValueError("too many tags")
            name, tag = image.rsplit(":", 1)
        else:
            raise ValueError("too many tags")
        if tag and (":" in tag or "/" in tag):
            raise ValueError("invalid tag")
        return name, tag

    def _check_allowed_uri_elements(self, url: URL) -> None:
        if not url.path or url.path == "/":
            raise ValueError("no image name specified")
        if url.query:
            raise ValueError(f"query is not allowed, found: '{url.query}'")
        if url.fragment:
            raise ValueError(f"fragment is not allowed, found: '{url.fragment}'")
        if url.user:
            raise ValueError(f"user is not allowed, found: '{url.user}'")
        if url.password:
            raise ValueError(f"password is not allowed, found: '{url.password}'")
        if url.port and url.scheme == "image":
            raise ValueError(
                f"port is not allowed with 'image://' scheme, found: '{url.port}'"
            )


def _get_url_authority(url: URL) -> Optional[str]:
    if url.host is None:
        return None
    port = url.explicit_port  # type: ignore
    suffix = f":{port}" if port is not None else ""
    return url.host + suffix
