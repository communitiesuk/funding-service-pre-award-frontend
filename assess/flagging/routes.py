from flask import abort, current_app, g, redirect, render_template, request, url_for

from assess.authentication.validation import check_access_application_id
from assess.flagging.forms.continue_application_form import (
    ContinueApplicationForm,
)
from assess.flagging.forms.flag_form import FlagApplicationForm
from assess.flagging.forms.resolve_flag_form import ResolveFlagForm
from assess.flagging.helpers import resolve_application
from assess.services.data_services import (
    get_available_teams,
    get_flag,
    get_flags,
    get_sub_criteria_banner_state,
    submit_flag,
)
from assess.services.models.flag import FlagType
from assess.services.shared_data_helpers import get_state_for_tasklist_banner
from assess.shared.helpers import determine_assessment_status, determine_flag_status, get_ttl_hash
from common.blueprints import Blueprint
from config import Config

flagging_bp = Blueprint(
    "flagging_bp",
    __name__,
    url_prefix=Config.ASSESSMENT_HUB_ROUTE,
    template_folder="templates",
)


@flagging_bp.route(
    "/flag/<application_id>",
    methods=["GET", "POST"],
)
@check_access_application_id(roles_required=["ASSESSOR"])
def flag(application_id):
    # Get assessor tasks list
    state = get_state_for_tasklist_banner(application_id)
    choices = [(item["sub_section_id"], item["sub_section_name"]) for item in state.get_sub_sections_metadata()]

    teams_available = get_available_teams(
        state.fund_id,
        state.round_id,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )

    form = FlagApplicationForm(
        section_choices=choices,
        team_choices=[team["value"] for team in teams_available],
    )

    if request.method == "POST" and form.validate_on_submit():
        submit_flag(
            application_id,
            FlagType.RAISED.name,
            g.account_id,
            form.justification.data,
            form.section.data,
            form.teams_available.data,
        )
        return redirect(
            url_for(
                "assessment_bp.application",
                application_id=application_id,
            )
        )

    sub_criteria_banner_state = get_sub_criteria_banner_state(application_id)

    flags_list = get_flags(application_id)
    assessment_status = determine_assessment_status(state.workflow_status, state.is_qa_complete)
    flag_status = determine_flag_status(flags_list)
    return render_template(
        "flagging/flag_application.html",
        application_id=application_id,
        flag=flag,
        sub_criteria=sub_criteria_banner_state,
        form=form,
        assessment_status=assessment_status,
        flag_status=flag_status,
        referrer=request.referrer,
        state=state,
        teams_available=teams_available,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


@flagging_bp.route("/resolve_flag/<application_id>", methods=["GET", "POST"])
@check_access_application_id(roles_required=["LEAD_ASSESSOR"])
def resolve_flag(application_id):
    form = ResolveFlagForm()
    flag_id = request.args.get("flag_id")

    if not flag_id:
        current_app.logger.error("No flag id found in query params")
        abort(404)
    flag_data = get_flag(flag_id)
    state = get_state_for_tasklist_banner(application_id)
    section = flag_data.sections_to_flag
    return resolve_application(
        form=form,
        application_id=application_id,
        flag=form.resolution_flag.data,
        user_id=g.account_id,
        justification=form.justification.data,
        section=section,
        page_to_render="flagging/resolve_flag.html",
        state=state,
        reason_to_flag=flag_data.updates[-1]["justification"],
        allocated_team=flag_data.updates[-1]["allocation"],
        flag_id=flag_id,
    )


@flagging_bp.route("/continue_assessment/<application_id>", methods=["GET", "POST"])
@check_access_application_id(roles_required=["LEAD_ASSESSOR"])
def continue_assessment(application_id):
    form = ContinueApplicationForm()
    flag_id = request.args.get("flag_id")

    if not flag_id:
        current_app.logger.error("No flag id found in query params")
        abort(404)
    flag_data = get_flag(flag_id)
    return resolve_application(
        form=form,
        application_id=application_id,
        flag=FlagType.RESOLVED.name,
        user_id=g.account_id,
        justification=form.reason.data,
        section=["NA"],
        state=get_state_for_tasklist_banner(application_id),
        page_to_render="flagging/continue_assessment.html",
        reason_to_flag=flag_data.updates[-1]["justification"],
        allocated_team=flag_data.updates[-1]["allocation"],
        flag_id=flag_id,
    )
