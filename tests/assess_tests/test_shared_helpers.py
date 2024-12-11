import pytest

from assess.services.models.assessor_task_list import AssessorTaskList
from assess.services.shared_data_helpers import get_state_for_tasklist_banner


def mock_task_list(sections=None, criterias=None):
    if criterias is None:
        criterias = []
    if sections is None:
        sections = []
    return AssessorTaskList.from_json({"sections": sections, "criterias": criterias})


@pytest.mark.application_id("resolved_app")
@pytest.mark.sub_criteria_id("test_sub_criteria_id")
def test_pagination_helper_should_parse_with_real_backend_data(
    mock_get_sub_criteria,
    mock_get_fund,
    mock_get_round,
    mock_get_assessor_tasklist_state,
):
    # make sure the helper appropriately loads and parses pagination from backend services by mocking out those calls
    state = get_state_for_tasklist_banner("resolved_app")
    pagination = state.get_pagination_from_sub_criteria_id("test_sub_criteria_id")

    assert pagination["previous"]["sub_section_name"] == "A fixed sub criteria"
    assert pagination["next"] is None


def test_pagination_should_be_none_for_missing_section_id():
    state = mock_task_list(sections=[], criterias=[])
    assert state.get_pagination_from_sub_criteria_id("missing-sub-criteria-id") is None


def test_pagination_should_be_empty_with_only_one_section():
    state = mock_task_list(
        sections=[
            {
                "name": "first-group",
                "sub_criterias": [{"id": "first-section", "name": "A sub criteria"}],
            }
        ],
    )
    pagination = state.get_pagination_from_sub_criteria_id("first-section")
    assert pagination["previous"] is None
    assert pagination["next"] is None


multiple_sections_state = mock_task_list(
    sections=[
        {
            "name": "first-group",
            "sub_criterias": [
                {"id": "first-section", "name": "A sub criteria"},
                {"id": "second-section", "name": "A second sub criteria"},
                {"id": "third-section", "name": "A third sub criteria"},
            ],
        },
        {
            "name": "second-group",
            "sub_criterias": [
                {
                    "id": "first-section-second-group",
                    "name": "A sub criteria for the second group",
                },
            ],
        },
    ],
    # Note that sections and criterias are treated the same on the task list detail page
    criterias=[
        {
            "name": "first-group-criterias",
            "sub_criterias": [
                {
                    "id": "criteria-id",
                    "name": "A first criteria name",
                    "theme_count": 1,
                    "score": 4,
                    "status": "string",
                },
                {
                    "id": "second-criteria-id",
                    "name": "A second criteria name",
                    "theme_count": 1,
                    "score": 4,
                    "status": "string",
                },
            ],
            "total_criteria_score": 4,
            "number_of_scored_sub_criteria": 5,
            "weighting": 0,
        }
    ],
)


def test_pagination_should_have_empty_previous_when_loading_first_section():
    pagination = multiple_sections_state.get_pagination_from_sub_criteria_id("first-section")
    assert pagination["previous"] is None
    assert pagination["next"]["sub_section_id"] == "second-section"


def test_pagination_should_have_empty_next_when_loading_last_section():
    pagination = multiple_sections_state.get_pagination_from_sub_criteria_id("second-criteria-id")
    assert pagination["previous"]["sub_section_id"] == "criteria-id"
    assert pagination["next"] is None


def test_pagination_should_have_previous_next_when_loading_within_section_group():
    pagination = multiple_sections_state.get_pagination_from_sub_criteria_id("second-section")
    assert pagination["previous"]["sub_section_id"] == "first-section"
    assert pagination["next"]["sub_section_id"] == "third-section"


def test_pagination_should_have_previous_next_when_loading_across_section_groups():
    # This should get the last section from the first group and the first section from the critereas group
    pagination = multiple_sections_state.get_pagination_from_sub_criteria_id("first-section-second-group")
    assert pagination["previous"]["sub_section_id"] == "third-section"
    assert pagination["next"]["sub_section_id"] == "criteria-id"
