from dataclasses import dataclass

import pytest

from app.core.config import get_settings
from app.services.auth_service import CurrentUser


@dataclass
class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def transaction(self):
        return FakeTransaction()


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def current_user() -> CurrentUser:
    return CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner")

