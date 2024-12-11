import datetime
from dataclasses import dataclass

import pytz
from flask import current_app, url_for

from assess.assessments.models.round_status import RoundStatus, determine_round_status
from assess.authentication.validation import (
    AssessmentAccessController,
    get_countries_from_roles,
    has_devolved_authority_validation,
)
from assess.services.data_services import get_application_stats, get_assessments_stats, get_rounds
from assess.services.models.fund import Fund
from assess.shared.helpers import get_ttl_hash
from config import Config
from assess.config.display_value_mappings import LandingFilters


@dataclass
class Stats:
    date: str
    total_received: int
    completed: int
    started: int
    qa_complete: int
    stopped: int


@dataclass
class LiveRoundStats:
    closing_date: str
    not_started: int | None
    in_progress: int | None
    completed: int | None
    submitted: int | None


@dataclass
class RoundSummary:
    status: RoundStatus
    fund_id: str
    round_id: str
    fund_name: str
    round_name: str
    access_controller: AssessmentAccessController
    round_application_fields_download_available: bool
    sorting_date: str
    assessments_href: str = None
    export_href: str = None
    feedback_export_href: str = None
    assessment_tracker_href: str = None
    assessment_stats: Stats | None = None
    live_round_stats: LiveRoundStats = None
    is_expression_of_interest: bool = False


def _add_links_to_summary(summary, fund_short_name, round) -> RoundSummary:
    summary.assessments_href = url_for(
        "assessment_bp.fund_dashboard",
        fund_short_name=fund_short_name,
        round_short_name=round.short_name.lower(),
    )
    summary.export_href = url_for(
        "assessment_bp.assessor_export",
        fund_short_name=fund_short_name,
        round_short_name=round.short_name.lower(),
        report_type="ASSESSOR_EXPORT",
    )
    summary.assessment_tracker_href = (
        url_for(
            "assessment_bp.assessor_export",
            fund_short_name=fund_short_name,
            round_short_name=round.short_name.lower(),
            report_type="OUTPUT_TRACKER",
        )
        if not round.is_expression_of_interest
        else None
    )
    summary.feedback_export_href = (
        url_for(
            "assessment_bp.feedback_export",
            fund_short_name=fund_short_name,
            round_short_name=round.short_name.lower(),
        )
        if (round.feedback_survey_config.has_feedback_survey or round.feedback_survey_config.has_section_feedback)
        else ""
    )
    return summary


def _populate_assessment_stats(
    fund_id, round_ids_to_fetch_assessment_stats, search_params, round_id_to_summary_map
) -> dict:
    round_id_to_round_stats = get_assessments_stats(fund_id, round_ids_to_fetch_assessment_stats, search_params)
    for round_id, round_stats in round_id_to_round_stats.items():
        summary = round_id_to_summary_map[round_id]
        summary.assessment_stats = Stats(
            date=summary.sorting_date,  # which is same as round.assessment_deadline
            total_received=round_stats["total"],
            completed=round_stats["completed"],
            started=round_stats["assessing"],
            qa_complete=round_stats["qa_completed"],
            stopped=round_stats["stopped"],
        )
    return round_id_to_summary_map


def _populate_live_round_stats(round_id_to_summary_map, live_rounds, fund) -> dict:
    live_rounds_map = {r.id: r for r in live_rounds}
    round_stats = get_application_stats([fund.id], [r.id for r in live_rounds])
    if not round_stats:
        current_app.logger.warning("Error retrieving round stats, application-store may be down.")
        for live_round_id in live_rounds_map:
            live_round = live_rounds_map[live_round_id]
            round_id_to_summary_map[live_round_id].live_round_stats = LiveRoundStats(
                closing_date=live_round.deadline,
                not_started=None,
                in_progress=None,
                completed=None,
                submitted=None,
            )
    else:
        this_fund_stats = next(f for f in round_stats["metrics"] if f["fund_id"] == fund.id)
        for this_round_stats in this_fund_stats["rounds"]:
            current_round_id = this_round_stats["round_id"]
            if current_round_id not in live_rounds_map:
                continue

            statuses = this_round_stats["application_statuses"]
            live_round = live_rounds_map[current_round_id]
            round_id_to_summary_map[current_round_id].live_round_stats = LiveRoundStats(
                closing_date=live_round.deadline,
                not_started=statuses["NOT_STARTED"],
                in_progress=statuses["IN_PROGRESS"],
                completed=statuses["COMPLETED"],
                submitted=statuses["SUBMITTED"],
            )
    return round_id_to_summary_map


def create_round_summaries(fund: Fund, filters: LandingFilters) -> list[RoundSummary]:  # noqa: C901
    """Get all the round stats in a fund."""
    access_controller = AssessmentAccessController(fund.short_name)

    search_params = {}
    if has_devolved_authority_validation(fund_id=fund.id):
        countries = get_countries_from_roles(fund.short_name)
        search_params = {"countries": ",".join(countries)}

    summaries = []
    live_rounds = []
    round_id_to_summary_map = {}
    round_ids_to_fetch_assessment_stats = set()
    for round in get_rounds(fund.id, ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME)):
        round_status: RoundStatus = determine_round_status(round=round)

        # Filter for closed assessments
        if filters.filter_status == "closed" and not round_status.has_assessment_closed:
            continue

        # Filter for active assessments
        if filters.filter_status == "active" and not round_status.is_assessment_active:
            continue

        # Filter for live application windows
        if filters.filter_status == "live" and not round_status.is_application_open:
            continue

        # Commenters can't see rounds that haven't started assessment yet
        if not round_status.has_assessment_opened and not access_controller.has_any_assessor_role:
            continue

        sorting_date = round.deadline

        if round_status.is_application_open:
            live_rounds.append(round)
        elif round.is_expression_of_interest:
            live_rounds.append(round)

        if round_status.is_application_not_yet_open:
            sorting_date = round.assessment_deadline

        if round_status.has_assessment_opened:
            round_ids_to_fetch_assessment_stats.add(round.id)
            sorting_date = round.assessment_deadline

        summary = RoundSummary(
            status=round_status,
            fund_id=fund.id,
            round_id=round.id,
            fund_name=fund.name,
            round_name=round.title,
            assessment_stats=None,  # populated later, with a bulk request,
            access_controller=access_controller,
            round_application_fields_download_available=round.application_fields_download_available,
            sorting_date=sorting_date,
            is_expression_of_interest=round.is_expression_of_interest,
        )
        round_id_to_summary_map[round.id] = _add_links_to_summary(summary, fund.short_name, round)
        summaries.append(summary)

    if round_ids_to_fetch_assessment_stats:
        round_id_to_summary_map = _populate_assessment_stats(
            fund_id=fund.id,
            round_ids_to_fetch_assessment_stats=round_ids_to_fetch_assessment_stats,
            search_params=search_params,
            round_id_to_summary_map=round_id_to_summary_map,
        )

    if live_rounds:
        round_id_to_summary_map = _populate_live_round_stats(round_id_to_summary_map, live_rounds, fund)

    return sorted(summaries, key=lambda s: s.sorting_date, reverse=True)


def is_after_today(date_str: str):
    """Check if the provided datetime string has passed the current datetime"""
    uk_tz = pytz.timezone("Europe/London")
    date_format = "%Y-%m-%dT%H:%M:%S"
    dt = datetime.datetime.strptime(date_str, date_format)
    dt_uk = uk_tz.localize(dt)
    now_uk = datetime.datetime.now(tz=uk_tz)
    return dt_uk > now_uk
