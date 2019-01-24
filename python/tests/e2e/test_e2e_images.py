from pathlib import Path
from uuid import uuid4 as uuid

import aiodocker
import pytest
from yarl import URL

from neuromation.cli.rc import ConfigFactory
from neuromation.clientv2.jobs import JobStatus as Status
from tests.e2e.test_e2e_utils import wait_job_change_state_to


TEST_IMAGE_NAME = "e2e-banana-image"


@pytest.fixture()
def docker(loop):
    client = aiodocker.Docker()
    yield client
    loop.run_until_complete(client.close())


@pytest.fixture()
def tag():
    return str(uuid())


async def generate_image(docker: aiodocker.Docker, tag: str) -> str:
    image_archive = Path(__file__).parent / "assets/echo-tag.tar"
    # TODO use random image name here
    tag = f"{TEST_IMAGE_NAME}:{tag}"
    await docker.images.build(
        fileobj=image_archive.open(mode="r+b"),
        tag=tag,
        buildargs={"TAG": tag},
        encoding="identity",
    )

    return tag


@pytest.fixture()
def image(loop, docker, tag):
    image = loop.run_until_complete(generate_image(docker, tag))
    yield image
    loop.run_until_complete(docker.images.delete(image, force=True))


@pytest.mark.e2e
def test_images_complete_lifecycle(run, image, tag, loop, docker):
    # Let`s push image
    captured = run(["image", "push", image])

    assert not captured.err

    image_url = URL(captured.out.strip())
    assert image_url.scheme == "image"
    assert image_url.path.lstrip("/") == image

    # Check if image available on registry
    captured = run(["image", "ls"])

    image_urls = [URL(line) for line in captured.out.splitlines() if line]
    for url in image_urls:
        assert url.scheme == "image"
    image_url_without_tag = image_url.with_path(
        image_url.path.replace(f":{tag}", "")
    )
    assert image_url_without_tag in image_urls

    pulled_image = f"{image}-pull"

    # Pull image as with another tag
    captured = run(["image", "pull", str(image_url), pulled_image])
    assert not captured.err
    assert pulled_image == captured.out.strip()
    # Check if image exists and remove, all-in-one swiss knife
    loop.run_until_complete(docker.images.delete(pulled_image, force=True))

    # Execute image and check result
    config = ConfigFactory.load()
    repo = str(URL(config.url).host).replace("platform.", "registry.")
    image_with_repo = f'{repo}/{image_url.host}/{image_url.path.lstrip("/")}'
    captured = run(
        [
            "job",
            "submit",
            image_with_repo,
            "--memory",
            "100M",
            "-g",
            "0",
            "-q",
            "--non-preemptible",
        ]
    )
    assert not captured.err
    job_id = captured.out.strip()
    assert job_id.startswith("job-")
    wait_job_change_state_to(run, job_id, Status.SUCCEEDED, Status.FAILED)
    captured = run(["job", "monitor", job_id])
    assert not captured.err
    assert captured.out.strip() == tag
