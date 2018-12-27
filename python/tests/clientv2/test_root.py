from neuromation.clientv2 import ClientV2


async def test_client_username():
    async with ClientV2("http://example.com", "user", "token") as client:
        assert client.username == "user"
