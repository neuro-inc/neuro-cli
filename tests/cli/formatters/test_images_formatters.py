from typing import Any

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
from neuromation.cli.formatters import DockerImageProgress
from neuromation.cli.printer import CSI


class TestDockerImageProgress:
    def test_quiet_pull(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.pull(
            ImageProgressPull(
                RemoteImage.new_external_image(name="input"), LocalImage("output")
            )
        )
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_quiet_push(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.push(
            ImageProgressPush(
                LocalImage("output"), RemoteImage.new_external_image(name="input")
            )
        )
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_quiet_save(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.save(
            ImageProgressSave("job-id", RemoteImage.new_external_image(name="output"))
        )
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_quiet_commit_started(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.commit_started(
            ImageCommitStarted(
                job_id="job-id", target_image=RemoteImage.new_external_image("img")
            )
        )
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_quiet_commit_finished(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=True)
        formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out == ""

    def test_no_tty_pull(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
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
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.step(ImageProgressStep("message2", "layer1"))

        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://test-cluster/bob/output:stream" in out
        assert "message1" not in out
        assert "message2" not in out
        assert CSI not in out

    def test_no_tty_push(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
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
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.step(ImageProgressStep("message2", "layer1"))

        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://test-cluster/bob/output:stream" in out
        assert "message1" not in out
        assert "message2" not in out
        assert CSI not in out

    def test_no_tty_save(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
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
        formatter.close()
        out, err = capfd.readouterr()
        assert (
            "Saving job 'job-id' to image 'image://test-cluster/bob/output:stream'"
            in out
        )
        assert err == ""

    def test_no_tty_commit_started(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
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
        formatter.close()
        out, err = capfd.readouterr()
        assert "Using remote image 'image://test-cluster/bob/output:stream'" in out
        assert f"Creating image from the job container..." in out
        assert err == ""

    def test_no_tty_commit_finished(self, capfd: Any) -> None:
        formatter = DockerImageProgress.create(tty=False, quiet=False)
        formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
        formatter.close()
        out, err = capfd.readouterr()
        assert out.startswith("Image created")
        assert err == ""

    def test_tty_pull(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
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
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.step(ImageProgressStep("message2", "layer1"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://test-cluster/bob/output:stream" in out
        assert "message1" in out
        assert "message2" in out
        assert CSI in out

    def test_tty_push(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
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
        formatter.step(ImageProgressStep("message1", "layer1"))
        formatter.step(ImageProgressStep("message2", "layer1"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "input:latest" in out
        assert "image://test-cluster/bob/output:stream" in out
        assert "message1" in out
        assert "message2" in out
        assert CSI in out

    def test_tty_save(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
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
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "job-id" in out
        assert "image://test-cluster/bob/output:stream" in out
        assert CSI in out

    def test_tty_commit_started(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
        formatter.commit_started(
            ImageCommitStarted(
                job_id="job-id", target_image=RemoteImage.new_external_image(name="img")
            )
        )
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert "img" in out
        assert CSI in out

    def test_tty_commit_finished(self, capfd: Any, click_tty_emulation: Any) -> None:
        formatter = DockerImageProgress.create(tty=True, quiet=False)
        formatter.commit_finished(ImageCommitFinished(job_id="job-id"))
        formatter.close()
        out, err = capfd.readouterr()
        assert err == ""
        assert out.startswith("Image created")
        assert CSI not in out  # no styled strings
