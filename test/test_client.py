import pytest
from assistant.client import AssistantClient
from assistant.utils import get_message
from config.settings import BASE_URL


@pytest.mark.asyncio
async def test_client_session_and_send_message():
    """
    Basic integration test:
    - session initializes correctly
    - CSRF is fetched
    - message can be sent successfully
    """

    async with AssistantClient(
        base_url=BASE_URL,
        verify_ssl=False,
        debug=True,   # keep logs visible in test runs
    ) as client:

        result = await client.send_message(
            message="test message",
            route_name="website.home",
            history=[{"role": "user", "content": "test message"}],
        )

        # --- basic structure validation ---
        assert isinstance(result, dict)

        message = get_message(result)

        assert message is not None
        assert isinstance(message, str)
        assert len(message) > 0


@pytest.mark.asyncio
async def test_session_has_csrf_token():
    """
    Ensure CSRF token is properly initialized.
    """

    async with AssistantClient(
        base_url=BASE_URL,
        verify_ssl=False,
    ) as client:

        # private access for test (acceptable here)
        assert client._csrf_token is not None
        assert isinstance(client._csrf_token, str)
        assert len(client._csrf_token) > 10