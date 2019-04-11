async def test_client_username(make_client):
    async with make_client("http://example.com") as client:
        assert client.username == "user"
