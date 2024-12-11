import pytest
from bs4 import BeautifulSoup

from tests.assess_tests.api_data.test_data import fund_specific_claim_map
from tests.assess_tests.conftest import create_valid_token


@pytest.mark.mock_parameters(
    {
        "get_assessment_stats_path": [
            "assess.assessments.models.round_summary.get_assessments_stats",
        ],
        "get_rounds_path": [
            "assess.assessments.models.round_summary.get_rounds",
        ],
        "fund_id": "test-fund",
        "round_id": "test-round",
    }
)
@pytest.mark.maintenance_mode("False")
def test_route_landing_maintenance_mode_disabled(
    flask_test_maintenance_client,
    mock_get_funds,
    mock_get_rounds,
    mock_get_assessment_stats,
):
    response = flask_test_maintenance_client.get("/assess/assessor_tool_dashboard/")
    assert 200 == response.status_code, "Wrong status code on response"
    soup = BeautifulSoup(response.data, "html.parser")
    assert (
        soup.title.string == "Assessment tool dashboard – Assessment Hub – GOV.UK"
    ), "Response does not contain expected heading"


@pytest.mark.maintenance_mode("True")
def test_route_landing_maintenance_mode_enabled(
    flask_test_maintenance_client,
):
    response = flask_test_maintenance_client.get("/assess/assessor_tool_dashboard/")
    assert 503 == response.status_code, "Wrong status code on response"
    soup = BeautifulSoup(response.data, "html.parser")
    assert (
        soup.title.string == "Sorry, this service is unavailable – Assessment Hub – GOV.UK"
    ), "Response does not contain expected heading"


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": {
            "search_term": "",
            "search_in": "project_name,short_id",
            "asset_type": "ALL",
            "assigned_to": "ALL",
            "status": "ALL",
            "filter_by_tag": "ALL",
        },
    }
)
@pytest.mark.application_id("resolved_app")
@pytest.mark.maintenance_mode("False")
def test_route_fund_dashboard_maintenance_mode_disabled(
    request,
    flask_test_maintenance_client,
    mock_get_fund,
    mock_get_funds,
    mock_get_round,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    mock_get_assessment_progress,
    mock_get_active_tags_for_fund_round,
    mock_get_tag_types,
):
    flask_test_maintenance_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map["COF"]["ASSESSOR"]),
    )

    params = request.node.get_closest_marker("mock_parameters").args[0]

    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    response = flask_test_maintenance_client.get(
        f"/assess/fund_dashboard/{fund_short_name}/{round_short_name}",
        follow_redirects=True,
    )
    assert 200 == response.status_code, "Wrong status code on response"
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.title.string == "Team dashboard – Assessment Hub – GOV.UK", "Response does not contain expected heading"


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
    }
)
@pytest.mark.application_id("resolved_app")
@pytest.mark.maintenance_mode("True")
def test_route_fund_dashboard_maintenance_mode_enabled(
    request,
    flask_test_maintenance_client,
):
    flask_test_maintenance_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map["COF"]["ASSESSOR"]),
    )

    params = request.node.get_closest_marker("mock_parameters").args[0]

    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    response = flask_test_maintenance_client.get(
        f"/assess/fund_dashboard/{fund_short_name}/{round_short_name}",
        follow_redirects=True,
    )
    assert 503 == response.status_code, "Wrong status code on response"
    soup = BeautifulSoup(response.data, "html.parser")
    assert (
        soup.title.string == "Sorry, this service is unavailable – Assessment Hub – GOV.UK"
    ), "Response does not contain expected heading"
