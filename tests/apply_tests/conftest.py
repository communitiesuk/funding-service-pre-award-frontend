import multiprocessing
import platform
from typing import Any

import pytest
from flask import template_rendered
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app import create_app
from apply.models.fund import Fund
from config.envs.unit_test import UnitTestConfig
from tests.apply_tests.api_data.test_data import TEST_FUNDS_DATA, TEST_ROUNDS_DATA


@pytest.fixture
def mock_login(monkeypatch):
    monkeypatch.setattr(
        "fsd_utils.authentication.decorators._check_access_token",
        lambda return_app: {
            "accountId": "test-user",
            "fullName": "Test User",
            "email": "test-user@test.com",
            "roles": [],
        },
    )


class _ApplyFlaskClient(FlaskClient):
    def open(
        self,
        *args: Any,
        buffered: bool = False,
        follow_redirects: bool = False,
        **kwargs: Any,
    ) -> TestResponse:
        if "headers" in kwargs:
            kwargs["headers"].setdefault("Host", UnitTestConfig.APPLY_HOST)
        else:
            kwargs.setdefault("headers", {"Host": UnitTestConfig.APPLY_HOST})
        return super().open(*args, buffered=buffered, follow_redirects=follow_redirects, **kwargs)


@pytest.fixture()
def apply_test_client(app):
    """
    Creates the test client we will be using to test the responses
    from our app, this is a test fixture.
    :return: A flask test client.
    """
    app.test_client_class = _ApplyFlaskClient
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(scope="function")
def templates_rendered(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


@pytest.fixture(autouse=True)
def mock_get_fund_round(mocker):
    mocker.patch(
        "apply.default.account_routes.get_all_funds",
        return_value=TEST_FUNDS_DATA,
    )
    mocker.patch(
        "apply.default.account_routes.get_all_rounds_for_fund",
        return_value=TEST_ROUNDS_DATA,
    )
    mocker.patch(
        "apply.helpers.get_round_data_by_short_names",
        return_value=TEST_ROUNDS_DATA[0],
    )
    mocker.patch(
        "apply.helpers.get_fund_data_by_short_name",
        return_value=Fund.from_dict(TEST_FUNDS_DATA[0]),
    )
    mocker.patch(
        "apply.default.routes.get_all_fund_short_names",
        return_value=["COF", "NSTF"],
    )
    mocker.patch(
        "apply.helpers.get_all_fund_short_names",
        return_value=["COF", "NSTF"],
    )
    mocker.patch(
        "apply.helpers.get_default_round_for_fund",
        return_value=TEST_ROUNDS_DATA[0],
    )
    mocker.patch(
        "apply.default.application_routes.get_round_data",
        return_value=TEST_ROUNDS_DATA[0],
    )
    mocker.patch(
        "apply.default.application_routes.get_fund_data",
        return_value=Fund.from_dict(TEST_FUNDS_DATA[0]),
    )
    mocker.patch(
        "apply.default.data.get_round_data_fail_gracefully",
        return_value=TEST_ROUNDS_DATA[0],
    )
    mocker.patch("apply.default.account_routes.get_lang", return_value="en")
    mocker.patch(
        "apply.default.application_routes.get_fund_and_round",
        return_value=(Fund.from_dict(TEST_FUNDS_DATA[0]), TEST_ROUNDS_DATA[0]),
    )
