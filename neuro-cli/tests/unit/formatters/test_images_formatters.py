import time
from typing import Any

from neuro_sdk import (
    ImageCommitFinished,
    ImageCommitStarted,
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressSave,
    ImageProgressStep,
    LocalImage,
    RemoteImage,
)

from neuro_cli.formatters.images import DockerImageProgress

from tests.unit.conftest import NewConsole


class TestDockerImageProgress:
    def test_quiet_pull(self, rich_cmp: Any, new_console: NewConsole) -> None:
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

    def test_quiet_push(self, rich_cmp: Any, new_console: NewConsole) -> None:
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

    def test_quiet_save(self, rich_cmp: Any, new_console: NewConsole) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=True) as formatter:
            formatter.save(
                ImageProgressSave(
                    "job-id", RemoteImage.new_external_image(name="output")
                )
            )
            rich_cmp(console)

    def test_quiet_commit_started(self, rich_cmp: Any, new_console: NewConsole) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=True) as formatter:
            formatter.commit_started(
                ImageCommitStarted(
                    job_id="job-id", target_image=RemoteImage.new_external_image("img")
                )
            )
            rich_cmp(console)

    def test_quiet_commit_finished(
        self, rich_cmp: Any, new_console: NewConsole
    ) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=True) as formatter:
            formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
            rich_cmp(console)

    def test_no_tty_pull(self, rich_cmp: Any, new_console: NewConsole) -> None:
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

    def test_no_tty_push(self, rich_cmp: Any, new_console: NewConsole) -> None:
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

    def test_no_tty_save(self, rich_cmp: Any, new_console: NewConsole) -> None:
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

    def test_no_tty_commit_started(
        self, rich_cmp: Any, new_console: NewConsole
    ) -> None:
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

    def test_no_tty_commit_finished(
        self, rich_cmp: Any, new_console: NewConsole
    ) -> None:
        console = new_console(tty=False)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
            rich_cmp(console)

    def test_tty_pull(self, rich_cmp: Any, new_console: NewConsole) -> None:
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
            time.sleep(0.3)
            rich_cmp(console, index=1)
            formatter.step(ImageProgressStep("message2", "layer1", "status2", 30, 100))
            time.sleep(0.3)
            rich_cmp(console, index=2)

    def test_tty_push(self, rich_cmp: Any, new_console: NewConsole) -> None:
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
            time.sleep(0.3)
            rich_cmp(console, index=1)
            formatter.step(ImageProgressStep("message2", "layer1", "status2", 30, 100))
            time.sleep(0.3)
            rich_cmp(console, index=2)

    def test_tty_save(self, rich_cmp: Any, new_console: NewConsole) -> None:
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

    def test_tty_commit_started(self, rich_cmp: Any, new_console: NewConsole) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.commit_started(
                ImageCommitStarted(
                    job_id="job-id",
                    target_image=RemoteImage.new_external_image(name="img"),
                )
            )
            rich_cmp(console)

    def test_tty_commit_finished(self, rich_cmp: Any, new_console: NewConsole) -> None:
        console = new_console(tty=True)
        with DockerImageProgress.create(console, quiet=False) as formatter:
            formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
            rich_cmp(console)
