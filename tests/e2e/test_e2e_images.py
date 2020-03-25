import asyncio
import re
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, AsyncIterator, Set
from uuid import uuid4 as uuid

import aiodocker
import pytest
from yarl import URL

from neuromation.api import CONFIG_ENV_NAME, DEFAULT_CONFIG_PATH, JobStatus
from tests.e2e import Helper
from tests.e2e.utils import JOB_TINY_CONTAINER_PARAMS


TEST_IMAGE_NAME = "e2e-banana-image"


def parse_docker_ls_output(docker_ls_output: Any) -> Set[str]:
    return set(
        repo_tag
        for info in docker_ls_output
        if info["RepoTags"] is not None
        for repo_tag in info["RepoTags"]
        if repo_tag
    )


@pytest.fixture()
def tag() -> str:
    return str(uuid())


async def generate_image(docker: aiodocker.Docker, tag: str) -> str:
    image_archive = Path(__file__).parent / "assets/echo-tag.tar"
    # TODO use random image name here
    image_name = f"{TEST_IMAGE_NAME}:{tag}"
    with image_archive.open(mode="r+b") as fileobj:
        result = await docker.images.build(
            fileobj=fileobj, tag=image_name, buildargs={"TAG": tag}, encoding="identity"
        )
        print(result)

    return image_name


@pytest.fixture()
async def image(
    loop: asyncio.AbstractEventLoop, docker: aiodocker.Docker, tag: str
) -> AsyncIterator[str]:
    image = await generate_image(docker, tag)
    yield image
    await docker.images.delete(image, force=True)


@pytest.mark.e2e
def test_images_complete_lifecycle(
    helper: Helper,
    image: str,
    tag: str,
    loop: asyncio.AbstractEventLoop,
    docker: aiodocker.Docker,
) -> None:
    # Let`s push image
    captured = helper.run_cli(["image", "push", image])

    # stderr has "Used image ..." lines
    # assert not captured.err

    image_full_str = f"image://{helper.cluster_name}/{helper.username}/{image}"
    assert captured.out.endswith(image_full_str)
    image_url = URL(image_full_str)

    # Check if image available on registry
    captured = helper.run_cli(["image", "ls", "--full-uri"])

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
    captured = helper.run_cli(["image", "pull", f"image:{image}"])
    # stderr has "Used image ..." lines
    # assert not captured.err
    assert captured.out.endswith(image)

    # check pulled locally, delete for cleanup
    docker_ls_output = loop.run_until_complete(docker.images.list())
    local_images = parse_docker_ls_output(docker_ls_output)
    assert image in local_images

    # Execute image and check result
    captured = helper.run_cli(
        [
            "-q",
            "submit",
            *JOB_TINY_CONTAINER_PARAMS,
            "--non-preemptible",
            "--no-wait-start",
            str(image_url),
        ]
    )
    assert not captured.err
    job_id = captured.out
    assert job_id.startswith("job-")
    helper.wait_job_change_state_to(job_id, JobStatus.SUCCEEDED, JobStatus.FAILED)

    helper.check_job_output(job_id, re.escape(tag))


@pytest.mark.e2e
def test_image_tags(helper: Helper, image: str, tag: str) -> None:
    # push image
    captured = helper.run_cli(["image", "push", image])

    image_full_str = f"image://{helper.cluster_name}/{helper.username}/{image}"
    assert captured.out.endswith(image_full_str)

    # check the tag is present now
    image_full_str_no_tag = image_full_str.replace(f":{tag}", "")
    captured = helper.run_cli(["image", "tags", image_full_str_no_tag])
    assert tag in captured.out

    cmd = f"neuro image tags {image_full_str}"
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    assertion_msg = f"Command {cmd} should fail: {result.stdout!r} {result.stderr!r}"
    assert result.returncode, assertion_msg

    image_full_str_latest_tag = image_full_str.replace(f":{tag}", ":latest")
    cmd = f"neuro image tags {image_full_str_latest_tag}"
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    assertion_msg = f"Command {cmd} should fail: {result.stdout!r} {result.stderr!r}"
    assert result.returncode, assertion_msg


@pytest.mark.e2e
def test_image_ls(helper: Helper, image: str, tag: str) -> None:
    # push image
    captured = helper.run_cli(["image", "push", image])

    image_full_str = f"image://{helper.cluster_name}/{helper.username}/{image}"
    image_short_str = f"image:{image}"
    assert captured.out.endswith(image_full_str)

    image_full_str_no_tag = image_full_str.replace(f":{tag}", "")
    image_short_str_no_tag = image_short_str.replace(f":{tag}", "")

    # check ls short mode
    captured = helper.run_cli(["image", "ls"])
    assert image_short_str_no_tag in captured.out.splitlines()

    captured = helper.run_cli(["image", "ls", "--full-uri"])
    assert image_full_str_no_tag in captured.out.splitlines()

    # check ls long mode
    captured = helper.run_cli(["image", "ls", "-l"])
    matching_lines = [
        line
        for line in captured.out.splitlines()
        if image_short_str_no_tag == line.split()[0]
    ]
    assert len(matching_lines) == 1

    image_full_https_str_no_tag = f"/{helper.username}/{image}".replace(f":{tag}", "")
    actual_https_url = urllib.parse.urlparse(matching_lines[0].split()[1])
    assert actual_https_url.scheme == "https"
    assert actual_https_url.path == image_full_https_str_no_tag

    captured = helper.run_cli(["image", "ls", "-l", "--full-uri"])
    matching_lines = [
        line
        for line in captured.out.splitlines()
        if image_full_str_no_tag == line.split()[0]
    ]
    assert len(matching_lines) == 1


@pytest.mark.e2e
def test_images_push_with_specified_name(
    helper: Helper,
    image: str,
    tag: str,
    loop: asyncio.AbstractEventLoop,
    docker: aiodocker.Docker,
) -> None:
    # Let`s push image
    image_no_tag = image.replace(f":{tag}", "")
    pushed_no_tag = f"{image_no_tag}-pushed"
    pulled_no_tag = f"{image_no_tag}-pulled"
    pulled = f"{pulled_no_tag}:{tag}"

    captured = helper.run_cli(["image", "push", image, f"image:{pushed_no_tag}:{tag}"])
    # stderr has "Used image ..." lines
    # assert not captured.err
    image_pushed_full_str = (
        f"image://{helper.cluster_name}/{helper.username}/{pushed_no_tag}:{tag}"
    )
    assert captured.out.endswith(image_pushed_full_str)
    image_url_without_tag = image_pushed_full_str.replace(f":{tag}", "")

    # Check if image available on registry
    captured = helper.run_cli(["image", "ls", "--full-uri"])
    image_urls = captured.out.splitlines()
    assert image_url_without_tag in image_urls

    # check locally
    docker_ls_output = loop.run_until_complete(docker.images.list())
    local_images = parse_docker_ls_output(docker_ls_output)
    assert pulled not in local_images

    # Pull image as with another name
    captured = helper.run_cli(["image", "pull", f"image:{pushed_no_tag}:{tag}", pulled])
    # stderr has "Used image ..." lines
    # assert not captured.err
    assert captured.out.endswith(pulled)
    # check locally
    docker_ls_output = loop.run_until_complete(docker.images.list())
    local_images = parse_docker_ls_output(docker_ls_output)
    assert pulled in local_images

    # TODO (A.Yushkovskiy): delete the pushed image in GCR
    # delete locally
    loop.run_until_complete(docker.images.delete(pulled, force=True))


@pytest.mark.e2e
def test_docker_helper(
    helper: Helper, image: str, tag: str, nmrc_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv(CONFIG_ENV_NAME, str(nmrc_path or DEFAULT_CONFIG_PATH))
    helper.run_cli(["config", "docker"])
    registry = helper.registry_url.host
    username = helper.username
    full_tag = f"{registry}/{username}/{image}"
    tag_cmd = f"docker tag {image} {full_tag}"
    result = subprocess.run(
        tag_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    assert (
        not result.returncode
    ), f"Command {tag_cmd} failed: {result.stdout!r} {result.stderr!r} "
    push_cmd = f"docker push {full_tag}"
    result = subprocess.run(
        push_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    assert (
        not result.returncode
    ), f"Command {push_cmd} failed: {result.stdout!r} {result.stderr!r} "
    # Run image and check output
    image_url = f"image://{helper.cluster_name}/{username}/{image}"
    job_id = helper.run_job_and_wait_state(
        image_url, "", wait_state=JobStatus.SUCCEEDED, stop_state=JobStatus.FAILED
    )
    helper.check_job_output(job_id, re.escape(tag))
