from pathlib import Path
from uuid import uuid4 as uuid

import aiodocker
import pytest
from yarl import URL

from neuromation.cli.rc import ConfigFactory
from neuromation.client import JobStatus
from tests.e2e.utils import attempt


TEST_IMAGE_NAME = "e2e-banana-image"


@pytest.fixture()
async def docker(loop):
    client = aiodocker.Docker()
    yield client
    await client.close()


@pytest.fixture()
def tag():
    return str(uuid())


async def generate_image(docker: aiodocker.Docker, tag: str) -> str:
    image_archive = Path(__file__).parent / "assets/echo-tag.tar"
    # TODO use random image name here
    image_name = f"{TEST_IMAGE_NAME}:{tag}"
    with image_archive.open(mode="r+b") as fileobj:
        await docker.images.build(
            fileobj=fileobj, tag=image_name, buildargs={"TAG": tag}, encoding="identity"
        )

    return image_name


@pytest.fixture()
async def image(loop, docker, tag):
    image = await generate_image(docker, tag)
    yield image
    await docker.images.delete(image, force=True)


@pytest.mark.e2e
def test_images_complete_lifecycle(helper, run_cli, image, tag, loop, docker):
    # Let`s push image
    captured = run_cli(["image", "push", image])

    # stderr has "Used image ..." lines
    # assert not captured.err

    image_url = URL(captured.out.strip())
    assert image_url.scheme == "image"
    assert image_url.path.lstrip("/") == image

    # Check if image available on registry
    captured = run_cli(["image", "ls"])

    image_urls = [URL(line) for line in captured.out.splitlines() if line]
    for url in image_urls:
        assert url.scheme == "image"
    image_url_without_tag = image_url.with_path(image_url.path.replace(f":{tag}", ""))
    assert image_url_without_tag in image_urls

    pulled_image = f"{image}-pull"

    # Pull image as with another tag
    captured = run_cli(["image", "pull", f"image:{image}", pulled_image])
    # stderr has "Used image ..." lines
    # assert not captured.err
    assert pulled_image == captured.out.strip()
    # Check if image exists and remove, all-in-one swiss knife
    loop.run_until_complete(docker.images.delete(pulled_image, force=True))

    # Execute image and check result
    ConfigFactory.load()
    captured = run_cli(
        [
            "job",
            "submit",
            f"image:{image}",
            "-g",
            "0",
            "-q",
            "--non-preemptible",
            "--no-wait-start",
        ]
    )
    assert not captured.err
    job_id = captured.out.strip()
    assert job_id.startswith("job-")
    helper.wait_job_change_state_to(job_id, JobStatus.SUCCEEDED, JobStatus.FAILED)

    @attempt()
    def check_job_output():
        captured = run_cli(["job", "logs", job_id])
        assert not captured.err
        assert captured.out == tag

    check_job_output()
