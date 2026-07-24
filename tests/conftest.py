import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def _set_test_env() -> None:
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("COINGLASS_API_KEY", "test-key")