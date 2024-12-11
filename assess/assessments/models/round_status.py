from dataclasses import dataclass

from fsd_utils.simple_utils.date_utils import (
    current_datetime_after_given_iso_string,
    current_datetime_before_given_iso_string,
)

from assess.services.data_services import get_round
from assess.services.models.round import Round
from assess.shared.helpers import get_ttl_hash
from config import Config


@dataclass
class RoundStatus:
    is_application_not_yet_open: bool
    is_application_open: bool
    has_application_closed: bool
    is_assessment_active: bool
    has_assessment_opened: bool
    has_assessment_closed: bool


def determine_round_status(round: Round = None, fund_id: str = None, round_id: str = None) -> RoundStatus:
    if not round:
        round = get_round(
            fund_id,
            round_id,
            ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
        )
    has_assessment_opened = (
        current_datetime_after_given_iso_string(round.assessment_start)
        if round.assessment_start
        else current_datetime_after_given_iso_string(round.deadline)
    )
    has_assessment_closed = current_datetime_after_given_iso_string(round.assessment_deadline)
    result = RoundStatus(
        is_application_not_yet_open=current_datetime_before_given_iso_string(round.opens),
        is_application_open=current_datetime_after_given_iso_string(round.opens)
        and current_datetime_before_given_iso_string(round.deadline),
        has_application_closed=current_datetime_after_given_iso_string(round.deadline),
        has_assessment_opened=has_assessment_opened,
        has_assessment_closed=has_assessment_closed,
        is_assessment_active=has_assessment_opened and not has_assessment_closed,
    )

    return result
