import sys
from pathlib import Path
from uuid import uuid4 as uuid

import aiodocker
import pytest
from yarl import URL

from neuromation.client import JobStatus
from tests.e2e.utils import attempt


TEST_IMAGE_NAME = "e2e-banana-image"


def parse_docker_ls_output(docker_ls_output):
    return set(
        repo_tag
        for info in docker_ls_output
        if info["RepoTags"] is not None
        for repo_tag in info["RepoTags"]
        if repo_tag
    )


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
@pytest.mark.skipif(
    sys.platform == "win32", reason="Image operations are not supported on Windows yet"
)
def test_images_complete_lifecycle(helper, run_cli, image, tag, loop, docker):

    # Let`s push image
    captured = run_cli(["image", "push", image])

    # stderr has "Used image ..." lines
    # assert not captured.err

    image_full_str = f"image://{helper._config.username}/{image}"
    assert captured.out.endswith(image_full_str)
    image_url = URL(image_full_str)

    # Check if image available on registry
    captured = run_cli(["image", "ls"])

    image_urls = [URL(line) for line in captured.out.splitlines() if line]
    for url in image_urls:
        assert url.scheme == "image"
    image_url_without_tag = image_url.with_path(image_url.path.replace(f":{tag}", ""))
    assert image_url_without_tag in image_urls

    # delete local
    loop.run_until_complete(docker.images.delete(image, force=True))
    docker_ls_output = loop.run_until_complete(docker.images.list())
    local_images = parse_docker_ls_output(docker_ls_output)
    assert image not in local_images

    # Pull image as with another tag
    captured = run_cli(["image", "pull", f"image://~/{image}"])
    # stderr has "Used image ..." lines
    # assert not captured.err
    assert captured.out.endswith(image)

    # check pulled locally, delete for cleanup
    docker_ls_output = loop.run_until_complete(docker.images.list())
    local_images = parse_docker_ls_output(docker_ls_output)
    assert image in local_images

    # Execute image and check result
    captured = run_cli(
        [
            "submit",
            str(image_url),
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


@pytest.mark.e2e
def test_images_push_with_specified_name(helper, run_cli, image, tag, loop, docker):
    # Let`s push image
    image_no_tag = image.replace(f":{tag}", "")
    pushed_no_tag = f"{image_no_tag}-pushed"
    pulled_no_tag = f"{image_no_tag}-pulled"
    pulled = f"{pulled_no_tag}:{tag}"

    captured = run_cli(["image", "push", image, f"image://~/{pushed_no_tag}:{tag}"])
    # stderr has "Used image ..." lines
    # assert not captured.err
    image_pushed_full_str = f"image://{helper._config.username}/{pushed_no_tag}:{tag}"
    assert captured.out.endswith(image_pushed_full_str)
    image_url_without_tag = image_pushed_full_str.replace(f":{tag}", "")

    # Check if image available on registry
    captured = run_cli(["image", "ls"])
    image_urls = captured.out.splitlines()
    assert image_url_without_tag in image_urls

    # check locally
    docker_ls_output = loop.run_until_complete(docker.images.list())
    local_images = parse_docker_ls_output(docker_ls_output)
    assert pulled not in local_images

    # Pull image as with another name
    captured = run_cli(["image", "pull", f"image:{pushed_no_tag}:{tag}", pulled])
    # stderr has "Used image ..." lines
    # assert not captured.err
    assert captured.out.endswith(pulled)
    # check locally
    docker_ls_output = loop.run_until_complete(docker.images.list())
    local_images = parse_docker_ls_output(docker_ls_output)
    assert pulled in local_images

    loop.run_until_complete(docker.images.delete(pulled, force=True))
