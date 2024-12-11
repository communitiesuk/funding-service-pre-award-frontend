from flask import redirect, render_template, request, url_for

from assess.services.data_services import get_flags, get_fund, get_sub_criteria_banner_state, submit_flag
from assess.shared.helpers import determine_assessment_status, determine_flag_status, get_ttl_hash
from config import Config


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
                "assessment_bp.application",
                application_id=application_id,
            )
        )
    sub_criteria_banner_state = get_sub_criteria_banner_state(application_id)
    flags_list = get_flags(application_id)
    assessment_status = determine_assessment_status(
        state.workflow_status if state else sub_criteria_banner_state.workflow_status,
        state.is_qa_complete,
    )
    flag_status = determine_flag_status(flags_list)

    fund = get_fund(
        sub_criteria_banner_state.fund_id,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
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
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )
