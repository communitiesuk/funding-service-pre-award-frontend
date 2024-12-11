import re
from unittest import mock

import pytest
from bs4 import BeautifulSoup
from flask import url_for

from tests.assess_tests.api_data.test_data import fund_specific_claim_map, resolved_app_id, stopped_app_id
from tests.assess_tests.conftest import create_valid_token


# Test assign_assessments route
@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": {
            "search_term": "",
            "search_in": "project_name,short_id",
            "assigned_to": "ALL",
            "asset_type": "ALL",
            "status": "ALL",
            "filter_by_tag": "ALL",
        },
    }
)
def test_assign_assessments_get(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    mock_get_assessment_progress,
    mock_get_application_metadata,
    mock_get_active_tags_for_fund_round,
    mock_get_tag_types,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    response = assess_test_client.get(
        url_for(
            "assessment_bp.assign_assessments",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
        )
    )

    soup = BeautifulSoup(response.data, "html.parser")

    # Check that there is a checkbox for each project
    project_checkboxes = soup.find_all("input", {"type": "checkbox", "name": "selected_assessments"})
    assert len(project_checkboxes) == 4, f"Expected 4 project checkboxes, found {len(project_checkboxes)}"

    assert response.status_code == 200
    assert b"Assign assessments" in response.data


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": "",
    }
)
def test_assign_assessments_post(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    patch_resolve_redirect,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    form_data = {
        "selected_assessments": ["assessment1"],
    }

    headers = {
        "Referer": url_for(
            "assessment_bp.assign_assessments",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = assess_test_client.post(
        url_for(
            "assessment_bp.assign_assessments",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
        ),
        headers=headers,
        data=form_data,
        follow_redirects=True,
    )

    # Check that there are two radio buttons, one for general assessor and one for lead assessor
    soup = BeautifulSoup(response.data, "html.parser")

    # Check form data has been processed and stored as hidden fields.
    hidden_fields = soup.find_all("input", {"type": "hidden", "name": "selected_assessments"})
    assert hidden_fields[0].get("value") == "assessment1"

    radio_buttons = soup.find_all("input", {"type": "radio"})

    assert len(radio_buttons) == 2, f"Expected 2 radio buttons, found {len(radio_buttons)}"

    radio_values = [radio.get("value") for radio in radio_buttons]
    assert "general_assessor" in radio_values, "Radio button for 'general_assessor' not found"
    assert "lead_assessor" in radio_values, "Radio button for 'lead_assessor' not found"

    assert response.status_code == 200
    assert b"Select the type of role you would like to assign." in response.data


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": "",
    }
)
def test_assessor_type_post(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    patch_resolve_redirect,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    form_data = {
        "selected_assessments": ["assessment1"],
        "assessor_role": ["lead_assessor"],
    }

    headers = {
        "Referer": url_for(
            "assessment_bp.assessor_type",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }

    with mock.patch(
        "assess.assessments.routes.get_application_assignments",
        return_value=[{"user_id": "user2"}],
    ):
        response = assess_test_client.post(
            url_for(
                "assessment_bp.assessor_type",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            headers=headers,
            data=form_data,
            follow_redirects=True,
        )

    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")

    # Check form data has been processed and stored as hidden fields.
    for key, value in form_data.items():
        hidden_field = soup.find("input", {"type": "hidden", "name": key})
        assert hidden_field is not None
        assert hidden_field.get("value") == value[0]

    # Check for the "select all" checkbox
    select_all_checkbox = soup.find("input", {"id": "select_all_users", "type": "checkbox"})
    assert select_all_checkbox is not None, "Select all checkbox not found"

    table_body = soup.find("tbody", class_="govuk-table__body")
    assert table_body is not None, "Table body not found"

    # Check there is only a single assignable user ("Lead Test User")
    rows = table_body.find_all("tr", class_="govuk-table__row")
    assert len(rows) == 1, f"Expected 1 row, found {len(rows)}"

    row = rows[0]

    name_cell = row.find_all("td", class_="govuk-table__cell")[1]
    assert (
        fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["fullName"] in name_cell.text.strip()
    ), f"Expected 'Lead Test User', found {name_cell.text.strip()}"

    # Check that there is a checkbox for this entry
    checkbox = row.find(
        "input",
        {
            "type": "checkbox",
            "name": "selected_users",
            "value": fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
        },
    )
    assert (
        checkbox is not None
    ), f"Checkbox for {fund_specific_claim_map[fund_short_name]['LEAD_ASSESSOR']['accountId']} not found"

    assert not checkbox.has_attr("checked"), "Checkbox is not checked"


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": "",
    }
)
def test_assessor_type_post_existing_assignment(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    patch_resolve_redirect,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    form_data = {
        "selected_assessments": ["assessment1"],
        "assessor_role": ["lead_assessor"],
    }

    headers = {
        "Referer": url_for(
            "assessment_bp.assessor_type",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }

    with mock.patch(
        "assess.assessments.routes.get_application_assignments",
        return_value=[{"user_id": "cof-lead-assessor"}],
    ):
        response = assess_test_client.post(
            url_for(
                "assessment_bp.assessor_type",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            headers=headers,
            data=form_data,
            follow_redirects=True,
        )

    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")

    table_body = soup.find("tbody", class_="govuk-table__body")
    assert table_body is not None, "Table body not found"

    # Check there is only a single assignable user ("Lead Test User")
    rows = table_body.find_all("tr", class_="govuk-table__row")
    assert len(rows) == 1, f"Expected 1 row, found {len(rows)}"

    row = rows[0]

    name_cell = row.find_all("td", class_="govuk-table__cell")[1]
    assert (
        fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["fullName"] in name_cell.text.strip()
    ), f"Expected 'Lead Test User', found {name_cell.text.strip()}"

    # Check that there is a checkbox for this entry
    checkbox = row.find(
        "input",
        {
            "type": "checkbox",
            "name": "selected_users",
            "value": fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
        },
    )

    assert checkbox is not None, "Checkbox not found"

    # Check if the checkbox is checked
    assert checkbox.has_attr("checked"), "Checkbox is not checked"


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": "",
    }
)
def test_assessor_type_list_post(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    mock_get_assessment_progress,
    patch_resolve_redirect,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    form_data = {
        "selected_assessments": ["stopped_app"],
        "assessor_role": ["general_assessor"],
        "selected_users": [fund_specific_claim_map[fund_short_name]["ASSESSOR"]["accountId"]],
    }
    headers = {
        "Referer": url_for(
            "assessment_bp.assessor_type_list",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }
    response = assess_test_client.post(
        url_for(
            "assessment_bp.assessor_type_list",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
        ),
        data=form_data,
        headers=headers,
        follow_redirects=True,
    )

    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")

    # Check form data has been processed and stored as hidden fields.
    for key, value in form_data.items():
        hidden_field = soup.find("input", {"type": "hidden", "name": key})
        assert hidden_field is not None
        assert hidden_field.get("value") == value[0]

    # Check get_assessment_progress() is only called for the selected assessments
    assert len(mock_get_assessment_progress.call_args[0][0]) == 1
    assert mock_get_assessment_progress.call_args[0][0][0]["application_id"] == form_data["selected_assessments"][0]
    strip_html_regx = re.compile("<.*?>")
    html_stripped_output = re.sub(strip_html_regx, "", str(response.data))
    assert (
        f"You are about to assign {fund_specific_claim_map[fund_short_name]['ASSESSOR']['fullName']}"
        " as a general assessor to the selected assessment" in html_stripped_output
    )


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": "",
    }
)
def test_assignment_overview_remove_assessor(
    request,
    assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    mock_get_assessment_progress,
    patch_resolve_redirect,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    headers = {
        "Referer": url_for(
            "assessment_bp.assessor_type_list",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }

    form_data = {
        "selected_assessments": ["stopped_app"],
        "assessor_role": ["general_assessor"],
        "selected_users": [],
        "assigned_users": [fund_specific_claim_map[fund_short_name]["ASSESSOR"]["accountId"]],
    }

    response = assess_test_client.post(
        url_for(
            "assessment_bp.assessor_type_list",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
        ),
        data=form_data,
        headers=headers,
        follow_redirects=True,
    )
    strip_html_regx = re.compile("<.*?>")
    html_stripped_output = re.sub(strip_html_regx, "", str(response.data))
    assert (
        f"You are about to remove {fund_specific_claim_map[fund_short_name]['ASSESSOR']['fullName']}"
        " as a general assessor from the selected assessment" in html_stripped_output
    )


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": "",
    }
)
def test_assignment_overview_add_and_remove_assessors(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    mock_get_assessment_progress,
    patch_resolve_redirect,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    headers = {
        "Referer": url_for(
            "assessment_bp.assessor_type_list",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }

    form_data = {
        "selected_assessments": ["stopped_app"],
        "assessor_role": ["general_assessor"],
        "selected_users": [
            fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
            fund_specific_claim_map[fund_short_name]["COMMENTER"]["accountId"],
        ],
        "assigned_users": [
            fund_specific_claim_map[fund_short_name]["ASSESSOR"]["accountId"],
            fund_specific_claim_map[fund_short_name]["COMMENTER"]["accountId"],
        ],
    }

    response = assess_test_client.post(
        url_for(
            "assessment_bp.assessor_type_list",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
        ),
        data=form_data,
        headers=headers,
        follow_redirects=True,
    )
    strip_html_regx = re.compile("<.*?>")
    html_stripped_output = re.sub(strip_html_regx, "", str(response.data))
    assert (
        f"remove {fund_specific_claim_map[fund_short_name]['ASSESSOR']['fullName']}"
        " as a general assessor from the assessment" in html_stripped_output
    )
    assert (
        f"assign {fund_specific_claim_map[fund_short_name]['LEAD_ASSESSOR']['fullName']}"
        " as a general assessor to the assessment" in html_stripped_output
    )


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": {
            "search_term": "",
            "search_in": "project_name,short_id",
            "asset_type": "ALL",
            "status": "ALL",
            "filter_by_tag": "ALL",
            "assigned_to": "ALL",
        },
    }
)
def test_assignment_overview_post_new_and_exising(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    mock_get_assessment_progress,
    mock_get_application_metadata,
    mock_get_active_tags_for_fund_round,
    mock_get_tag_types,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    user_1 = fund_specific_claim_map[fund_short_name]["COMMENTER"]["accountId"]
    user_2 = fund_specific_claim_map[fund_short_name]["ASSESSOR"]["accountId"]
    assessment_1 = stopped_app_id
    assessment_2 = resolved_app_id

    form_data = {
        "selected_assessments": [assessment_1, assessment_2],
        "assessor_role": ["lead_assessor"],
        "selected_users": [user_1, user_2],
        "message_to_all": "Hi, how are you?",
        f"message_{user_1}": "This is a message to user1",
    }

    headers = {
        "Referer": url_for(
            "assessment_bp.assignment_overview",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }
    with (
        mock.patch(
            "assess.assessments.routes.get_application_assignments",
            return_value=[{"user_id": user_2}],
        ),
        mock.patch(
            "assess.assessments.routes.assign_user_to_assessment",
        ) as mock_assign_user_to_assessment_1,
    ):
        response = assess_test_client.post(
            url_for(
                "assessment_bp.assignment_overview",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            data=form_data,
            headers=headers,
            follow_redirects=True,
        )

        # For User 1 this is a new assignment, for User 2 this is an existing assignment that should be activated.
        mock_assign_user_to_assessment_1.assert_has_calls(
            [
                mock.call(
                    assessment_1,
                    user_1,
                    fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
                    False,
                    True,
                    True,
                    "This is a message to user1",
                ),
                mock.call(
                    assessment_2,
                    user_1,
                    fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
                    False,
                    True,
                    True,
                    "This is a message to user1",
                ),
                mock.call(
                    assessment_1,
                    user_2,
                    fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
                    True,
                    True,
                    True,
                    "Hi, how are you?",
                ),
                mock.call(
                    assessment_2,
                    user_2,
                    fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
                    True,
                    True,
                    True,
                    "Hi, how are you?",
                ),
            ],
            any_order=True,
        )

        assert len(mock_assign_user_to_assessment_1.mock_calls) == 4

    assert response.status_code == 200


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": {
            "search_term": "",
            "search_in": "project_name,short_id",
            "asset_type": "ALL",
            "status": "ALL",
            "filter_by_tag": "ALL",
            "assigned_to": "ALL",
        },
    }
)
def test_assignment_overview_post_add_and_remove(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    mock_get_assessment_progress,
    mock_get_application_metadata,
    mock_get_active_tags_for_fund_round,
    mock_get_tag_types,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    user_1 = fund_specific_claim_map[fund_short_name]["COMMENTER"]["accountId"]
    user_2 = fund_specific_claim_map[fund_short_name]["ASSESSOR"]["accountId"]
    user_3 = fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"]
    assessment_1 = stopped_app_id

    form_data = {
        "selected_assessments": [assessment_1],
        "assessor_role": ["lead_assessor"],
        "selected_users": [user_1, user_3],
        "assigned_users": [user_2, user_3],
    }

    headers = {
        "Referer": url_for(
            "assessment_bp.assignment_overview",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }
    with (
        mock.patch(
            "assess.assessments.routes.get_application_assignments",
            return_value=[{"user_id": user_2}, {"user_id": user_3}],
        ),
        mock.patch(
            "assess.assessments.routes.assign_user_to_assessment",
        ) as mock_assign_user_to_assessment_1,
    ):
        response = assess_test_client.post(
            url_for(
                "assessment_bp.assignment_overview",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            data=form_data,
            headers=headers,
            follow_redirects=True,
        )

        # For User 1 this is a new assignment, for User 2 the existing assignment should be deactivated.
        mock_assign_user_to_assessment_1.assert_has_calls(
            [
                mock.call(
                    assessment_1,
                    user_1,
                    fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
                    False,
                    True,
                    True,
                    "",
                ),
                mock.call(
                    assessment_1,
                    user_2,
                    fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]["accountId"],
                    True,
                    False,
                    True,
                    "",
                ),
            ],
            any_order=True,
        )

        assert len(mock_assign_user_to_assessment_1.mock_calls) == 2

    assert response.status_code == 200


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": "",
    }
)
def test_assignment_multiple_users_multiple_messages(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    patch_resolve_redirect,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    user_1 = fund_specific_claim_map[fund_short_name]["COMMENTER"]["accountId"]
    user_2 = fund_specific_claim_map[fund_short_name]["ASSESSOR"]["accountId"]

    assessment_1 = stopped_app_id

    form_data = {
        "selected_assessments": [assessment_1],
        "assessor_role": ["lead_assessor"],
        "selected_users": [user_1, user_2],
        "edit_messages": "",
    }

    headers = {
        "Referer": url_for(
            "assessment_bp.assignment_overview",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }

    response = assess_test_client.post(
        url_for(
            "assessment_bp.assignment_overview",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
        ),
        data=form_data,
        headers=headers,
        follow_redirects=True,
    )

    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")

    text_field_1 = soup.find("textarea", {"id": "message_to_all"})
    text_field_2 = soup.find("textarea", {"id": f"message_{user_1}"})
    text_field_3 = soup.find("textarea", {"id": f"message_{user_2}"})

    assert bool(text_field_1 and text_field_2 and text_field_3)

    assert soup.find("input", {"type": "checkbox", "id": "assessor_messages_checkbox"})


@pytest.mark.mock_parameters(
    {
        "fund_short_name": "COF",
        "round_short_name": "TR",
        "expected_search_params": "",
    }
)
def test_assignment_overview_cancel_messages(
    request,
        assess_test_client,
    mock_get_funds,
    mock_get_round,
    mock_get_fund,
    mock_get_application_overviews,
    mock_get_users_for_fund,
    mock_get_assessment_progress,
    patch_resolve_redirect,
):
    params = request.node.get_closest_marker("mock_parameters").args[0]
    fund_short_name = params["fund_short_name"]
    round_short_name = params["round_short_name"]

    assess_test_client.set_cookie(
        "fsd_user_token",
        create_valid_token(fund_specific_claim_map[fund_short_name]["LEAD_ASSESSOR"]),
    )

    user_1 = fund_specific_claim_map[fund_short_name]["COMMENTER"]["accountId"]
    assessment_1 = stopped_app_id

    form_data = {
        "selected_assessments": [assessment_1],
        "assessor_role": ["lead_assessor"],
        "selected_users": [user_1],
        "old_assessor_messages": '{"message_to_all": "This is the original message"}',
        "message_to_all": "This is the new message",
        "cancel_messages": "",
    }

    headers = {
        "Referer": url_for(
            "assessment_bp.assessor_comments",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
            _external=True,
        ),
    }

    response = assess_test_client.post(
        url_for(
            "assessment_bp.assessor_comments",
            fund_short_name=fund_short_name,
            round_short_name=round_short_name,
        ),
        data=form_data,
        headers=headers,
        follow_redirects=True,
    )

    assert "This is the original message" in str(response.data)
    assert "This is the new message" not in str(response.data)
