import httpx
import pytest

from app.services.olist_auth import OlistAuth
from app.services.olist_client import OlistClient
from app.services.token_store import TokenStore


class FakeMonotonic:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def sleeps() -> list[float]:
    return []


@pytest.fixture
def monotonic() -> FakeMonotonic:
    return FakeMonotonic()


@pytest.fixture
async def olist_client(settings, fake_olist, connected, sleeps, monotonic):
    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    async with httpx.AsyncClient(transport=fake_olist.transport) as http:
        auth = OlistAuth(settings, http, TokenStore(settings.tokens_file))
        yield OlistClient(settings, http, auth, sleep=fake_sleep, clock=monotonic)
