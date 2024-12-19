import typing as t
from collections import OrderedDict
from contextlib import contextmanager
from distutils.util import strtobool
from pathlib import Path
from typing import Any
from unittest import mock

import jwt as jwt
import pytest
import werkzeug
from flask import template_rendered
from flask.sessions import SessionMixin
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app import create_app
from assess.assessments.models.round_status import RoundStatus
from assess.services.models.assessor_task_list import AssessorTaskList
from assess.shared.helpers import get_ttl_hash
from assess.tagging.models.tag import AssociatedTag, Tag, TagType
from config import Config
from config.envs.unit_test import UnitTestConfig
from tests.assess_tests.api_data.example_get_full_application import mock_full_application_json
from tests.assess_tests.api_data.test_data import fund_specific_claim_map, mock_api_results
from tests.assess_tests.test_tags import associated_tag, test_get_tag, test_tags_active, test_tags_inactive

test_lead_assessor_claims = {
    "accountId": "lead",
    "email": "lead@test.com",
    "fullName": "Test User",
    "roles": ["TF_LEAD_ASSESSOR", "TF_ASSESSOR", "TF_COMMENTER"],
}

test_assessor_claims = {
    "accountId": "assessor",
    "email": "assessor@test.com",
    "fullName": "Test User",
    "roles": ["TF_ASSESSOR", "TF_COMMENTER"],
}

test_commenter_claims = {
    "accountId": "commenter",
    "email": "commenter@test.com",
    "fullName": "Test User",
    "roles": ["TF_COMMENTER"],
}

test_roleless_user_claims = {
    "accountId": "test-user",
    "email": "test@example.com",
    "fullName": "Test User",
    "roles": [],
}


def create_valid_token(payload=test_assessor_claims):
    _test_private_key_path = str(Path(__file__).parent.parent) + "/keys/rsa256/private.pem"
    with open(_test_private_key_path, mode="rb") as private_key_file:
        rsa256_private_key = private_key_file.read()

        return jwt.encode(payload, rsa256_private_key, algorithm="RS256")


def create_invalid_token():
    _test_private_key_path = str(Path(__file__).parent.parent) + "/keys/rsa256/private_invalid.pem"
    with open(_test_private_key_path, mode="rb") as private_key_file:
        rsa256_private_key = private_key_file.read()

        return jwt.encode(test_assessor_claims, rsa256_private_key, algorithm="RS256")


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


class _AssessFlaskClient(FlaskClient):
    def open(
        self,
        *args: Any,
        buffered: bool = False,
        follow_redirects: bool = False,
        **kwargs: Any,
    ) -> TestResponse:
        if "headers" in kwargs:
            kwargs["headers"].setdefault("Host", UnitTestConfig.ASSESS_HOST)
        else:
            kwargs.setdefault("headers", {"Host": UnitTestConfig.ASSESS_HOST})
        return super().open(*args, buffered=buffered, follow_redirects=follow_redirects, **kwargs)

    def set_cookie(
        self,
        key: str,
        value: str = "",
        *,
        domain: str | None = None,
        origin_only: bool = False,
        path: str = "/",
        **kwargs: t.Any,
    ) -> None:
        if domain is None:
            domain = self.application.config["ASSESS_HOST"]
        super().set_cookie(key, value, domain=domain, origin_only=origin_only, path=path, **kwargs)

    @contextmanager
    def session_transaction(self, *args: t.Any, **kwargs: t.Any) -> t.Generator[SessionMixin, None, None]:
        if "headers" in kwargs:
            kwargs["headers"].setdefault("Host", UnitTestConfig.ASSESS_HOST)
        else:
            kwargs.setdefault("headers", {"Host": UnitTestConfig.ASSESS_HOST})
        with super().session_transaction(*args, **kwargs) as sess:
            yield sess


@pytest.fixture(scope="function")
def assess_test_client(app, user_token=None):
    """
    Creates the test client we will be using to test the responses
    from our app, this is a test fixture.
    :return: A flask test client.
    """
    app.test_client_class = _AssessFlaskClient
    with app.test_client() as test_client:
        test_client.set_cookie(
            "fsd_user_token",
            user_token or create_valid_token(),
        )
        yield test_client


def resolve_redirect_path(self, response, buffered=False):
    # Custom logic here
    response.request.environ["wsgi.input"].seek(0)

    # Call the original resolve_redirect method
    return self._original_resolve_redirect(response, buffered=buffered)


@pytest.fixture
def patch_resolve_redirect():
    # Store the original resolve_redirect method
    werkzeug.test.Client._original_resolve_redirect = werkzeug.test.Client.resolve_redirect

    # Patch the resolve_redirect method with resolve_redirect_path
    with mock.patch.object(werkzeug.test.Client, "resolve_redirect", new=resolve_redirect_path):
        yield


@pytest.fixture(scope="function")
def flask_test_maintenance_client(request, user_token=None):
    """
    Creates the test maintenance client we will be using to test the responses
    from our app, this is a test fixture.
    :return: A flask test client.
    """
    marker = request.node.get_closest_marker("maintenance_mode")
    maintenance_mode = marker.args[0]
    app = create_app()
    app.test_client_class = _AssessFlaskClient
    app.config.update({"MAINTENANCE_MODE": strtobool(maintenance_mode)})
    with app.test_client() as test_client:
        test_client.set_cookie(
            "fsd_user_token",
            user_token or create_valid_token(),
        )
        yield test_client


@pytest.fixture(scope="function")
def mock_get_sub_criteria_banner_state(request):
    from assess.services.models.banner import Banner

    marker = request.node.get_closest_marker("application_id")
    application_id = marker.args[0]

    mock_banner_info = Banner.from_filtered_dict(
        mock_api_results[f"assessment_store/sub_criteria_overview/banner_state/{application_id}"]
    )

    with (
        mock.patch(
            "assess.flagging.helpers.get_sub_criteria_banner_state",
            return_value=mock_banner_info,
        ),
        mock.patch(
            "assess.flagging.routes.get_sub_criteria_banner_state",
            return_value=mock_banner_info,
        ),
    ):
        yield


@pytest.fixture(scope="function")
def mock_get_fund(mocker):
    from assess.services.models.fund import Fund

    mock_fund_info = Fund.from_json(mock_api_results["fund_store/funds/{fund_id}"])

    mock_funcs = [
        "assess.assessments.routes.get_fund",
        "assess.authentication.validation.get_fund",
        "assess.flagging.helpers.get_fund",
        "assess.tagging.routes.get_fund",
        "assess.services.shared_data_helpers.get_fund",
    ]

    for mock_func in mock_funcs:
        (mocker.patch(mock_func, return_value=mock_fund_info),)

    mocker.patch(
        "assess.authentication.validation.determine_round_status",
        return_value=RoundStatus(False, False, True, True, True, False),
    )

    yield


@pytest.fixture(scope="function")
def mock_get_funds():
    from assess.services.models.fund import Fund

    mock_fund_info = [
        Fund.from_json(mock_api_results["fund_store/funds/{fund_id}"]),
        Fund.from_json(mock_api_results["fund_store/funds/NSTF"]),
        Fund.from_json(mock_api_results["fund_store/funds/CYP"]),
        Fund.from_json(mock_api_results["fund_store/funds/COF"]),
        Fund.from_json(mock_api_results["fund_store/funds/DPIF"]),
    ]

    with (
        mock.patch(
            "assess.assessments.routes.get_funds",
            return_value=mock_fund_info,
        ),
        mock.patch(
            "assess.authentication.auth.get_funds",
            return_value=mock_fund_info,
        ),
    ):
        yield


@pytest.fixture(scope="function")
def mock_get_application_metadata(mocker):
    mocker.patch(
        "assess.authentication.validation.get_application_metadata",
        return_value=mock_api_results["assessment_store/applications/{application_id}"],
    )
    yield


@pytest.fixture
def mocks_for_file_export_download(mocker):
    mocker.patch(
        "assess.assessments.routes.get_application_sections_display_config",
        return_value=[],
    )

    mocker.patch(
        "assess.assessments.routes.generate_maps_from_form_names",
        return_value=COF_R2_W2_GENERATE_MAPS_FROM_FORM_NAMES,
    )

    mocker.patch(
        "assess.assessments.helpers.generate_maps_from_form_names",
        return_value=COF_R2_W2_GENERATE_MAPS_FROM_FORM_NAMES,
    )
    yield


@pytest.fixture(scope="function")
def mock_get_round(mocker):
    from assess.services.models.round import Round

    mock_funcs = [
        "assess.assessments.routes.get_round",
        "assess.tagging.routes.get_round",
        "assess.services.shared_data_helpers.get_round",
        "assess.authentication.validation.get_round",
    ]

    mock_round_info = Round.from_dict(mock_api_results["fund_store/funds/{fund_id}/rounds/{round_id}"])

    mocked_rounds = []
    for mock_func in mock_funcs:
        mocked_round = mocker.patch(mock_func, return_value=mock_round_info)
        mocked_rounds.append(mocked_round)

    yield mocked_rounds


@pytest.fixture(scope="function")
def mock_get_rounds(request, mocker):
    from assess.services.models.round import Round

    marker = request.node.get_closest_marker("mock_parameters")
    func_calls = [
        "assess.assessments.models.round_summary.get_rounds",
    ]
    if marker:
        params = marker.args[0]
        mock_funcs = params.get("get_rounds_path", func_calls)
        fund_id = params.get("fund_id", "test-fund")
    else:
        mock_funcs = func_calls
        fund_id = "test-fund"

    mock_round_info = [Round.from_dict(mock_api_results["fund_store/funds/{fund_id}/rounds/{round_id}"])]
    mocked_get_rounds = []
    for mock_func in mock_funcs:
        mocked_round = mocker.patch(mock_func, return_value=mock_round_info)
        mocked_get_rounds.append(mocked_round)

    yield mocked_get_rounds

    for mocked_round in mocked_get_rounds:
        mocked_round.assert_called_with(fund_id, ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME))


@pytest.fixture(scope="function")
def mock_get_users_for_fund(request, mocker):
    marker = request.node.get_closest_marker("mock_parameters")
    try:
        param_fund_short_name = request.getfixturevalue("fund_short_name")
    except pytest.FixtureLookupError:
        param_fund_short_name = None
    func_path = "assess.assessments.routes.get_users_for_fund"
    if param_fund_short_name:
        fund_short_name = param_fund_short_name
        path = func_path
    elif marker:
        params = marker.args[0]
        fund_short_name = params.get("fund_short_name", None)
        path = params.get(
            "users_for_fund_path",
            func_path,
        )
    else:
        fund_short_name = None
        path = func_path

    if fund_short_name and fund_short_name != "TF":
        return_value = []
        for _, account in fund_specific_claim_map[fund_short_name].items():
            return_value.append(
                {
                    **account,
                    "account_id": account["accountId"],
                    "full_name": account["fullName"],
                }
            )
    else:
        return_value = [
            {
                **test_assessor_claims,
                "account_id": test_assessor_claims["accountId"],
                "full_name": test_assessor_claims["fullName"],
            },
            {
                **test_commenter_claims,
                "account_id": test_commenter_claims["accountId"],
                "full_name": test_commenter_claims["fullName"],
            },
            {
                **test_lead_assessor_claims,
                "account_id": test_lead_assessor_claims["accountId"],
                "full_name": test_lead_assessor_claims["fullName"],
            },
        ]

    mocked_assigned_apps = mocker.patch(
        path,
        return_value=return_value,
    )

    yield mocked_assigned_apps


@pytest.fixture(scope="function")
def mock_get_application_overviews(request, mocker):
    marker = request.node.get_closest_marker("mock_parameters")
    func_path = "assess.assessments.routes.get_application_overviews"
    if marker:
        params = marker.args[0]
        search_params = params.get("expected_search_params")
        fund_id = params.get("fund_id", "test-fund")
        round_id = params.get("round_id", "test-round")
        path = params.get(
            "application_overviews_path",
            func_path,
        )
    else:
        search_params = {
            "search_term": "",
            "search_in": "project_name,short_id",
            "asset_type": "ALL",
            "status": "ALL",
            "filter_by_tag": "ALL",
            "assigned_to": "ALL",
        }
        path = func_path
        fund_id = "test-fund"
        round_id = "test-round"

    mocked_apps_overview = mocker.patch(
        path,
        return_value=mock_api_results["assessment_store/application_overviews/{fund_id}/{round_id}?"],
    )
    yield mocked_apps_overview

    mocked_apps_overview.assert_called_with(fund_id, round_id, search_params)


@pytest.fixture(scope="function")
def mock_get_assessor_tasklist_state(request, mocker):
    marker = request.node.get_closest_marker("application_id")
    if "expect_flagging" in request.fixturenames:
        expect_flagging = request.getfixturevalue("expect_flagging")
    else:
        expect_flagging = True

    application_id = marker.args[0]
    mock_tasklist_state = mock_api_results[f"assessment_store/application_overviews/{application_id}"]
    mocked_tasklist_state = mocker.patch(
        "assess.services.shared_data_helpers.get_assessor_task_list_state",
        return_value=mock_tasklist_state,
    )
    yield mocked_tasklist_state

    if expect_flagging:
        mocked_tasklist_state.assert_called_with(application_id)


@pytest.fixture(scope="function")
def mock_get_assessment_stats(request, mocker):
    marker = request.node.get_closest_marker("mock_parameters")
    params = marker.args[0]
    mock_funcs = params.get(
        "get_assessment_stats_path",
        [
            "assess.assessments.models.round_summary.get_assessments_stats",
        ],
    )
    # fund_id = params.get("fund_id", "test-fund")
    # round_id = params.get("round_id", "test-round")

    mock_stats = mock_api_results["assessment_store/assessments/get-stats/{fund_id}"]

    mocked_get_stats = []
    for mock_func in mock_funcs:
        mocked_stat = mocker.patch(mock_func, return_value=mock_stats)
        mocked_get_stats.append(mocked_stat)

    yield mocked_get_stats

    # if params.get("get_assessment_stats_path"):
    #     for mocked_stat in mocked_get_stats:
    #         mocked_stat.assert_called_with(fund_id, round_id)


@pytest.fixture(scope="function")
def mock_get_assessment_progress(mocker):
    mocked_progress_func = mocker.patch(
        "assess.assessments.routes.get_assessment_progress",
        return_value=mock_api_results["assessment_store/application_overviews/{fund_id}/{round_id}?"],
    )
    yield mocked_progress_func

    mocked_progress_func.assert_called_once()


@pytest.fixture(scope="function")
def mock_get_teams_flag_stats(mocker):
    mocked_progress_func = mocker.patch(
        "assess.assessments.routes.get_team_flag_stats",
        return_value=mock_api_results["assessment_store/assessments/get-team-flag-stats/{fund_id}/{round_id}"],
    )
    yield mocked_progress_func

    mocked_progress_func.assert_called_once()


@pytest.fixture(scope="function")
def mock_get_flags(request, mocker):
    from assess.services.models.flag import Flag

    marker = request.node.get_closest_marker("application_id")
    application_id = marker.args[0]

    mock_flag_info = Flag.from_list(mock_api_results[f"assessment_store/flags?application_id={application_id}"])

    mock_funcs = [
        "assess.assessments.routes.get_flags",
        "assess.flagging.helpers.get_flags",
        "assess.flagging.routes.get_flags",
        "assess.scoring.routes.get_flags",
    ]

    mocked_flags = []
    for mock_func in mock_funcs:
        mocked_flags.append(mocker.patch(mock_func, return_value=mock_flag_info))
    yield mocked_flags


@pytest.fixture(scope="function")
def mock_submit_flag(request, mocker):
    all_submit_flag_funcs = ["assess.flagging.helpers.submit_flagassess.flagging.routes.submit_flag"]
    marker_submit_flag_paths = request.node.get_closest_marker("submit_flag_paths")
    submit_flag_paths = marker_submit_flag_paths.args[0] if marker_submit_flag_paths else all_submit_flag_funcs

    marker_flag = request.node.get_closest_marker("flag")
    flag = marker_flag.args[0] if marker_flag else None

    mock_funcs = (
        submit_flag_paths
        if marker_submit_flag_paths
        else [
            "assess.flagging.helpers.submit_flag",
            "assess.flagging.routes.submit_flag",
        ]
    )

    mocked_submit_flags = []
    for mock_func in mock_funcs:
        mocked_flag = mocker.patch(mock_func, return_value=flag)
        mocked_submit_flags.append(mocked_flag)

    yield mocked_submit_flags
    if marker_submit_flag_paths:
        for mocked_flag in mocked_submit_flags:
            mocked_flag.assert_called_once()


@pytest.fixture(scope="function")
def mock_get_qa_complete(request, mocker):
    marker = request.node.get_closest_marker("application_id")
    application_id = marker.args[0]

    mock_qa_info = mock_api_results[f"assessment_store/qa_complete/{application_id}"]
    mocker.patch(
        "assess.assessments.routes.get_qa_complete",
        return_value=mock_qa_info,
    )
    yield


@pytest.fixture(scope="function")
def mock_get_flag(request, mocker):
    from assess.services.models.flag import Flag

    marker = request.node.get_closest_marker("flag_id")
    flag_id = marker.args[0]

    mock_flag_info = Flag.from_dict(mock_api_results[f"assessment_store/flag_data?flag_id={flag_id}"])

    mock_funcs = ["assess.flagging.routes.get_flag"]

    get_flag_mocks = []
    for mock_func in mock_funcs:
        get_flag_mocks.append(mocker.patch(mock_func, return_value=mock_flag_info))

    yield get_flag_mocks


@pytest.fixture(scope="function")
def mock_get_available_teams(request, mocker):
    mocker.patch(
        "assess.flagging.routes.get_available_teams",
        return_value=[{"key": "TEAM_A", "value": "Team A"}],
    )

    yield


@pytest.fixture(scope="function")
def mock_get_bulk_accounts(request, mocker):
    mock_bulk_accounts = mock_api_results["account_store/bulk-accounts"]
    mocker.patch(
        "assess.assessments.routes.get_bulk_accounts_dict",
        return_value=mock_bulk_accounts,
    )
    mocker.patch(
        "assess.services.data_services.get_bulk_accounts_dict",
        return_value=mock_bulk_accounts,
    )
    yield


@pytest.fixture(scope="function")
def mock_get_sub_criteria(request, mocker):
    application_id = request.node.get_closest_marker("application_id").args[0]
    sub_criteria_id = request.node.get_closest_marker("sub_criteria_id").args[0]
    from assess.services.models.sub_criteria import SubCriteria

    mock_funcs = [
        "assess.assessments.routes.get_sub_criteria",
        "assess.scoring.routes.get_sub_criteria",
    ]
    mock_sub_crit = SubCriteria.from_filtered_dict(
        mock_api_results[f"assessment_store/sub_criteria_overview/{application_id}/{sub_criteria_id}"]
    )
    mocked_sub_crits = []
    for mock_func in mock_funcs:
        mocked_sub_crits.append(mocker.patch(mock_func, return_value=mock_sub_crit))

    yield mocked_sub_crits


@pytest.fixture(scope="function")
def mock_get_sub_criteria_theme(request, mocker):
    application_id = request.node.get_closest_marker("application_id").args[0]
    mock_theme = mock_api_results[f"assessment_store/sub_criteria_themes/{application_id}/test_theme_id"]
    mocker.patch(
        "assess.assessments.routes.get_sub_criteria_theme_answers_all",
        return_value=mock_theme,
    )
    yield


@pytest.fixture(scope="function")
def mock_get_comments(mocker):
    mock_comments = mock_api_results["assessment_store/comment?"]
    (
        mocker.patch(
            "assess.assessments.routes.get_comments",
            return_value=mock_comments,
        ),
    )
    (
        mocker.patch(
            "assess.scoring.routes.get_comments",
            return_value=mock_comments,
        ),
    )
    yield


@pytest.fixture(scope="function")
def mock_get_scores(mocker):
    mock_scores = mock_api_results["assessment_store/score?"]
    mocker.patch(
        "assess.scoring.routes.get_score_and_justification",
        return_value=mock_scores,
    )
    yield


@pytest.fixture(scope="function")
def mock_get_application_json(mocker):
    full_application = mock_full_application_json
    mocker.patch(
        "assess.assessments.routes.get_application_json",
        return_value=mock_full_application_json,
    )
    yield full_application


@pytest.fixture(scope="function")
def mock_get_tasklist_state_for_banner(mocker):
    mock_task_list = AssessorTaskList(
        is_qa_complete="",
        fund_guidance_url="",
        fund_name="",
        fund_short_name="",
        fund_id="",
        round_id="",
        round_short_name="",
        project_name="",
        short_id="",
        workflow_status="IN_PROGRESS",
        date_submitted="2023-01-01 12:00:00",
        funding_amount_requested="123",
        project_reference="ABGCDF",
        sections=[],
        criterias=[],
        is_eoi_round=False,
    )
    mocker.patch(
        "assess.assessments.routes.get_state_for_tasklist_banner",
        return_value=mock_task_list,
    )
    mocker.patch(
        "assess.flagging.routes.get_state_for_tasklist_banner",
        return_value=mock_task_list,
    )
    mocker.patch(
        "assess.scoring.routes.get_state_for_tasklist_banner",
        return_value=mock_task_list,
    )
    mocker.patch(
        "assess.tagging.routes.get_state_for_tasklist_banner",
        return_value=mock_task_list,
    )
    mocker.patch(
        "assess.services.shared_data_helpers.get_state_for_tasklist_banner",
        return_value=mock_task_list,
    )
    yield


@pytest.fixture(scope="function")
def client_with_valid_session(assess_test_client):
    token = create_valid_token(test_lead_assessor_claims)
    assess_test_client.set_cookie("fsd_user_token", token)
    yield assess_test_client


@pytest.fixture(scope="function")
def mock_get_associated_tags_for_application(mocker):
    for function_module_path in [
        "assess.assessments.routes.get_associated_tags_for_application",
        "assess.tagging.routes.get_associated_tags_for_application",
    ]:
        mocker.patch(
            function_module_path,
            return_value=[AssociatedTag.from_dict(associated_tag)],
        )
    yield


@pytest.fixture(scope="function")
def mock_get_inactive_tags_for_fund_round(mocker):
    mocker.patch(
        "assess.assessments.routes.get_tags_for_fund_round",
        return_value=[Tag.from_dict(t) for t in test_tags_inactive],
    )
    mocker.patch(
        "assess.tagging.routes.get_tags_for_fund_round",
        return_value=[Tag.from_dict(t) for t in test_tags_inactive],
    )
    yield


@pytest.fixture(scope="function")
def mock_get_active_tags_for_fund_round(mocker):
    mocker.patch(
        "assess.assessments.routes.get_tags_for_fund_round",
        return_value=[Tag.from_dict(t) for t in test_tags_active],
    )
    mocker.patch(
        "assess.tagging.routes.get_tags_for_fund_round",
        return_value=[Tag.from_dict(t) for t in test_tags_active],
    )
    yield


@pytest.fixture(scope="function")
def mock_get_tag_for_fund_round(mocker):
    tag = Tag.from_dict(test_get_tag)
    mocker.patch(
        "assess.tagging.routes.get_tag_for_fund_round",
        return_value=tag,
    )
    yield tag


@pytest.fixture(scope="function")
def mock_get_tag_types(mocker):
    for function_module_path in [
        "assess.tagging.routes.get_tag_types",
        "assess.services.data_services.get_tag_types",
    ]:
        mocker.patch(
            function_module_path,
            return_value=[
                TagType(
                    id="type_1",
                    purpose="POSITIVE",
                    description="Tag type 1 description",
                )
            ],
        )
    yield


@pytest.fixture(scope="function")
def mock_update_tags(mocker, request):
    tag_updated_bool = request.node.get_closest_marker("tag_updated_bool").args[0]
    mocker.patch(
        "assess.tagging.routes.update_tags",
        return_value=tag_updated_bool,
    )
    yield


@pytest.fixture(scope="function")
def mock_get_tag_map_and_tag_options(mocker):
    for function_module_path in [
        "assess.assessments.routes.get_tag_map_and_tag_options",
        "assess.assessments.helpers.get_tag_map_and_tag_options",
    ]:
        mocker.patch(
            function_module_path,
            return_value=(
                [
                    AssociatedTag(
                        application_id="75dabe60-ae89-4a47-9263-d35e010b6c66",
                        associated=True,
                        purpose="NEGATIVE",
                        tag_id="75f4296f-502b-4293-82a8-b828e678dd9e",
                        user_id="65f4296f-502b-4293-82a8-b828e678dd9e",
                        value="Tag one red",
                    )
                ],
                [
                    TagType(
                        id="tag_type_1",
                        purpose="POSITIVE",
                        description="Tag type 1 description",
                    )
                ],
            ),
        )
    yield


@pytest.fixture(scope="function")
def mock_get_scoring_system(request, mocker):
    mocker.patch(
        "assess.scoring.helpers.get_scoring_system",
        return_value="OneToFive",
    )

    yield


COF_R2_W2_FORM_NAME_TO_TITLE_MAP = OrderedDict(
    [
        ("organisation-information", "Organisation Information"),
        ("applicant-information", "Applicant Information"),
        ("project-information", "Project Information"),
        ("asset-information", "Asset Information"),
        ("community-use", "Community Use"),
        ("community-engagement", "Community Engagement"),
        ("local-support", "Local Support"),
        ("environmental-sustainability", "Environmental Sustainability"),
        ("funding-required", "Funding Required"),
        ("feasibility", "Feasibility"),
        ("risk", "Risk"),
        ("project-costs", "Project Costs"),
        ("skills-and-resources", "Skills And Resources"),
        ("community-representation", "Community Representation"),
        ("inclusiveness-and-integration", "Inclusiveness And Integration"),
        ("upload-business-plan", "Upload Business Plan"),
        ("community-benefits", "Community Benefits"),
        ("value-to-the-community", "Value To The Community"),
        ("project-qualification", "Project Qualification"),
        ("declarations", "Declarations"),
    ]
)
COF_R2_W2_FORM_NAME_TO_PATH_MAP = OrderedDict(
    [
        ("organisation-information", "1.1.1.1"),
        ("applicant-information", "1.1.1.2"),
        ("project-information", "1.1.2.1"),
        ("asset-information", "1.1.2.2"),
        ("community-use", "1.1.3.1"),
        ("community-engagement", "1.1.3.2"),
        ("local-support", "1.1.3.3"),
        ("environmental-sustainability", "1.1.3.4"),
        ("funding-required", "1.1.4.1"),
        ("feasibility", "1.1.4.2"),
        ("risk", "1.1.4.3"),
        ("project-costs", "1.1.4.4"),
        ("skills-and-resources", "1.1.4.5"),
        ("community-representation", "1.1.4.6"),
        ("inclusiveness-and-integration", "1.1.4.7"),
        ("upload-business-plan", "1.1.4.8"),
        ("community-benefits", "1.1.5.1"),
        ("value-to-the-community", "1.1.6.1"),
        ("project-qualification", "1.1.7.1"),
        ("declarations", "1.1.8.1"),
    ]
)
COF_R2_W2_GENERATE_MAPS_FROM_FORM_NAMES = (
    COF_R2_W2_FORM_NAME_TO_TITLE_MAP,
    COF_R2_W2_FORM_NAME_TO_PATH_MAP,
)
