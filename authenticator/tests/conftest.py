import pytest
from flask import current_app
from testing.mocks.mocks import *  # noqa

from app import create_app
from authenticator.models.account import AccountMethods


@pytest.fixture
def app_context():
    with create_app().app_context():
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
