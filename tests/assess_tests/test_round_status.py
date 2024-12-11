from datetime import datetime, timedelta

import pytest

from assess.assessments.models.round_status import RoundStatus, determine_round_status
from assess.services.models.round import Round


def test_determine_round_status_open():
    r = Round(
        id="",
        assessment_start=(datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
        assessment_deadline=(datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"),
        deadline=(datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
        opens=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
        fund_id="",
        title="",
        short_name="",
    )
    result: RoundStatus = determine_round_status(r)
    assert result.has_assessment_closed is False
    assert result.has_assessment_opened is False
    assert result.has_application_closed is False
    assert result.is_application_open is True
    assert result.is_application_not_yet_open is False
    assert result.is_assessment_active is False


@pytest.mark.parametrize(
    "deadline_delta,assessment_start_delta,assessment_deadline_delta,exp_assessment_active",
    [
        (5, None, 10, False),
        (5, 5, 10, False),
        (-5, -5, 10, True),
        (-5, None, 10, True),
        (-5, None, -2, False),
        (-5, -5, -2, False),
    ],
)
def test_determine_round_status_is_assessment_active(
    deadline_delta,
    assessment_start_delta,
    assessment_deadline_delta,
    exp_assessment_active: bool,
):
    r = Round(
        id="",
        assessment_start=(
            (datetime.now() + timedelta(days=assessment_start_delta)).strftime("%Y-%m-%d %H:%M:%S")
            if assessment_start_delta
            else None
        ),
        assessment_deadline=(datetime.now() + timedelta(days=assessment_deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        deadline=(datetime.now() + timedelta(days=deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        opens=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        fund_id="",
        title="",
        short_name="",
    )
    result: RoundStatus = determine_round_status(r)
    assert result.is_assessment_active is exp_assessment_active


@pytest.mark.parametrize(
    "deadline_delta,assessment_start_delta,assessment_deadline_delta,exp_assessment_opened",
    [
        (5, None, 10, False),
        (5, 5, 10, False),
        (-5, -5, 10, True),
        (-5, None, 10, True),
        (-5, None, -2, True),
        (-5, -5, -2, True),
    ],
)
def test_determine_round_status_has_assessment_opened(
    deadline_delta,
    assessment_start_delta,
    assessment_deadline_delta,
    exp_assessment_opened: bool,
):
    r = Round(
        id="",
        assessment_start=(
            (datetime.now() + timedelta(days=assessment_start_delta)).strftime("%Y-%m-%d %H:%M:%S")
            if assessment_start_delta
            else None
        ),
        assessment_deadline=(datetime.now() + timedelta(days=assessment_deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        deadline=(datetime.now() + timedelta(days=deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        opens=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        fund_id="",
        title="",
        short_name="",
    )
    result: RoundStatus = determine_round_status(r)
    assert result.has_assessment_opened is exp_assessment_opened


@pytest.mark.parametrize(
    "deadline_delta,assessment_start_delta,assessment_deadline_delta,exp_assessment_closed",
    [
        (5, None, 10, False),
        (5, 5, 10, False),
        (-5, -5, 10, False),
        (-5, None, 10, False),
        (-5, None, -2, True),
        (-5, -5, -2, True),
    ],
)
def test_determine_round_status_has_assessment_closed(
    deadline_delta,
    assessment_start_delta,
    assessment_deadline_delta,
    exp_assessment_closed: bool,
):
    r = Round(
        id="",
        assessment_start=(
            (datetime.now() + timedelta(days=assessment_start_delta)).strftime("%Y-%m-%d %H:%M:%S")
            if assessment_start_delta
            else None
        ),
        assessment_deadline=(datetime.now() + timedelta(days=assessment_deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        deadline=(datetime.now() + timedelta(days=deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        opens=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        fund_id="",
        title="",
        short_name="",
    )
    result: RoundStatus = determine_round_status(r)
    assert result.has_assessment_closed is exp_assessment_closed


@pytest.mark.parametrize(
    "opens_delta,deadline_delta,exp_app_open",
    [
        (5, 10, False),
        (-5, 10, True),
        (-5, -1, False),
    ],
)
def test_determine_round_status_is_app_open(deadline_delta, opens_delta, exp_app_open: bool):
    r = Round(
        id="",
        assessment_start=None,
        assessment_deadline=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        deadline=(datetime.now() + timedelta(days=deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        opens=(datetime.now() + timedelta(days=opens_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        fund_id="",
        title="",
        short_name="",
    )
    result: RoundStatus = determine_round_status(r)
    assert result.is_application_open is exp_app_open


@pytest.mark.parametrize(
    "opens_delta,deadline_delta,exp_app_closed",
    [
        (5, 10, False),
        (-5, 10, False),
        (-5, -1, True),
    ],
)
def test_determine_round_status_is_app_closed(deadline_delta, opens_delta, exp_app_closed: bool):
    r = Round(
        id="",
        assessment_start=None,
        assessment_deadline=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        deadline=(datetime.now() + timedelta(days=deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        opens=(datetime.now() + timedelta(days=opens_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        fund_id="",
        title="",
        short_name="",
    )
    result: RoundStatus = determine_round_status(r)
    assert result.has_application_closed is exp_app_closed


@pytest.mark.parametrize(
    "opens_delta,deadline_delta,exp_app_not_yet_open",
    [
        (5, 10, True),
        (-5, 10, False),
        (-5, -1, False),
    ],
)
def test_determine_round_status_is_app_not_yet_open(deadline_delta, opens_delta, exp_app_not_yet_open: bool):
    r = Round(
        id="",
        assessment_start=None,
        assessment_deadline=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        deadline=(datetime.now() + timedelta(days=deadline_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        opens=(datetime.now() + timedelta(days=opens_delta)).strftime("%Y-%m-%d %H:%M:%S"),
        fund_id="",
        title="",
        short_name="",
    )
    result: RoundStatus = determine_round_status(r)
    assert result.is_application_not_yet_open is exp_app_not_yet_open
