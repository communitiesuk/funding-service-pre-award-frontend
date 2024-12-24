from datetime import datetime

import pytest

from tests.apply_tests.api_data.test_data import TEST_APPLICATION_SUMMARIES


@pytest.fixture
def display_data():
    return {
        "funds": [
            {
                "fund_data": {"name": "Test Fund", "funding_type": "EOI", "short_name": "TF"},
                "rounds": [
                    {
                        "is_not_yet_open": False,
                        "round_details": {
                            "title": "Test Round",
                            "deadline": "2030-12-31T11:58:00",
                            "has_eligibility": False,
                            "is_expression_of_interest": False,
                            "id": "round_id",
                            "short_name": "TR",
                        },
                        "is_past_submission_deadline": False,
                        "applications": [
                            {
                                "status": "CHANGES_REQUESTED",
                                "id": "app_id",
                                "project_name": "Test Project",
                                "last_edited": datetime(2024, 12, 23, 15, 12, 51, 889247),
                            }
                        ],
                    }
                ],
            }
        ],
        "total_applications_to_display": 1,
    }


@pytest.mark.usefixtures("mock_login", "mock_get_fund_round")
def test_changes_requested_notification(apply_test_client, mocker, templates_rendered, display_data):
    mocker.patch(
        "apply.default.account_routes.search_applications",
        return_value=TEST_APPLICATION_SUMMARIES,
    )
    apply_test_client.application.jinja_env.globals["get_service_title"] = lambda: "Test Service Title"
    apply_test_client.application.jinja_env.globals["toggle_dict"] = {"MULTIFUND_DASHBOARD": False}

    response = apply_test_client.get("/account?fund=CTDF", follow_redirects=True)
    assert response.status_code == 200

    template, context = templates_rendered[0]
    assert template.name == "apply/dashboard_single_fund.html"

    rendered_html = template.render(
        display_data=display_data,
    )
    assert "Please review updates from the Assessor" in rendered_html


@pytest.mark.usefixtures("mock_login", "mock_get_fund_round")
def test_no_changes_requested_notification(apply_test_client, mocker, templates_rendered, display_data):
    mocker.patch(
        "apply.default.account_routes.search_applications",
        return_value=TEST_APPLICATION_SUMMARIES,
    )
    apply_test_client.application.jinja_env.globals["get_service_title"] = lambda: "Test Service Title"
    apply_test_client.application.jinja_env.globals["toggle_dict"] = {"MULTIFUND_DASHBOARD": False}

    # Change the status to SUBMITTED
    display_data["funds"][0]["rounds"][0]["applications"][0]["status"] = "SUBMITTED"

    response = apply_test_client.get("/account?fund=CTDF", follow_redirects=True)
    assert response.status_code == 200

    template, context = templates_rendered[0]
    assert template.name == "apply/dashboard_single_fund.html"

    rendered_html = template.render(display_data=display_data)
    assert "Please review updates from the Assessor" not in rendered_html
