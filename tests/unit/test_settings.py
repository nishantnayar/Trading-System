"""
Unit tests for Settings Configuration
"""

from unittest.mock import patch

import pytest

import src.config.settings
from src.config.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _reset_singleton():
    src.config.settings._settings = None
    yield
    src.config.settings._settings = None


class TestSettingsDefaults:
    """Defaults apply when neither env vars nor a .env file are present"""

    def test_alpaca_defaults_empty(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(_env_file=None)
        assert settings.alpaca_api_key == ""
        assert settings.alpaca_secret_key == ""

    def test_smtp_defaults_none(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(_env_file=None)
        assert settings.smtp_host is None
        assert settings.smtp_port is None
        assert settings.smtp_username is None
        assert settings.smtp_password is None
        assert settings.smtp_from_email is None
        assert settings.smtp_to_email is None

    def test_prefect_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(_env_file=None)
        assert settings.prefect_api_url == "http://localhost:4200/api"
        assert settings.prefect_work_pool_data_ingestion == "data-ingestion-pool"


class TestSettingsFromEnvironment:
    """Environment variables override defaults"""

    def test_alpaca_from_env(self):
        env = {"ALPACA_API_KEY": "k", "ALPACA_SECRET_KEY": "s"}
        with patch.dict("os.environ", env, clear=True):
            settings = Settings(_env_file=None)
        assert settings.alpaca_api_key == "k"
        assert settings.alpaca_secret_key == "s"

    def test_smtp_from_env_parses_port(self):
        env = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "user@example.com",
            "SMTP_PASSWORD": "pw",
            "SMTP_FROM_EMAIL": "from@example.com",
            "SMTP_TO_EMAIL": "to@example.com",
        }
        with patch.dict("os.environ", env, clear=True):
            settings = Settings(_env_file=None)
        assert settings.smtp_host == "smtp.example.com"
        assert settings.smtp_port == 587
        assert settings.smtp_to_email == "to@example.com"

    def test_prefect_from_env(self):
        env = {
            "PREFECT_API_URL": "http://prefect:4200/api",
            "PREFECT_WORK_POOL_DATA_INGESTION": "custom-pool",
        }
        with patch.dict("os.environ", env, clear=True):
            settings = Settings(_env_file=None)
        assert settings.prefect_api_url == "http://prefect:4200/api"
        assert settings.prefect_work_pool_data_ingestion == "custom-pool"

    def test_case_insensitive_and_extra_ignored(self):
        env = {"alpaca_api_key": "lower", "SOME_UNKNOWN_VAR": "x"}
        with patch.dict("os.environ", env, clear=True):
            settings = Settings(_env_file=None)
        assert settings.alpaca_api_key == "lower"
        assert not hasattr(settings, "some_unknown_var")


class TestGetSettings:
    """get_settings() returns a cached module-level singleton"""

    def test_singleton(self):
        with patch.dict("os.environ", {}, clear=True):
            assert get_settings() is get_settings()

    def test_cached_instance_ignores_later_env_changes(self):
        with patch.dict("os.environ", {"ALPACA_API_KEY": "first"}, clear=True):
            first = get_settings()
        with patch.dict("os.environ", {"ALPACA_API_KEY": "second"}, clear=True):
            assert get_settings() is first
