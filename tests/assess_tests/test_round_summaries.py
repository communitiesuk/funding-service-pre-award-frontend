from unittest.mock import MagicMock, patch

import pytest

from assess.assessments.models.round_status import RoundStatus
from assess.assessments.models.round_summary import create_round_summaries
from assess.services.models.round import Round
from assess.config.display_value_mappings import ALL_VALUE


@pytest.fixture(autouse=True)
def mock_summaries_helpers(mocker):
    mocker.patch(
        "assess.assessments.models.round_summary._add_links_to_summary",
        return_value=lambda summaries, fsn, r: summaries,
    )
    mocker.patch(
        "assess.assessments.models.round_summary.has_devolved_authority_validation",
        return_value=False,
    )


@pytest.fixture
def mock_live_stats(mocker):
    mock_populate_live_stats = mocker.patch(
        "assess.assessments.models.round_summary._populate_live_round_stats",
        return_value=lambda results, lr, f: results,
    )
    yield mock_populate_live_stats


@pytest.fixture
def mock_assessment_stats(mocker):
    mock_populate_assessment_stats = mocker.patch(
        "assess.assessments.models.round_summary._populate_assessment_stats",
        return_value=lambda f, fetch, sp, results: results,
    )
    yield mock_populate_assessment_stats


@pytest.fixture
def mock_get_round(mocker):
    mocker.patch(
        "assess.assessments.models.round_summary.get_rounds",
        return_value=[
            Round.from_dict(
                {
                    "assessment_deadline": ASSESSMENT_DEADLINE,
                    "deadline": APPLICATION_DEADLINE,
                    **default_round,
                }
            )
        ],
    )


def test_create_round_summaries_no_rounds(mocker, mock_live_stats, mock_assessment_stats):
    mocker.patch(
        "assess.assessments.models.round_summary.determine_round_status",
        return_value=RoundStatus(False, False, False, False, False, False),
    )
    mocker.patch("assess.assessments.models.round_summary.get_rounds", return_value=[])

    mock_fund = MagicMock()
    results = create_round_summaries(mock_fund, [])
    assert len(results) == 0


ASSESSMENT_DEADLINE = "2124-01-01 12:00:00"
APPLICATION_DEADLINE = "2324-01-01 12:00:00"
default_round = {
    "id": "",
    "assessment_start": "",
    "fund_id": "",
    "opens": "",
    "title": "",
    "short_name": "",
}


@pytest.mark.parametrize("filter_status", [(ALL_VALUE), "closed"])
def test_create_round_summaries_assessment_closed(
    mocker, mock_live_stats, mock_assessment_stats, mock_get_round, filter_status
):
    mocker.patch(
        "assess.assessments.models.round_summary.determine_round_status",
        return_value=RoundStatus(False, False, False, False, True, True),
    )
    mock_fund = MagicMock()
    mock_landing_filters = MagicMock()
    mock_landing_filters.filter_status = filter_status
    with patch("assess.assessments.models.round_summary.AssessmentAccessController") as mock:
        instance = mock.return_value
        instance.has_any_assessor_role = True
        results = create_round_summaries(mock_fund, mock_landing_filters)
        assert len(results) == 1
        assert results[0].sorting_date == ASSESSMENT_DEADLINE

        mock_live_stats.assert_not_called()
        mock_assessment_stats.assert_called_once()


@pytest.mark.parametrize("filter_status", [(ALL_VALUE), "live"])
def test_create_round_summaries_live_round(
    mocker, mock_live_stats, mock_assessment_stats, mock_get_round, filter_status
):
    mocker.patch(
        "assess.assessments.models.round_summary.determine_round_status",
        return_value=RoundStatus(False, True, False, False, False, False),
    )
    mock_fund = MagicMock()
    mock_landing_filters = MagicMock()
    mock_landing_filters.filter_status = filter_status
    with patch("assess.assessments.models.round_summary.AssessmentAccessController") as mock:
        instance = mock.return_value
        instance.has_any_assessor_role = True
        results = create_round_summaries(mock_fund, mock_landing_filters)
        assert len(results) == 1
        assert results[0].sorting_date == APPLICATION_DEADLINE

        mock_live_stats.assert_called_once()
        mock_assessment_stats.assert_not_called()


@pytest.mark.parametrize("filter_status", [(ALL_VALUE), "active", "live"])
def test_create_round_summaries_assess_active_and_round_live(
    mocker, mock_live_stats, mock_assessment_stats, mock_get_round, filter_status
):
    mocker.patch(
        "assess.assessments.models.round_summary.determine_round_status",
        return_value=RoundStatus(False, True, False, True, True, False),
    )
    mock_fund = MagicMock()
    mock_landing_filters = MagicMock()
    mock_landing_filters.filter_status = filter_status
    with patch("assess.assessments.models.round_summary.AssessmentAccessController") as mock:
        instance = mock.return_value
        instance.has_any_assessor_role = True
        results = create_round_summaries(mock_fund, mock_landing_filters)
        assert len(results) == 1
        assert results[0].sorting_date == ASSESSMENT_DEADLINE

        mock_live_stats.assert_called_once()
        mock_assessment_stats.assert_called_once()


@pytest.mark.parametrize(
    "is_application_open,has_assessment_opened,is_assessment_active,has_assessor_roles,filter_value",
    [
        (True, False, False, False, ALL_VALUE),
        (False, True, True, True, "closed"),
        (False, True, False, True, "active"),
        (False, True, True, True, "live"),
    ],
)
def test_create_round_summaries_no_results(
    mocker,
    mock_live_stats,
    mock_assessment_stats,
    mock_get_round,
    is_application_open,
    has_assessment_opened,
    is_assessment_active,
    has_assessor_roles,
    filter_value,
):
    mocker.patch(
        "assess.assessments.models.round_summary.determine_round_status",
        return_value=RoundStatus(
            False,
            is_application_open,
            False,
            is_assessment_active,
            has_assessment_opened,
            False,
        ),
    )
    mock_fund = MagicMock()
    mock_landing_filters = MagicMock()
    mock_landing_filters.filter_status = filter_value
    with patch("assess.assessments.models.round_summary.AssessmentAccessController") as mock:
        instance = mock.return_value
        instance.has_any_assessor_role = has_assessor_roles
        results = create_round_summaries(mock_fund, mock_landing_filters)
        assert len(results) == 0

        mock_live_stats.assert_not_called()
        mock_assessment_stats.assert_not_called()


@pytest.mark.parametrize(
    "is_application_open,is_expression_of_interest,num_results",
    [
        (True, False, 1),
        (False, True, 1),
        (True, True, 1),
    ],
)
def test_create_round_summaries_eoi(
    mocker,
    mock_live_stats,
    mock_assessment_stats,
    is_application_open,
    is_expression_of_interest,
    num_results,
):
    mocker.patch(
        "assess.assessments.models.round_summary.determine_round_status",
        return_value=RoundStatus(False, is_application_open, False, False, False, False),
    )
    mocker.patch(
        "assess.assessments.models.round_summary.get_rounds",
        return_value=[
            Round.from_dict(
                {
                    "assessment_deadline": ASSESSMENT_DEADLINE,
                    "deadline": APPLICATION_DEADLINE,
                    "is_expression_of_interest": is_expression_of_interest,
                    "is_application_open": is_application_open,
                    **default_round,
                }
            )
        ],
    )

    mock_fund = MagicMock()
    mock_landing_filters = MagicMock()
    mock_landing_filters.filter_status = ALL_VALUE
    with patch("assess.assessments.models.round_summary.AssessmentAccessController") as mock:
        instance = mock.return_value
        instance.has_any_assessor_role = True
        results = create_round_summaries(mock_fund, mock_landing_filters)
        assert len(results) == num_results

        mock_live_stats.assert_called_once()
