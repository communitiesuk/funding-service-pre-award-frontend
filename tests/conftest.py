import multiprocessing
import platform

import pytest

from app import create_app

if platform.system() == "Darwin":
    multiprocessing.set_start_method("fork")  # Required on macOSX



@pytest.fixture(scope="session")
def app():
    """
    Returns an instance of the Flask app as a fixture for testing,
    which is available for the testing session and accessed with the
    @pytest.mark.uses_fixture('live_server')
    :return: An instance of the Flask app.
    """
    yield create_app()
