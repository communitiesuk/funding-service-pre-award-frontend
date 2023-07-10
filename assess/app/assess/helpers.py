import time
from typing import List

from app.assess.data import get_flags
from app.assess.data import get_fund
from app.assess.data import get_sub_criteria_banner_state
from app.assess.data import submit_flag
from app.assess.display_value_mappings import assessment_statuses
from app.assess.models.flag_v2 import FlagTypeV2
from app.assess.models.flag_v2 import FlagV2
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for


def get_ttl_hash(seconds=3600) -> int:
    return round(time.time() / seconds)


def get_application_id_from_request() -> str | None:
    application_id = (
        request.view_args.get("application_id")
        or request.view_args.get("application")
        or request.args.get("application_id")
        or request.args.get("application")
    )
    return application_id


def get_fund_short_name_from_request() -> str | None:
    fund_short_name = (
        request.view_args.get("fund_short_name")
        or request.view_args.get("fund_short_name")
        or request.args.get("fund_short_name")
        or request.args.get("fund_short_name")
    )
    return fund_short_name


def determine_flag_status(Flags: List[FlagV2]) -> str:
    flag_status = ""
    flags_list = (
        [
            (FlagV2.from_dict(flag) if isinstance(flag, dict) else flag)
            for flag in Flags
        ]
        if Flags
        else []
    )
    all_latest_status = [flag.latest_status for flag in flags_list]

    if FlagTypeV2.STOPPED in all_latest_status:
        flag_status = "Stopped"
    elif all_latest_status.count(FlagTypeV2.RAISED) > 1:
        flag_status = "Multiple flags to resolve"
    elif all_latest_status.count(FlagTypeV2.RAISED) == 1:
        for flag in flags_list:
            if flag.latest_status == FlagTypeV2.RAISED:
                flag_status = (
                    ("Flagged for " + flag.latest_allocation)
                    if flag.latest_allocation
                    else "Flagged"
                )
    return flag_status


def determine_display_status(workflow_status: str, Flags: List[FlagV2]) -> str:
    flag_status = determine_flag_status(Flags)
    if flag_status:
        display_status = flag_status
    elif is_qa_complete(Flags):
        display_status = "QA complete"
    else:
        display_status = assessment_statuses[workflow_status]

    return display_status


def determine_assessment_status(
    workflow_status: str, Flags: List[FlagV2]
) -> str:
    if is_qa_complete(Flags):
        assessment_status = "QA complete"
    else:
        assessment_status = assessment_statuses[workflow_status]

    return assessment_status


def is_flaggable(flag_status: str):
    return flag_status != "Stopped"


def is_qa_complete(Flags: List[FlagV2]) -> bool:
    # TODO: Rework on this when QA_COMPLETED is moved to assessment enum type
    flags_list = (
        [
            (FlagV2.from_dict(flag) if isinstance(flag, dict) else flag)
            for flag in Flags
        ]
        if Flags
        else []
    )
    all_latest_status = [flag.latest_status for flag in flags_list]
    return FlagTypeV2.QA_COMPLETED in all_latest_status or False


def set_application_status_in_overview(application_overviews):
    """Add the 'application_status' key and return the modified list of application overviews."""
    for overview in application_overviews:
        display_status = determine_display_status(
            overview["workflow_status"], overview["flags_v2"]
        )
        status = ""
        for key, val in assessment_statuses.items():
            if val == display_status:
                status = key
                break
        if not status:
            status = display_status
        overview["application_status"] = status

    return application_overviews


def resolve_application(
    form,
    application_id,
    flag,
    user_id,
    justification,
    section,
    page_to_render,
    state=None,
    reason_to_flag="",
    allocated_team="",
    flag_id="",
):
    """This function is used to resolve an application
      by submitting a flag, justification, and section for the application.

    Args:
        form (obj): Form object to be validated and submitted
        application_id (int): ID of the application
        flag (str): Flag submitted for the application
        justification (str): Justification for the flag submitted
        section (str): Section of the application the flag is submitted for
        page_to_render (str): Template name to be rendered

    Returns:
        redirect: Redirects to the application page if the request method is
                  "POST" and form is valid.
        render_template: Renders the specified template with the
                         application_id, fund_name, state, form, and referrer
                         as parameters.
    """
    if request.method == "POST" and form.validate_on_submit():
        submit_flag(
            application_id,
            flag,
            user_id,
            justification,
            section,
            allocated_team,
            flag_id,
        )
        return redirect(
            url_for(
                "assess_bp.application",
                application_id=application_id,
            )
        )
    sub_criteria_banner_state = get_sub_criteria_banner_state(application_id)
    flags_list = get_flags(application_id)
    assessment_status = determine_assessment_status(
        state.workflow_status
        if state
        else sub_criteria_banner_state.workflow_status,
        flags_list,
    )
    flag_status = determine_flag_status(flags_list)

    fund = get_fund(sub_criteria_banner_state.fund_id)
    return render_template(
        page_to_render,
        application_id=application_id,
        fund=fund,
        sub_criteria=sub_criteria_banner_state,
        form=form,
        referrer=request.referrer,
        assessment_status=assessment_status,
        flag_status=flag_status,
        state=state,
        sections_to_flag=section,
        reason_to_flag=reason_to_flag,
        allocated_team=allocated_team,
    )
