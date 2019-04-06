from neuromation.api import Client


async def test_client_username(token):
    async with Client("http://example.com", token) as client:
        assert client.username == "user"
