from contextlib import contextmanager
from typing import Any, Generator

import jwt as jwt
import pytest
from flask import current_app
from flask.sessions import SessionMixin
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from authenticator.models.account import AccountMethods
from config.envs.unit_test import UnitTestConfig
from tests.authenticator_tests.testing.mocks.mocks import *  # noqa


@pytest.fixture
def app_context(app):
    with app.app_context():
        with current_app.test_request_context():
            yield


@pytest.fixture(scope="function")
def create_magic_link(mocker):
    from authenticator.models.fund import Fund
    from authenticator.models.round import Round

    mocker.patch(
        "authenticator.models.account.FundMethods.get_fund",
        return_value=Fund(
            name="test fund", fund_title="hello", short_name="COF", identifier="asdfasdf", description="asdfasdfasdf"
        ),
    )
    mocker.patch("authenticator.models.account.get_round_data", return_value=Round(contact_email="asdf@asdf.com"))
    mocker.patch("authenticator.models.account.Notification.send", return_value=True)
    auth_landing = AccountMethods.get_magic_link("a@example.com", "cof", "r1w1")
    link_key_end = auth_landing.index("?fund=")
    link_key = auth_landing[link_key_end - 8 : link_key_end]  # noqa:E203
    yield link_key


class _AuthenticatorFlaskClient(FlaskClient):
    def open(
        self,
        *args: Any,
        buffered: bool = False,
        follow_redirects: bool = False,
        **kwargs: Any,
    ) -> TestResponse:
        if "headers" in kwargs:
            kwargs["headers"].setdefault("Host", UnitTestConfig.AUTH_HOST)
        else:
            kwargs.setdefault("headers", {"Host": UnitTestConfig.AUTH_HOST})
        return super().open(*args, buffered=buffered, follow_redirects=follow_redirects, **kwargs)

    def set_cookie(
        self,
        key: str,
        value: str = "",
        *,
        domain: str | None = None,
        origin_only: bool = True,
        path: str = "/",
        **kwargs: Any,
    ) -> None:
        if domain is None:
            domain = self.application.config["COOKIE_DOMAIN"]
        super().set_cookie(key=key, value=value, domain=domain, origin_only=origin_only, path=path, **kwargs)

    @contextmanager
    def session_transaction(self, *args: Any, **kwargs: Any) -> Generator[SessionMixin, None, None]:
        if "headers" in kwargs:
            kwargs["headers"].setdefault("Host", UnitTestConfig.AUTH_HOST)
        else:
            kwargs.setdefault("headers", {"Host": UnitTestConfig.AUTH_HOST})
        with super().session_transaction(*args, **kwargs) as sess:
            yield sess


@pytest.fixture()
def flask_test_client(app, user_token=None):
    """
    Creates the test client we will be using to test the responses
    from our app, this is a test fixture.
    :return: A flask test client.
    """

    app.test_client_class = _AuthenticatorFlaskClient

    with app.app_context() as app_context:
        with app_context.app.test_client() as test_client:
            yield test_client
