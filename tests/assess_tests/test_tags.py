from unittest import mock

import pytest
from bs4 import BeautifulSoup

from assess.services.data_services import (
    get_associated_tags_for_application,
    get_tags_for_fund_round,
    post_new_tag_for_fund_round,
    update_associated_tags,
)
from assess.tagging.models.tag import Tag
from assess.tagging.routes import FLAG_ERROR_MESSAGE
from tests.assess_tests.api_data.test_data import test_fund_id, test_round_id

test_tags_inactive = [
    {
        "id": "123",
        "value": "Val 1 INACTIVE",
        "creator_user_id": "Bob",
        "active": False,
        "purpose": "POSITIVE",
        "type_id": "type_1",
    },
    {
        "id": "432",
        "value": "Val 2 INACTIVE",
        "creator_user_id": "Bob",
        "active": False,
        "purpose": "POSITIVE",
        "type_id": "type_1",
    },
]
test_tags_active = [
    {
        "id": "123",
        "value": "Val 1",
        "creator_user_id": "Bob",
        "active": True,
        "purpose": "POSITIVE",
        "type_id": "type_1",
        "tag_association_count": 2,
    },
    {
        "id": "432",
        "value": "Val 2",
        "creator_user_id": "Bob",
        "active": True,
        "purpose": "POSITIVE",
        "type_id": "type_1",
        "tag_association_count": 2,
    },
]

associated_tag = {
    "application_id": "75dabe60-ae89-4a47-9263-d35e010b6c66",
    "associated": True,
    "purpose": "POSITIVE",
    "tag_id": "123",
    "user_id": "65f4296f-502b-4293-82a8-b828e678dd9e",
    "value": "Val 1",
}

test_get_tag = {
    "active": True,
    "created_at": "2023-07-25T09:10:39.073315+00:00",
    "creator_user_id": "00000000-0000-0000-0000-000000000000",
    "description": (
        "Use these tags to assign assessments to team members. Note: you cannot send notifications using tags"
    ),
    "fund_id": "47aef2f5-3fcb-4d45-acb5-f0152b5f03c4",
    "id": "a48f4951-b26b-4820-9301-9ca2c835b163",
    "purpose": "PEOPLE",
    "round_id": "5cf439bf-ef6f-431e-92c5-a1d90a4dd32f",
    "tag_association_count": 3,
    "type_id": "89e5c39d-cdc0-40e8-9986-ba26289e6bc4",
    "value": "Test tag",
}


@pytest.mark.application_id("resolved_app")
def test_change_tags_route(
    mock_get_tasklist_state_for_banner,
    client_with_valid_session,
    mock_get_funds,
    mock_get_application_metadata,
    mock_get_fund,
    mock_get_active_tags_for_fund_round,
    mock_get_associated_tags_for_application,
    mock_get_round,
):
    response = client_with_valid_session.get("/assess/application/app_id/tags")
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.find("h1").text == "Change tags"
    assert soup.find("strong").text == "In progress"
    assert (table := soup.find("table", class_="govuk-table dluhc-table-checkboxes"))
    assert len(table.findAll("tr")) == 3
    assert table.findAll("tr")[0].findAll("th")[0].text.strip() == "Tag name"
    assert table.findAll("tr")[1].findAll("th")[0].text.strip() == "Val 1"
    assert table.findAll("tr")[1].findAll("td")[0].text.strip() == "POSITIVE"
    assert table.findAll("tr")[1].findAll("td")[0].find("strong", class_="govuk-tag--green").text.strip() == "POSITIVE"


@pytest.mark.application_id("resolved_app")
def test_change_tags_route_does_not_show_deactivated_tags_as_options(
    mock_get_tasklist_state_for_banner,
    client_with_valid_session,
    mock_get_funds,
    mock_get_application_metadata,
    mock_get_fund,
    mock_get_inactive_tags_for_fund_round,
    mock_get_associated_tags_for_application,
    mock_get_round,
):
    response = client_with_valid_session.get("/assess/application/app_id/tags")
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.find("h1").text == "Change tags"
    assert (
        soup.find(
            "p",
            class_="govuk-body dluhc-body-empty",
        ).text.strip()
        == "There are no tags available"
    )


@pytest.mark.application_id("resolved_app")
def test_change_tags_route_associated_tag_checked(
    mock_get_tasklist_state_for_banner,
    client_with_valid_session,
    mock_get_funds,
    mock_get_application_metadata,
    mock_get_fund,
    mock_get_active_tags_for_fund_round,
    mock_get_associated_tags_for_application,
    mock_get_round,
):
    response = client_with_valid_session.get("/assess/application/app_id/tags")
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.find("h1").text == "Change tags"
    assert soup.find("input", {"id": "123"}).attrs.get("checked") is not None
    assert soup.find("input", {"id": "432"}).attrs.get("checked") is None
    assert (table := soup.find("table", class_="govuk-table dluhc-table-checkboxes"))
    assert len(table.findAll("tr")) == 3


@pytest.mark.application_id("resolved_app")
def test_change_tags_route_no_tags(
    mocker,
    mock_get_tasklist_state_for_banner,
    client_with_valid_session,
    mock_get_funds,
    mock_get_application_metadata,
    mock_get_fund,
    mock_get_round,
):
    mocker.patch(
        "assess.tagging.routes.get_tags_for_fund_round",
        return_value=[],
    )
    mocker.patch(
        "assess.tagging.routes.get_associated_tags_for_application",
        return_value=[],
    )
    response = client_with_valid_session.get("/assess/application/app_id/tags")
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.find("h1").text == "Change tags"
    assert (
        soup.find(
            "p",
            class_="govuk-body dluhc-body-empty",
        ).text.strip()
        == "There are no tags available"
    )


def test_post_new_tag_for_fund_round_returns_True(assess_test_client):
    with mock.patch("requests.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        fund_id = "c62abab1-41b5-4956-b496-4a8862d748a9"
        round_id = "13c7ba20-1d12-4a08-9a95-76d2fa447db1"
        tag = {
            "value": "v",
            "tag_type_id": "f07b4d46-e078-4e2c-9066-be2b96c3140d",
            "creator_user_id": "00000000-0000-0000-0000-000000000000",
        }

        result = post_new_tag_for_fund_round(fund_id, round_id, tag)
        assert result is True


@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
@pytest.mark.parametrize(
    "expect_flagging",
    [
        False,
    ],
)
def test_create_tag_initial_render_get(
    expect_flagging,
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_active_tags_for_fund_round,
):
    response = client_with_valid_session.get(f"/assess/tags/create/{test_fund_id}/{test_round_id}")
    soup = BeautifulSoup(response.data, "html.parser")

    assert response.status_code == 200

    assert "Tag type 1 description" in response.text
    assert "POSITIVE" in response.text
    assert soup.find("h1").text == "Create a new tag"


@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
def test_create_tag_invalid_form_post(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_active_tags_for_fund_round,
):
    expected_errors = [
        "Provide a value for the tag.",
        "This field is required.",
    ]
    response = client_with_valid_session.post(
        f"/assess/tags/create/{test_fund_id}/{test_round_id}",
        data={},  # empty form, so invalid
    )
    soup = BeautifulSoup(response.data, "html.parser")

    # check component errors
    component_errors = soup.find_all("p", class_="govuk-error-message")
    assert response.status_code == 200
    assert all(error_string in str(component_errors) for error_string in expected_errors), "Component errors not found"
    # It is unlikely we will encounter an incorrect radio button submission
    # which is not in the users direct control (although still possible)

    # Check summary errors
    summary_errors = soup.find_all(class_="govuk-error-summary__list")
    assert all(error_string in str(summary_errors) for error_string in expected_errors), "Component errors not found"


@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
def test_create_tag_invalid_character_post(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_active_tags_for_fund_round,
):
    expected_errors = ["Invalid characters in value.", "Not a valid choice."]
    response = client_with_valid_session.post(
        f"/assess/tags/create/{test_fund_id}/{test_round_id}",
        data={"value": "!!", "type": "invalid_type"},  # SPECIAL CHARACTER
    )
    soup = BeautifulSoup(response.data, "html.parser")

    # check component errors
    component_errors = soup.find_all("p", class_="govuk-error-message")
    assert response.status_code == 200
    assert all(error_string in str(component_errors) for error_string in expected_errors), "Component errors not found"
    # It is unlikely we will encounter an incorrect radio button submission
    # which is not in the users direct control (although still possible)

    # Check summary errors
    summary_errors = soup.find_all(class_="govuk-error-summary__list")
    assert all(error_string in str(summary_errors) for error_string in expected_errors), "summary errors not found"


@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
def test_create_duplicate_tag_fails(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_active_tags_for_fund_round,
):
    expected_errors = ["Tag already exists for this round. Please ensure that the tag is unique."]
    response = client_with_valid_session.post(
        f"/assess/tags/create/{test_fund_id}/{test_round_id}",
        data={
            "value": "Val 1",
            "type": "type_1",
        },  # DUPLICATE TAG, mocked choices for tag types (id of the tag)
    )
    soup = BeautifulSoup(response.data, "html.parser")

    # check component errors
    component_errors = soup.find_all("p", class_="govuk-error-message")
    assert response.status_code == 200
    assert all(error_string in str(component_errors) for error_string in expected_errors), "Component errors not found"
    # It is unlikely we will encounter an incorrect radio button submission
    # which is not in the users direct control (although still possible)

    # Check summary errors
    summary_errors = soup.find_all(class_="govuk-error-summary__list")
    assert all(error_string in str(summary_errors) for error_string in expected_errors), "summary errors not found"


@pytest.mark.parametrize(
    "expect_flagging",
    [
        False,
    ],
)
@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
def test_manage_tag_page_renders_with_active_tags(
    expect_flagging,
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_active_tags_for_fund_round,
):
    response = client_with_valid_session.get(
        f"/assess/tags/manage/{test_fund_id}/{test_round_id}",
    )

    assert response.status_code == 200
    assert "Val 1" in response.text
    assert "Val 2" in response.text
    assert "Edit" in response.text
    assert "Deactivate" not in response.text
    assert "Reactivate" not in response.text


@pytest.mark.parametrize(
    "expect_flagging",
    [
        False,
    ],
)
@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
def test_manage_tag_page_renders_with_inactive_tags(
    expect_flagging,
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_inactive_tags_for_fund_round,
):
    response = client_with_valid_session.get(
        f"/assess/tags/manage/{test_fund_id}/{test_round_id}",
    )

    assert response.status_code == 200
    assert "Val 1 INACTIVE" in response.text
    assert "Val 2 INACTIVE" in response.text
    assert "Reactivate" in response.text
    assert "Deactivate" not in response.text


@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
def test_get_deactivate_route(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_tag_for_fund_round,
):
    response = client_with_valid_session.get(
        f"/assess/tags/deactivate/{test_fund_id}/{test_round_id}/{mock_get_tag_for_fund_round.id}"
    )
    assert response.status_code == 200
    assert "Yes, deactivate tag" in response.text
    assert mock_get_tag_for_fund_round.value in response.text


@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
@pytest.mark.tag_updated_bool(True)
def test_post_deactivate_existing_tag_with_checkbox_redirects(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_tag_for_fund_round,
    mock_update_tags,
):
    data = {
        "deactivate": "a48f4951-b26b-4820-9301-9ca2c835b163",
    }

    response = client_with_valid_session.post(
        f"/assess/tags/deactivate/{test_fund_id}/{test_round_id}/{mock_get_tag_for_fund_round.id}",
        data=data,
    )

    assert response.status_code == 302
    assert response.location == "/assess/tags/manage/test-fund/test-round"


@pytest.mark.tag_updated_bool(False)
def test_post_deactivate_non_existing_tag_returns_error(
    client_with_valid_session,
    mock_get_fund,
    mock_get_funds,
    mock_get_round,
    mock_get_tag_for_fund_round,
    mock_update_tags,
):
    data = {
        "deactivate": "a48f4951-b26b-4820-9301-9ca2c835b163",
    }
    response = client_with_valid_session.post(
        f"/assess/tags/deactivate/{test_fund_id}/{test_round_id}/{mock_get_tag_for_fund_round.id}",
        data=data,
    )

    assert response.status_code == 200
    assert "Tag not deactivated." in response.text
    assert "Yes, deactivate tag" in response.text


def test_get_reactivate_existing_tag_returns_200(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_tag_for_fund_round,
):
    response = client_with_valid_session.get(
        f"/assess/tags/reactivate/{test_fund_id}/{test_round_id}/{mock_get_tag_for_fund_round.id}"
    )
    assert response.status_code == 200
    assert "Yes, reactivate tag" in response.text
    assert mock_get_tag_for_fund_round.value in response.text


@pytest.mark.tag_updated_bool(False)
def test_post_reactivate_non_existing_tag_returns_error(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mock_get_tag_for_fund_round,
    mock_update_tags,
):
    data = {}

    response = client_with_valid_session.post(
        f"/assess/tags/reactivate/{test_fund_id}/{test_round_id}/{mock_get_tag_for_fund_round.id}",
        data=data,
    )

    assert response.status_code == 200
    assert "Tag not reactivated." in response.text
    assert "Yes, reactivate tag" in response.text


def test_create_tag_shows_error_if_valid_form_post_but_request_fails(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mocker,
):
    mocker.patch(
        "assess.tagging.routes.post_new_tag_for_fund_round",
        return_value=lambda *_: False,
    )

    response = client_with_valid_session.post(
        f"/assess/tags/create/{test_fund_id}/{test_round_id}",
        data={"value": "Tag value", "type": "type_1"},
    )

    # this redirects and will flash the error message
    assert response.status_code == 302
    assert response.location == "/assess/tags/create/test-fund/test-round"


@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
def test_create_tag_valid_form_post(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mocker,
):
    mocker.patch(
        "assess.tagging.routes.post_new_tag_for_fund_round",
        return_value=lambda *_: True,
    )

    response = client_with_valid_session.post(
        f"/assess/tags/create/{test_fund_id}/{test_round_id}",
        data={"value": "Tag value", "type": "type_1"},
    )

    assert response.status_code == 302
    assert response.location == "/assess/tags/create/test-fund/test-round"
    assert FLAG_ERROR_MESSAGE not in response.text


@pytest.mark.mock_parameters(
    {
        "get_rounds_path": "assess.assessments.routes.get_round",
    }
)
def test_create_tag_valid_form_go_back_post(
    client_with_valid_session,
    mock_get_funds,
    mock_get_fund,
    mock_get_tag_types,
    mock_get_round,
    mocker,
):
    mocker.patch(
        "assess.tagging.routes.post_new_tag_for_fund_round",
        return_value=lambda *_: True,
    )

    response = client_with_valid_session.post(
        f"/assess/tags/create/{test_fund_id}/{test_round_id}?go_back=True",
        data={"value": "Tag value", "type": "type_1"},
    )

    assert response.status_code == 302
    assert response.location == "/assess/tags/manage/test-fund/test-round"


# Test Functions


def test_get_available_active_tags(assess_test_client):
    with mock.patch(
        "assess.services.data_services.get_data",
        return_value=test_tags_active,
    ) as mock_get_data:
        result = get_tags_for_fund_round("test_fund", "test_round", {"tag_status": "True"})
        mock_get_data.assert_called_once()
        mock_get_data.assert_called_with("assessment_store/funds/test_fund/rounds/test_round/tags?tag_status=True")
        assert len(result) == 2
        assert result[0].value == "Val 1"


def test_get_available_inactive_tags(assess_test_client):
    with mock.patch(
        "assess.services.data_services.get_data",
        return_value=test_tags_inactive,
    ) as mock_get_data:
        result = get_tags_for_fund_round("test_fund", "test_round", {"tag_status": "False"})
        mock_get_data.assert_called_once()
        mock_get_data.assert_called_with("assessment_store/funds/test_fund/rounds/test_round/tags?tag_status=False")
        assert len(result) == 2
        assert result[0].value == "Val 1 INACTIVE"


def test_get_available_tags_no_tags(assess_test_client):
    with mock.patch("assess.services.data_services.get_data", return_value=[]):
        result = get_tags_for_fund_round("test_fund", "test_round", "")
        assert len(result) == 0


def test_get_associated_tags_for_applications(assess_test_client):
    with mock.patch(
        "assess.services.data_services.get_data",
        return_value=[
            {
                "application_id": "155df6dc-541e-4d7c-82bb-9d8e3b7e52ef",
                "associated": True,
                "purpose": "PEOPLE",
                "tag_id": "c62abab1-41b5-4956-b496-4a8862d748a9",
                "user_id": "00000000-0000-0000-0000-000000000000",
                "value": "test tag",
            }
        ],
    ):
        result = get_associated_tags_for_application("155df6dc-541e-4d7c-82bb-9d8e3b7e52ef")
        assert len(result) == 1
        assert result[0].value == "test tag"


def test_update_associated_tag_returns_true(assess_test_client):
    with mock.patch("requests.put") as mock_put:
        mock_response = mock.Mock()
        mock_response.ok = True
        mock_put.return_value = mock_response

        new_tags = [
            {
                "tag_id": "13c7ba20-1d12-4a08-9a95-76d2fa447db1",
                "user_id": "00000000-0000-0000-0000-000000000000",
            },
            {
                "tag_id": "c62abab1-41b5-4956-b496-4a8862d748a9",
                "user_id": "00000000-0000-0000-0000-000000000000",
            },
            {
                "tag_id": "d74d6bb2-a14d-4d4e-98a9-96731aa94f28",
                "user_id": "00000000-0000-0000-0000-000000000000",
            },
        ]

        result = update_associated_tags("155df6dc-541e-4d7c-82bb-9d8e3b7e52ef", new_tags)
        assert result is True


@pytest.fixture
def mock_get_fund_round(
    mocker,
    mock_get_funds,
    mock_get_fund,
):
    mocker.patch(
        "assess.tagging.routes.get_fund_round",
        return_value={
            "fund_name": "test-fund",
            "round_name": "round 1",
            "fund_id": "TF",
            "round_id": "TR",
        },
    )


@pytest.fixture
def mock_get_tag_and_count(mocker):
    tag_id = "123-123"
    count = 6
    mock_tag = Tag(
        id=tag_id,
        value="tag value 1",
        creator_user_id="test-user",
        active=True,
        purpose="general",
        type_id="abcabc",
        tag_association_count=count,
    )
    mocker.patch("assess.tagging.routes.get_tag", return_value=mock_tag)
    yield (tag_id, count)


def test_edit_tag_get(
    client_with_valid_session,
    mocker,
    mock_get_fund_round,
    mock_get_tag_and_count,
    mock_get_round,
):
    response = client_with_valid_session.get(
        f"/assess/tags/edit/{test_fund_id}/{test_round_id}/{mock_get_tag_and_count[0]}"
    )
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.find("h1").text.strip() == 'Edit tag "tag value 1"'
    assert (
        f"{mock_get_tag_and_count[1]} tagged assessments" in soup.find("strong", class_="govuk-warning-text__text").text
    )


@pytest.mark.parametrize(
    "new_value,return_from_data,expected_response_code,expect_error",
    [
        ("new value", "tag", 302, False),
        ("new value", None, 200, True),
        ("!&asdf£$", "tag", 200, True),
    ],
)
def test_edit_tag_post(
    new_value,
    return_from_data,
    expected_response_code,
    expect_error,
    client_with_valid_session,
    mock_get_fund_round,
    mocker,
    mock_get_tag_and_count,
    mock_get_round,
):
    mocker.patch(
        "assess.tagging.routes.update_tag",
        return_value=return_from_data,
    )
    response = client_with_valid_session.post(
        f"/assess/tags/edit/{test_fund_id}/{test_round_id}/{mock_get_tag_and_count[0]}",
        data={"value": new_value},
        follow_redirects=False,
    )
    assert response.status_code == expected_response_code
    if expect_error:
        soup = BeautifulSoup(response.data, "html.parser")
        assert soup.find("div", class_="govuk-grid-row govuk-error-summary")
