from neuromation.clientv2 import ClientV2


async def test_client_username(token):
    async with ClientV2("http://example.com", token) as client:
        assert client.username == "user"
