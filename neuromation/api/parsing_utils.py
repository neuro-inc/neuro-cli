from typing import Optional, Tuple

from yarl import URL

from .images import IMAGE_SCHEME, DockerImage


class ImageNameParser:
    default_tag = "latest"

    def __init__(self, default_user: str, registry_url: URL):
        self._default_user = default_user
        if not registry_url.host:
            raise ValueError(
                f"Empty hostname in registry URL '{registry_url}': "
                "please consider updating configuration"
            )
        self._registry = registry_url.host

    def parse_as_docker_image(self, image: str) -> DockerImage:
        try:
            self._validate_image_name(image)
            return self._parse_as_docker_image(image)
        except ValueError as e:
            raise ValueError(f"Invalid docker image '{image}': {e}") from e

    def parse_as_neuro_image(self, image: str, allow_tag: bool = True) -> DockerImage:
        try:
            self._validate_image_name(image)
            tag: Optional[str]
            if allow_tag:
                tag = self.default_tag
            else:
                if self.has_tag(image):
                    raise ValueError("tag is not allowed")
                tag = None
            return self._parse_as_neuro_image(image, default_tag=tag)
        except ValueError as e:
            raise ValueError(f"Invalid remote image '{image}': {e}") from e

    def is_in_neuro_registry(self, image: str) -> bool:
        # not use URL here because URL("ubuntu:v1") is parsed as scheme=ubuntu path=v1
        return image.startswith(f"{IMAGE_SCHEME}:") or image.startswith(
            f"{self._registry}/"
        )

    def convert_to_neuro_image(self, image: DockerImage) -> DockerImage:
        return DockerImage(
            name=image.name,
            tag=image.tag,
            owner=self._default_user,
            registry=self._registry,
        )

    def convert_to_docker_image(self, image: DockerImage) -> DockerImage:
        return DockerImage(name=image.name, tag=image.tag)

    def normalize(self, image: str) -> str:
        try:
            if self.is_in_neuro_registry(image):
                parsed_image = self.parse_as_neuro_image(image)
            else:
                parsed_image = self.parse_as_docker_image(image)
            image_normalized = parsed_image.as_url_str()
        except ValueError:
            image_normalized = image
        return image_normalized

    def has_tag(self, image: str) -> bool:
        prefix = f"{IMAGE_SCHEME}:"
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

    def _parse_as_docker_image(self, image: str) -> DockerImage:
        if self.is_in_neuro_registry(image):
            raise ValueError(
                f"scheme '{IMAGE_SCHEME}://' is not allowed for docker images"
            )
        name, tag = self._split_image_name(image, self.default_tag)
        return DockerImage(name=name, tag=tag)

    def _parse_as_neuro_image(
        self, image: str, default_tag: Optional[str]
    ) -> DockerImage:
        if not self.is_in_neuro_registry(image):
            raise ValueError(
                f"scheme '{IMAGE_SCHEME}://' is required for remote images"
            )

        url = URL(image)
        if not url.scheme:
            parts = url.path.split("/")
            url = url.build(
                scheme=IMAGE_SCHEME,
                host=parts[1],
                path="/".join([""] + parts[2:]),
                query=url.query,
            )
        else:
            assert url.scheme == IMAGE_SCHEME, f"invalid image scheme: '{url.scheme}'"

        self._check_allowed_uri_elements(url)

        registry = self._registry
        owner = self._default_user if not url.host or url.host == "~" else url.host
        name, tag = self._split_image_name(url.path.lstrip("/"), default_tag)
        return DockerImage(name=name, tag=tag, registry=registry, owner=owner)

    def _split_image_name(
        self, image: str, default_tag: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        colon_count = image.count(":")
        if colon_count == 0:
            image, tag = image, default_tag
        elif colon_count == 1:
            image, tag = image.split(":")
            if not tag:
                raise ValueError("empty tag is not allowed")
        else:
            raise ValueError("too many tags")
        return image, tag

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
        if url.port:
            raise ValueError(f"port is not allowed, found: '{url.port}'")
