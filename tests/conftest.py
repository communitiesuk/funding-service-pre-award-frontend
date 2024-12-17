import multiprocessing
import platform

import pytest

from app import create_app
from tests.authenticator_tests.testing.mocks.mocks.redis_magic_links import RedisMLinks
from tests.authenticator_tests.testing.mocks.mocks.redis_sessions import RedisSessions

if platform.system() == "Darwin":
    multiprocessing.set_start_method("fork")  # Required on macOSX


@pytest.fixture(scope="session")
def app(session_mocker):
    """
    Returns an instance of the Flask app as a fixture for testing,
    which is available for the testing session and accessed with the
    @pytest.mark.uses_fixture('live_server')
    :return: An instance of the Flask app.
    """
    session_mocker.patch("redis.Redis.get", RedisSessions.get)
    session_mocker.patch("redis.Redis.set", RedisSessions.set)
    session_mocker.patch("redis.Redis.delete", RedisSessions.delete)
    session_mocker.patch("redis.Redis.setex", RedisSessions.setex)
    session_mocker.patch("app.redis_mlinks.client_list", RedisMLinks.client_list)
    yield create_app()
