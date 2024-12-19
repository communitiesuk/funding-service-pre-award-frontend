import time
from typing import Dict, List

from flask import request

from assess.config.display_value_mappings import LandingFilters, assessment_statuses
from assess.services.models.flag import Flag, FlagType
from assess.services.models.fund import Fund


def process_assessments_stats(application_overviews) -> Dict:
    num_completed = 0
    num_assessing = 0
    num_not_started = 0
    num_qa_completed = 0
    num_stopped = 0
    num_flagged = 0
    num_multiple_flagged = 0

    for assessment in application_overviews:
        status = determine_display_status(
            assessment["workflow_status"],
            assessment["flags"],
            assessment["is_qa_complete"],
        )
        if status == "Assessment complete":
            num_completed += 1
        elif status == "In progress":
            num_assessing += 1
        elif status == "Not started":
            num_not_started += 1
        elif status == "QA complete":
            num_qa_completed += 1
        elif status == "Stopped":
            num_stopped += 1
        elif status == "Flagged":
            num_flagged += 1
        elif status == "Multiple flags to resolve":
            num_multiple_flagged += 1

    stats = {
        "completed": num_completed,
        "assessing": num_assessing,
        "not_started": num_not_started,
        "qa_completed": num_qa_completed,
        "stopped": num_stopped,
        "flagged": num_flagged,
        "multiple_flagged": num_multiple_flagged,
        "total": len(application_overviews),
    }

    return stats


def determine_assessment_status(workflow_status: str, is_qa_complete: bool) -> str:
    if is_qa_complete:
        assessment_status = "QA complete"
    else:
        assessment_status = assessment_statuses[workflow_status]

    return assessment_status


def is_flaggable(flag_status: str):
    return flag_status != "Stopped"


def determine_display_status(workflow_status: str, Flags: List[Flag], is_qa_complete: bool) -> str:
    flag_status = determine_flag_status(Flags)
    if flag_status:
        display_status = flag_status
    elif is_qa_complete:
        display_status = "QA complete"
    else:
        display_status = assessment_statuses[workflow_status]

    return display_status


def determine_flag_status(Flags: List[Flag]) -> str:
    flag_status = ""
    flags_list = [(Flag.from_dict(flag) if isinstance(flag, dict) else flag) for flag in Flags] if Flags else []
    all_latest_status = [flag.latest_status for flag in flags_list]

    if FlagType.STOPPED in all_latest_status:
        flag_status = "Stopped"
    elif all_latest_status.count(FlagType.RAISED) > 1:
        flag_status = "Multiple flags to resolve"
    elif all_latest_status.count(FlagType.RAISED) == 1:
        for flag in flags_list:
            if flag.latest_status == FlagType.RAISED:
                flag_status = ("Flagged for " + flag.latest_allocation) if flag.latest_allocation else "Flagged"
    return flag_status


def match_search_params(search_params, request_args):
    show_clear_filters = False
    if "clear_filters" not in request_args:
        search_params.update({k: v for k, v in request_args.items() if k in search_params and k != "countries"})
        show_clear_filters = any(k in request_args for k in search_params if k != "countries")
    return search_params, show_clear_filters


def get_ttl_hash(seconds=3600) -> int:
    """
    The @lru_cache decorator from the functools module in Python
    requires that the decorated function takes arguments that are
    hashable so that it can use those arguments as keys in its cache.

    get_ttl_hash exploits the fact that lru_cache depends
    on the 'ttl_hash' argument. The ttl_hash (result of this function)
    will stay the same within a time period. If seconds is exceeded
    within time.time(), we get a different hash value.
    ttl_hash changes. lru_cache can't find a cache key for this new value and
    calls the cacheable function.
    (deleting the other if it exceeds the maxsize cache limit).
    """
    return round(time.time() / seconds)


def get_value_from_request(parameter_names) -> str | None:
    for parameter_name in parameter_names:
        view_args = request.view_args or {}
        value = view_args.get(parameter_name) or request.args.get(parameter_name)
        if value:
            return value


def fund_matches_filters(fund: Fund, filters: LandingFilters):
    if filters.filter_fund_name.casefold() not in fund.name.casefold():
        return False
    if filters.filter_fund_type not in fund.fund_types:
        return False
    return True
