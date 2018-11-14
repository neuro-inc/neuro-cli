import pytest

from neuromation import Resources
from neuromation.cli.command_handlers import ModelHandlerOperations
from neuromation.client import Image
from neuromation.client.jobs import NetworkPortForwarding


@pytest.fixture()
def alice_model():
    return ModelHandlerOperations("alice")


@pytest.mark.asyncio
class TestNormalCases:
    async def test_model_submit(self, alice_model, partial_mocked_model):
        partial_mocked_model().patch("train", None)
        await alice_model.train(
            "ubuntu:tf_2.0_beta",
            "storage:///data/set.txt",
            "storage://~/results/result1.txt",
            0,
            None,
            1,
            100,
            False,
            "",
            partial_mocked_model,
            http=None,
            ssh=None,
            description="test model",
        )
        partial_mocked_model().train.assert_called_once()
        partial_mocked_model().train.assert_called_with(
            image=Image(image="ubuntu:tf_2.0_beta", command=""),
            resources=Resources(memory=100, gpu=0, cpu=1.0, shm=False, gpu_model=None),
            network=None,
            dataset=f"storage://alice/data/set.txt",
            results=f"storage://alice/results/result1.txt",
            description="test model",
        )

    async def test_model_submit_with_gpu_model(self, alice_model, partial_mocked_model):
        partial_mocked_model().patch("train", None)
        await alice_model.train(
            "ubuntu:tf_2.0_beta",
            "storage:///data/set.txt",
            "storage://~/results/result1.txt",
            1,
            "nvidia-tesla-p4",
            1,
            100,
            False,
            "",
            partial_mocked_model,
            http=None,
            ssh=None,
            description="blah blah blah",
        )
        partial_mocked_model().train.assert_called_once()
        partial_mocked_model().train.assert_called_with(
            image=Image(image="ubuntu:tf_2.0_beta", command=""),
            resources=Resources(
                memory=100, gpu=1, cpu=1.0, shm=False, gpu_model="nvidia-tesla-p4"
            ),
            network=None,
            dataset=f"storage://alice/data/set.txt",
            results=f"storage://alice/results/result1.txt",
            description="blah blah blah",
        )

    async def test_model_submit_no_cmd(self, alice_model, partial_mocked_model):
        partial_mocked_model().patch("train", None)
        await alice_model.train(
            "ubuntu:tf_2.0_beta",
            "storage:///data/set.txt",
            "storage://~/results/result1.txt",
            0,
            None,
            1,
            100,
            False,
            None,
            partial_mocked_model,
            http=None,
            ssh=None,
            description="woo hoo!",
        )
        partial_mocked_model().train.assert_called_once()
        partial_mocked_model().train.assert_called_with(
            image=Image(image="ubuntu:tf_2.0_beta", command=None),
            resources=Resources(memory=100, gpu=0, cpu=1.0, shm=False, gpu_model=None),
            network=None,
            dataset=f"storage://alice/data/set.txt",
            results=f"storage://alice/results/result1.txt",
            description="woo hoo!",
        )

    async def test_model_submit_with_http(self, alice_model, partial_mocked_model):
        partial_mocked_model().patch("train", None)
        await alice_model.train(
            "ubuntu:tf_2.0_beta",
            "storage:///data/set.txt",
            "storage://~/results/result1.txt",
            0,
            None,
            1,
            100,
            False,
            "",
            partial_mocked_model,
            http=8888,
            ssh=None,
            description="hooray",
        )
        partial_mocked_model().train.assert_called_once()
        partial_mocked_model().train.assert_called_with(
            image=Image(image="ubuntu:tf_2.0_beta", command=""),
            resources=Resources(memory=100, gpu=0, cpu=1.0, shm=False, gpu_model=None),
            network=NetworkPortForwarding({"http": 8888}),
            dataset=f"storage://alice/data/set.txt",
            results=f"storage://alice/results/result1.txt",
            description="hooray",
        )

    async def test_model_submit_with_ssh(self, alice_model, partial_mocked_model):
        partial_mocked_model().patch("train", None)
        await alice_model.train(
            "ubuntu:tf_2.0_beta",
            "storage:///data/set.txt",
            "storage://~/results/result1.txt",
            0,
            None,
            1,
            100,
            False,
            "",
            partial_mocked_model,
            http=None,
            ssh=8888,
            description="la vita è bella",
        )
        partial_mocked_model().train.assert_called_once()
        partial_mocked_model().train.assert_called_with(
            image=Image(image="ubuntu:tf_2.0_beta", command=""),
            resources=Resources(memory=100, gpu=0, cpu=1.0, shm=False, gpu_model=None),
            network=NetworkPortForwarding({"ssh": 8888}),
            dataset=f"storage://alice/data/set.txt",
            results=f"storage://alice/results/result1.txt",
            description="la vita è bella",
        )

    async def test_model_submit_with_ssh_and_http(
        self, alice_model, partial_mocked_model
    ):
        partial_mocked_model().patch("train", None)
        await alice_model.train(
            "ubuntu:tf_2.0_beta",
            "storage:///data/set.txt",
            "storage://~/results/result1.txt",
            0,
            None,
            1,
            100,
            False,
            "",
            partial_mocked_model,
            http=7878,
            ssh=8888,
            description="la-la-la",
        )
        partial_mocked_model().train.assert_called_once()
        partial_mocked_model().train.assert_called_with(
            image=Image(image="ubuntu:tf_2.0_beta", command=""),
            resources=Resources(memory=100, gpu=0, cpu=1.0, shm=False, gpu_model=None),
            network=NetworkPortForwarding({"ssh": 8888, "http": 7878}),
            dataset=f"storage://alice/data/set.txt",
            results=f"storage://alice/results/result1.txt",
            description="la-la-la",
        )

    async def test_model_submit_wrong_src(self, alice_model, partial_mocked_model):
        with pytest.raises(ValueError):
            partial_mocked_model().patch("train", None)
            await alice_model.train(
                "ubuntu:tf_2.0_beta",
                "/data/set.txt",
                "storage://~/results/result1.txt",
                0,
                None,
                1,
                100,
                False,
                "",
                partial_mocked_model,
                http=None,
                ssh=None,
                description="la-la-la",
            )
        assert partial_mocked_model().train.call_count == 0

    async def test_model_submit_wrong_dst(self, alice_model, partial_mocked_model):
        partial_mocked_model().patch("train", None)
        with pytest.raises(ValueError):
            await alice_model.train(
                "ubuntu:tf_2.0_beta",
                "storage://~/data/set.txt",
                "http://results/result1.txt",
                0,
                None,
                1,
                100,
                False,
                "",
                partial_mocked_model,
                http=None,
                ssh=None,
                description="la-la-la",
            )
        assert partial_mocked_model().train.call_count == 0
