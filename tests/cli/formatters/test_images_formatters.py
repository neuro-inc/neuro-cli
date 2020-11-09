import time
from typing import Any

from rich.console import Console

from neuromation.api import (
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressStep,
    LocalImage,
    RemoteImage,
)
from neuromation.api.abc import (
    ImageCommitFinished,
    ImageCommitStarted,
    ImageProgressSave,
)
from neuromation.cli.formatters.images import DockerImageProgress


def new_console(tty: bool, color: bool = True) -> Console:
    # console doesn't accept the time source,
    # using the real time in tests is not reliable
    return Console(
        width=160,
        height=24,
        force_terminal=tty,
        color_system="auto" if color else None,
        record=True,
        highlighter=None,
        legacy_windows=False,
        log_path=False,
        log_time=False,
    )


class TestDockerImageProgress:
    def test_quiet_pull(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=True) as formatter:
            formatter.pull(
                ImageProgressPull(
                    RemoteImage.new_external_image(name="input"), LocalImage("output")
                )
            )
            rich_cmp(console, index=0)
            formatter.step(ImageProgressStep("message1", "layer1", "status", 1, 100))
            rich_cmp(console, index=1)

    def test_quiet_push(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=True) as formatter:
            formatter.push(
                ImageProgressPush(
                    LocalImage("output"), RemoteImage.new_external_image(name="input")
                )
            )
            rich_cmp(console, index=0)
            formatter.step(ImageProgressStep("message1", "layer1", "status", 1, 100))
            rich_cmp(console, index=1)

    def test_quiet_save(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=True) as formatter:
            formatter.save(
                ImageProgressSave(
                    "job-id", RemoteImage.new_external_image(name="output")
                )
            )
            rich_cmp(console)

    def test_quiet_commit_started(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=True) as formatter:
            formatter.commit_started(
                ImageCommitStarted(
                    job_id="job-id", target_image=RemoteImage.new_external_image("img")
                )
            )
            rich_cmp(console)

    def test_quiet_commit_finished(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=True) as formatter:
            formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
            rich_cmp(console)

    def test_no_tty_pull(self, rich_cmp: Any) -> None:
        console = new_console(tty=False)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.pull(
                ImageProgressPull(
                    RemoteImage.new_neuro_image(
                        name="output",
                        tag="stream",
                        owner="bob",
                        registry="https://registry-dev.neu.ro",
                        cluster_name="test-cluster",
                    ),
                    LocalImage("input", "latest"),
                )
            )
            rich_cmp(console, index=0)
            formatter.step(ImageProgressStep("message1", "layer1", "status1", 1, 100))
            rich_cmp(console, index=1)
            formatter.step(ImageProgressStep("message2", "layer1", "status2", 30, 100))
            rich_cmp(console, index=2)

    def test_no_tty_push(self, rich_cmp: Any) -> None:
        console = new_console(tty=False)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.push(
                ImageProgressPush(
                    LocalImage("input", "latest"),
                    RemoteImage.new_neuro_image(
                        name="output",
                        tag="stream",
                        owner="bob",
                        registry="https://registry-dev.neu.ro",
                        cluster_name="test-cluster",
                    ),
                )
            )
            rich_cmp(console, index=0)
            formatter.step(ImageProgressStep("message1", "layer1", "status1", 1, 100))
            rich_cmp(console, index=1)
            formatter.step(ImageProgressStep("message2", "layer1", "status2", 30, 100))
            rich_cmp(console, index=2)

    def test_no_tty_save(self, rich_cmp: Any) -> None:
        console = new_console(tty=False)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.save(
                ImageProgressSave(
                    "job-id",
                    RemoteImage.new_neuro_image(
                        name="output",
                        tag="stream",
                        owner="bob",
                        registry="https://registry-dev.neu.ro",
                        cluster_name="test-cluster",
                    ),
                )
            )
            rich_cmp(console)

    def test_no_tty_commit_started(self, rich_cmp: Any) -> None:
        console = new_console(tty=False)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.commit_started(
                ImageCommitStarted(
                    job_id="job-id",
                    target_image=RemoteImage.new_neuro_image(
                        name="output",
                        tag="stream",
                        owner="bob",
                        registry="https://registry-dev.neu.ro",
                        cluster_name="test-cluster",
                    ),
                )
            )
            rich_cmp(console)

    def test_no_tty_commit_finished(self, rich_cmp: Any) -> None:
        console = new_console(tty=False)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
            rich_cmp(console)

    def test_tty_pull(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.pull(
                ImageProgressPull(
                    RemoteImage.new_neuro_image(
                        name="output",
                        tag="stream",
                        owner="bob",
                        registry="https://registry-dev.neu.ro",
                        cluster_name="test-cluster",
                    ),
                    LocalImage("input", "latest"),
                )
            )
            rich_cmp(console, index=0)
            formatter.step(ImageProgressStep("message1", "layer1", "status1", 1, 100))
            time.sleep(0.1)
            rich_cmp(console, index=1)
            formatter.step(ImageProgressStep("message2", "layer1", "status2", 30, 100))
            time.sleep(0.1)
            rich_cmp(console, index=2)

    def test_tty_push(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.push(
                ImageProgressPush(
                    LocalImage("input", "latest"),
                    RemoteImage.new_neuro_image(
                        name="output",
                        tag="stream",
                        owner="bob",
                        registry="https://registry-dev.neu.ro",
                        cluster_name="test-cluster",
                    ),
                )
            )
            rich_cmp(console, index=0)
            formatter.step(ImageProgressStep("message1", "layer1", "status1", 1, 100))
            time.sleep(0.1)
            rich_cmp(console, index=1)
            formatter.step(ImageProgressStep("message2", "layer1", "status2", 30, 100))
            time.sleep(0.1)
            rich_cmp(console, index=2)

    def test_tty_save(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.save(
                ImageProgressSave(
                    "job-id",
                    RemoteImage.new_neuro_image(
                        name="output",
                        tag="stream",
                        owner="bob",
                        registry="https://registry-dev.neu.ro",
                        cluster_name="test-cluster",
                    ),
                )
            )
            rich_cmp(console)

    def test_tty_commit_started(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.commit_started(
                ImageCommitStarted(
                    job_id="job-id",
                    target_image=RemoteImage.new_external_image(name="img"),
                )
            )
            rich_cmp(console)

    def test_tty_commit_finished(self, rich_cmp: Any) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
            rich_cmp(console)
