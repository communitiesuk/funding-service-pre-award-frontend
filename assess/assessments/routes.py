import concurrent.futures
import contextvars
import functools
import io
import itertools
import json
import time
import zipfile
from collections import OrderedDict
from datetime import datetime
from urllib.parse import quote_plus, unquote_plus

from flask import (
    Response,
    abort,
    current_app,
    escape,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from fsd_utils import extract_questions_and_answers
from fsd_utils.sqs_scheduler.context_aware_executor import ContextAwareExecutor
from werkzeug.datastructures import ImmutableMultiDict, MultiDict

from assess.assessments.activity_trail import (
    AssociatedTags,
    CheckboxForm,
    Comments,
    Flags,
    Scores,
    SearchForm,
    add_user_info,
    filter_all_activities,
    select_filters,
)
from assess.assessments.forms.assessment_form import AssessmentCompleteForm
from assess.assessments.forms.assignment_forms import (
    AssessmentAssignmentForm,
    AssessorChoiceForm,
    AssessorCommentForm,
    AssessorTypeForm,
    AssignmentOverviewForm,
)
from assess.assessments.forms.comments_form import CommentsForm
from assess.assessments.forms.mark_qa_complete_form import MarkQaCompleteForm
from assess.assessments.helpers import (
    convert_datetime_to_bst,
    determine_display_status,
    download_file,
    generate_assessment_info_csv,
    generate_maps_from_form_names,
    get_files_for_application_upload_fields,
    get_tag_map_and_tag_options,
    get_team_flag_stats,
    sanitise_export_data,
    set_application_status_in_overview,
    set_assigned_info_in_overview,
    sort_assigned_column,
)
from assess.assessments.models import applicants_response
from assess.assessments.models.file_factory import (
    FILE_GENERATORS,
    ApplicationFileRepresentationArgs,
    generate_file_content,
)
from assess.assessments.models.flag_teams import TeamsFlagData
from assess.assessments.models.location_data import LocationData
from assess.assessments.models.round_summary import create_round_summaries, is_after_today
from assess.assessments.status import (
    all_status_completed,
    update_ar_status_to_completed,
    update_ar_status_to_qa_completed,
)
from assess.authentication.validation import (
    check_access_application_id,
    check_access_fund_short_name_round_sn,
    has_access_to_fund,
)
from assess.scoring.helpers import get_scoring_class
from assess.services.aws import get_file_for_download_from_aws
from assess.services.data_services import (
    assign_user_to_assessment,
    get_all_associated_tags_for_application,
    get_all_sub_criterias_with_application_json,
    get_all_uploaded_documents_theme_answers,
    get_applicant_export,
    get_applicant_feedback_and_survey_report,
    get_application_assignments,
    get_application_json,
    get_application_overviews,
    get_application_sections_display_config,
    get_assessment_progress,
    get_associated_tags_for_application,
    get_bulk_accounts_dict,
    get_comments,
    get_flags,
    get_fund,
    get_funds,
    get_qa_complete,
    get_round,
    get_score_and_justification,
    get_sub_criteria,
    get_sub_criteria_theme_answers_all,
    get_tag_types,
    get_tags_for_fund_round,
    get_users_for_fund,
    match_comment_to_theme,
    submit_comment,
)
from assess.services.models.comment import CommentType
from assess.services.models.fund import Fund
from assess.services.models.round import Round
from assess.services.models.theme import Theme
from assess.services.shared_data_helpers import get_state_for_tasklist_banner
from assess.shared.filters import utc_to_bst
from assess.shared.helpers import (
    determine_assessment_status,
    determine_flag_status,
    fund_matches_filters,
    get_ttl_hash,
    is_flaggable,
    match_search_params,
    process_assessments_stats,
)
from assess.themes.deprecated_theme_mapper import (
    map_application_with_sub_criterias_and_themes,
    order_entire_application_by_themes,
)
from common.blueprints import Blueprint
from config import Config
from assess.config.display_value_mappings import (
    assessment_statuses,
    asset_types,
    cohort,
    dpi_filters,
    funding_types,
    joint_application_options,
    landing_filters,
    search_params_default,
)

ASSESSMENT_TOOL_DASHBOARD_PATH = "/assess/assessor_tool_dashboard/"

assessment_bp = Blueprint(
    "assessment_bp",
    __name__,
    url_prefix=Config.ASSESSMENT_HUB_ROUTE,
    template_folder="templates",
)


def run_with_context(func, *args, **kwargs):
    with current_app.app_context():
        return func(*args, **kwargs)


class ContextThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    def __init__(self, *args, **kwargs):
        self.context = contextvars.copy_context()
        super().__init__(*args, **kwargs, initializer=self._set_child_context)

    def _set_child_context(self):
        for var, value in self.context.items():
            var.set(value)


def _handle_all_uploaded_documents(application_id):
    flags_list = get_flags(application_id)
    flag_status = determine_flag_status(flags_list)

    theme_answers_response = get_all_uploaded_documents_theme_answers(application_id)
    answers_meta = applicants_response.create_ui_components(theme_answers_response, application_id)

    state = get_state_for_tasklist_banner(application_id)
    assessment_status = determine_assessment_status(state.workflow_status, state.is_qa_complete)
    return render_template(
        "assessments/all_uploaded_documents.html",
        state=state,
        application_id=application_id,
        is_flaggable=is_flaggable(flag_status),
        answers_meta=answers_meta,
        assessment_status=assessment_status,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


def _get_fund_dashboard_data(fund: Fund, round: Round, request):
    search_params = {**search_params_default}

    fund_id, round_id = fund.id, round.id

    # matches the query parameters provided in the search and filter form
    search_params, show_clear_filters = match_search_params(search_params, request.args)

    thread_executor = ContextAwareExecutor(
        max_workers=4,
        thread_name_prefix="fund-dashboard-request",
        flask_app=current_app,
    )

    # The first call is to get the location data such as country, region and local_authority
    # from all the existing applications (i.e without search parameters as we don't want to filter
    # the stats at all).  see https://dluhcdigital.atlassian.net/browse/FS-3249
    future_all_applications_metadata = thread_executor.submit(get_application_overviews, fund_id, round_id, "")

    # The second call is with the search parameters
    future_application_overviews = thread_executor.submit(
        get_application_overviews,
        fund_id,
        round_id,
        search_params,
    )

    # Get all the users for the fund
    future_users_for_fund = thread_executor.submit(
        get_users_for_fund,
        fund.short_name,
    )

    future_active_fund_round_tags = thread_executor.submit(
        get_tags_for_fund_round,
        fund_id,
        round_id,
        {"tag_status": "True"},
    )

    future_tag_types = thread_executor.submit(get_tag_types)

    all_applications_metadata = future_all_applications_metadata.result()
    users_for_fund = future_users_for_fund.result()
    application_overviews = future_application_overviews.result()
    active_fund_round_tags = future_active_fund_round_tags.result()
    tag_types = future_tag_types.result()

    thread_executor.executor.shutdown()

    unfiltered_stats = process_assessments_stats(all_applications_metadata)
    all_application_locations = LocationData.from_json_blob(all_applications_metadata)

    teams_flag_stats = get_team_flag_stats(all_applications_metadata)

    # this is only used for querying applications, so remove it from the search params,
    # so it's not reflected on the user interface
    if "countries" in search_params:
        del search_params["countries"]

    round_details = {
        "assessment_deadline": round.assessment_deadline,
        "round_title": round.title,
        "fund_name": fund.name,
        "fund_short_name": fund.short_name,
        "round_short_name": round.short_name,
        "is_expression_of_interest": round.is_expression_of_interest,
    }

    is_active_status = is_after_today(round.assessment_deadline)
    post_processed_overviews = (
        get_assessment_progress(application_overviews, fund_id, round_id) if application_overviews else []
    )

    # get and set application status
    post_processed_overviews = set_application_status_in_overview(post_processed_overviews)
    post_processed_overviews, users_not_mapped = set_assigned_info_in_overview(post_processed_overviews, users_for_fund)

    if users_not_mapped:
        current_app.logger.warning(
            "The following users were assigned applications but could not be"
            "found in the account store: {users_not_mapped}",
            extra=dict(users_not_mapped=users_not_mapped),
        )

    tags_in_application_map, tag_option_groups = get_tag_map_and_tag_options(
        tag_types, active_fund_round_tags, post_processed_overviews
    )

    def get_sorted_application_overviews(application_overviews, column, reverse=False):
        """Sorts application_overviews list based on the specified column."""

        sort_field_to_lambda = {
            "location": lambda x: x["location_json_blob"]["country"],
            "funding_requested": lambda x: x["funding_amount_requested"],
            "local_authority": lambda x: x["local_authority"],
            "project_name": lambda x: x["project_name"],
            "asset_type": lambda x: x["asset_type"],
            "organisation_name": lambda x: x["organisation_name"],
            "funding_type": lambda x: x["funding_type"],
            "status": lambda x: x["application_status"],
            "tags": lambda x: len(tags_in_application_map.get(x["application_id"]) or []),
            "team_in_place": lambda x: x["team_in_place"],
            "datasets": lambda x: x["datasets"],
            "date_submitted": lambda x: x["date_submitted"],
            "lead_contact_email": lambda x: x["lead_contact_email"],
            "publish_datasets": lambda x: (
                x["publish_datasets"] if x["publish_datasets"] else str(x["publish_datasets"])
            ),
            "assigned_to": functools.cmp_to_key(sort_assigned_column),
        }

        # Define the sorting function based on the specified column
        if sort_key := sort_field_to_lambda.get(column, None):
            return sorted(application_overviews, key=sort_key, reverse=reverse)
        else:
            return application_overviews

    # Get the sort column and order from query parameters
    sort_column = request.args.get("sort_column", "")
    sort_order = request.args.get("sort_order", "")
    if sort_column:
        post_processed_overviews = get_sorted_application_overviews(
            post_processed_overviews,
            sort_column,
            reverse=sort_order != "asc",
        )
    assigned_applications = [
        application for application in post_processed_overviews if g.account_id in application["assigned_to_ids"]
    ]

    fund_user_aliases = (
        [user["full_name"] if user["full_name"] else user["email_address"] for user in users_for_fund]
        if users_for_fund
        else []
    )

    reporting_to_user_applications = [
        overview
        for overview in post_processed_overviews
        if "user_associations" in overview
        and overview["user_associations"]
        and any(assoc["assigner_id"] == g.account_id and assoc["active"] for assoc in overview["user_associations"])
    ]

    # Filter by assigned to here as it's not a searchable parameter on assessment store
    if "assigned_to" in search_params and post_processed_overviews:
        if search_params["assigned_to"].upper() == "ALL":
            pass
        elif search_params["assigned_to"].upper() == "NOT ASSIGNED":
            post_processed_overviews = [
                overview for overview in post_processed_overviews if len(overview["assigned_to_names"]) == 0
            ]
        else:
            post_processed_overviews = [
                overview
                for overview in post_processed_overviews
                if search_params["assigned_to"] in overview["assigned_to_names"]
            ]

    return {
        # "user":g.user,
        "application_overviews": post_processed_overviews,
        "assigned_applications": assigned_applications,
        "reporting_to_user_applications": reporting_to_user_applications,
        "round_details": round_details,
        "query_params": search_params,
        "asset_types": asset_types,
        "funding_types": funding_types,
        "cohort": cohort,
        "assessment_statuses": assessment_statuses,
        "joint_application_options": joint_application_options,
        "display_config": {"show_clear_filters": show_clear_filters},
        "stats": unfiltered_stats,
        "team_flag_stats": teams_flag_stats,
        "is_active_status": is_active_status,
        "sort_column": sort_column,
        "sort_order": sort_order,
        "tag_option_groups": tag_option_groups,
        "tags": tags_in_application_map,
        "tagging_purpose_config": Config.TAGGING_PURPOSE_CONFIG,
        "countries": all_application_locations.countries,
        "regions": all_application_locations.regions,
        "local_authorities": all_application_locations._local_authorities,
        "migration_banner_enabled": Config.MIGRATION_BANNER_ENABLED,
        "dpi_filters": dpi_filters,
        "users": ["All", "Not assigned"] + fund_user_aliases,
    }


@assessment_bp.route("/fund_dashboard/", methods=["GET"])
def old_landing():
    return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)


@assessment_bp.route("/assessor_tool_dashboard/", methods=["GET"])
def landing():
    filters = landing_filters._replace(**{k: v for k, v in request.args.items() if k in landing_filters._fields})  # noqa
    funds = [
        f
        for f in get_funds(get_ttl_hash(seconds=Config.LRU_CACHE_TIME))
        if has_access_to_fund(f.short_name) and fund_matches_filters(f, filters)
    ]
    sorted_funds_map = OrderedDict((fund.id, fund) for fund in sorted(funds, key=lambda f: f.name))

    round_summaries = {fund.id: create_round_summaries(fund, filters) for fund in funds}

    # print(f"fund summaries:=>  {round_summaries}")
    return render_template(
        "assessments/assessor_tool_dashboard.html",
        fund_summaries=round_summaries,
        funds=sorted_funds_map,
        todays_date=utc_to_bst(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
        landing_filters=filters,
        has_any_assessor_role=any(
            rs.access_controller.has_any_assessor_role for rsl in round_summaries.values() for rs in rsl
        ),
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


"""
Entry point (1/4) for assignment flow. This form checks the selected assessments
and progresses to the assessor type view if successful.
"""


@assessment_bp.route(
    "/assign/<fund_short_name>/<round_short_name>/",
    methods=["GET", "POST"],
)
@check_access_fund_short_name_round_sn
@check_access_fund_short_name_round_sn(roles_required=[Config.LEAD_ASSESSOR])
def assign_assessments(fund_short_name: str, round_short_name: str):
    selected_assessments = request.form.getlist("selected_assessments")

    form = AssessmentAssignmentForm()

    if form.validate_on_submit():
        return redirect(
            url_for(
                "assessment_bp.assessor_type",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    fund = get_fund(
        fund_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    if not fund:
        return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)

    round = get_round(
        fund_short_name,
        round_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    if not round:
        return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)

    dashboard_data = _get_fund_dashboard_data(fund, round, request)

    return render_template(
        "assessments/assign_assessments.html",
        user=g.user,
        form=form,
        selected_assessments=selected_assessments,
        **dashboard_data,
    )


"""
View 2/4 in the assignment flow. This form requests the type of
assessor the user would like to assign to. Options are lead or
general assessors. Successful submissions are routed to the
assessor_type_list.
"""


@assessment_bp.route(
    "/assign/<fund_short_name>/<round_short_name>/type",
    methods=["POST"],
)
@check_access_fund_short_name_round_sn
@check_access_fund_short_name_round_sn(roles_required=[Config.LEAD_ASSESSOR])
def assessor_type(fund_short_name: str, round_short_name: str):
    if not (selected_assessments := request.form.getlist("selected_assessments")):
        abort(500, "Required selected_assessments field to be populated")

    selected_assessor_role = request.form.getlist("assessor_role")[0] if request.form.getlist("assessor_role") else ""

    form = AssessorTypeForm()

    if form.validate_on_submit():
        return redirect(
            url_for(
                "assessment_bp.assessor_type_list",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    fund = get_fund(
        fund_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    if not fund:
        return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)

    round = get_round(
        fund_short_name,
        round_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )

    round_details = {
        "assessment_deadline": round.assessment_deadline,
        "round_title": round.title,
        "fund_name": fund.name,
        "fund_short_name": fund_short_name,
        "round_short_name": round_short_name,
        "is_expression_of_interest": round.is_expression_of_interest,
    }

    all_applications_metadata = get_application_overviews(fund.id, round.id, "")

    unfiltered_stats = process_assessments_stats(all_applications_metadata)

    return render_template(
        "assessments/assessor_type.html",
        selected_assessments=selected_assessments,
        selected_assessor_role=selected_assessor_role,
        round_details=round_details,
        stats=unfiltered_stats,
        form=form,
    )


"""
View 3/4 in the assignment flow. This view displays a list of
assessors of type chosen in the previous view. The user can
select one or more assessors for assignment and is then routed
to the assignment_overview page.
"""


@assessment_bp.route(
    "/assign/<fund_short_name>/<round_short_name>/assessors",
    methods=["POST"],
)
@check_access_fund_short_name_round_sn
@check_access_fund_short_name_round_sn(roles_required=[Config.LEAD_ASSESSOR])
def assessor_type_list(fund_short_name: str, round_short_name: str):
    if not (selected_assessments := request.form.getlist("selected_assessments")):
        abort(500, "Required selected_assessments field to be populated")

    if not (assessor_role := request.form.getlist("assessor_role")):
        abort(500, "Required assessor_role field to be populated")

    assessor_role = assessor_role[0]

    form = AssessorChoiceForm()

    if form.validate_on_submit():
        return redirect(
            url_for(
                "assessment_bp.assignment_overview",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    fund = get_fund(
        fund_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    if not fund:
        return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)

    round = get_round(
        fund_short_name,
        round_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )

    round_details = {
        "assessment_deadline": round.assessment_deadline,
        "round_title": round.title,
        "fund_name": fund.name,
        "fund_short_name": fund_short_name,
        "round_short_name": round_short_name,
        "is_expression_of_interest": round.is_expression_of_interest,
    }

    thread_executor = ContextAwareExecutor(
        max_workers=4,
        thread_name_prefix="fund-dashboard-request",
        flask_app=current_app,
    )

    # The first call is to get the location data such as country, region and local_authority
    # from all the existing applications (i.e without search parameters as we don't want to filter
    # the stats at all).  see https://dluhcdigital.atlassian.net/browse/FS-3249
    future_all_applications_metadata = thread_executor.submit(get_application_overviews, fund.id, round.id, "")

    # Get all the users for the fund
    future_users_for_fund = thread_executor.submit(
        get_users_for_fund,
        fund.short_name,
        None,  # round_short_name,
        True,
        False,
    )

    future_existing_assignments = thread_executor.submit(get_application_assignments, selected_assessments[0], True)

    all_applications_metadata = future_all_applications_metadata.result()
    users_for_fund = future_users_for_fund.result()
    existing_assignments = future_existing_assignments.result()
    all_assigned_users = set(assignment["user_id"] for assignment in existing_assignments)

    thread_executor.executor.shutdown()

    # Selectable users are the complete set of users who can be assigned the assessment
    # Assigned users are the users who are already assigned to the assessment
    # Selected users are those which have been selected via this form (defaults to assigned_users otherwise)
    if assessor_role.lower() == Config.LEAD_ASSESSOR.lower():
        selectable_users = [
            user for user in users_for_fund if any(Config.LEAD_ASSESSOR in role for role in user["roles"])
        ]
    else:
        selectable_users = [
            user
            for user in users_for_fund
            if any(Config.ASSESSOR in role and Config.LEAD_ASSESSOR not in role for role in user["roles"])
        ]

    assigned_users = [user["account_id"] for user in selectable_users if user["account_id"] in all_assigned_users]
    selected_users = (
        request.form.getlist("selected_users") if request.form.getlist("selected_users") else assigned_users
    )

    unfiltered_stats = process_assessments_stats(all_applications_metadata)

    return render_template(
        "assessments/select_assessor.html",
        selected_assessments=selected_assessments,
        assessor_role=assessor_role,
        round_details=round_details,
        stats=unfiltered_stats,
        users=selectable_users,
        selected_users=selected_users,
        assigned_users=assigned_users,
        form=form,
    )


@assessment_bp.route(
    "/assign/<fund_short_name>/<round_short_name>/assessors/comment",
    methods=["GET", "POST"],
)
@check_access_fund_short_name_round_sn
@check_access_fund_short_name_round_sn(roles_required=[Config.LEAD_ASSESSOR])
def assessor_comments(fund_short_name: str, round_short_name: str):
    if "cancel_messages" in request.form:
        return redirect(
            url_for(
                "assessment_bp.assignment_overview",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    assigned_user_set = set(request.form.getlist("assigned_users"))
    selected_user_set = set(request.form.getlist("selected_users"))

    if not (selected_assessments := request.form.getlist("selected_assessments")):
        abort(500, "Required selected_assessments field to be populated")

    if not (assessor_role := request.form.getlist("assessor_role")):
        abort(500, "Required assessor_role field to be populated")

    assessor_messages = {}
    for key, value in request.form.items():
        if "message_" in key and value:
            assessor_messages[key] = escape(value)

    old_assessor_messages = (
        json.loads(request.form.get("old_assessor_messages"))
        if "old_assessor_messages" in request.form
        else assessor_messages
    )
    has_individual_messages = any(key != "message_to_all" for key in assessor_messages.keys())

    assessor_role = assessor_role[0]

    form = AssessorCommentForm()

    if form.validate_on_submit():
        return redirect(
            url_for(
                "assessment_bp.assignment_overview",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    add_user_assignments = selected_user_set - assigned_user_set
    remove_user_assignments = assigned_user_set - selected_user_set

    fund = get_fund(
        fund_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    if not fund:
        return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)

    round = get_round(
        fund_short_name,
        round_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )

    round_details = {
        "assessment_deadline": round.assessment_deadline,
        "round_title": round.title,
        "fund_name": fund.name,
        "fund_short_name": fund_short_name,
        "round_short_name": round_short_name,
        "is_expression_of_interest": round.is_expression_of_interest,
    }

    thread_executor = ContextAwareExecutor(
        max_workers=4,
        thread_name_prefix="assignment-overview-request",
        flask_app=current_app,
    )

    future_all_applications_metadata = thread_executor.submit(get_application_overviews, fund.id, round.id, "")

    # Get all the users for the fund
    future_users_for_fund = thread_executor.submit(
        get_users_for_fund,
        fund.short_name,
        None,  # round_short_name,
        True,
        False,
    )

    all_applications_metadata = future_all_applications_metadata.result()
    users_for_fund = future_users_for_fund.result()

    thread_executor.executor.shutdown()

    # Get either name or email of those assessors that have been selected
    add_assign_users = (
        [user for user in users_for_fund if user["account_id"] in add_user_assignments] if users_for_fund else []
    )
    add_assign_user_names = [
        user["full_name"] if user["full_name"] else user["email_address"] for user in add_assign_users
    ]

    unassign_users = (
        [user for user in users_for_fund if user["account_id"] in remove_user_assignments] if users_for_fund else []
    )

    unassign_user_names = [user["full_name"] if user["full_name"] else user["email_address"] for user in unassign_users]

    unfiltered_stats = process_assessments_stats(all_applications_metadata)
    return render_template(
        "assessments/assessor_comments.html",
        round_details=round_details,
        stats=unfiltered_stats,
        assessor_role=assessor_role,
        add_assign_user_names=add_assign_user_names,
        unassign_user_names=unassign_user_names,
        changed_users=add_assign_users + unassign_users,
        selected_assessments=selected_assessments,
        selected_users=selected_user_set,
        assigned_users=assigned_user_set,
        old_assessor_messages=old_assessor_messages,
        assessor_messages=assessor_messages,
        has_individual_messages=has_individual_messages,
        form=form,
    )


"""
View 4/4 in the assignment flow. This view displays the choices
selected by the user in an overview form. The user can navigate
back to previous pages to change their selection, or they can submit
the selection to create the assignments.
"""


@assessment_bp.route(
    "/assign/<fund_short_name>/<round_short_name>/overview",
    methods=["POST"],
)
@check_access_fund_short_name_round_sn
@check_access_fund_short_name_round_sn(roles_required=[Config.LEAD_ASSESSOR])
def assignment_overview(fund_short_name: str, round_short_name: str):  # noqa: C901
    # Options to navigate back in the flow to change selections
    if "change_users" in request.form:
        return redirect(
            url_for(
                "assessment_bp.assessor_type_list",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    if "change_roles" in request.form:
        return redirect(
            url_for(
                "assessment_bp.assessor_type",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    if "change_assessments" in request.form:
        return redirect(
            url_for(
                "assessment_bp.assign_assessments",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    if "edit_messages" in request.form:
        return redirect(
            url_for(
                "assessment_bp.assessor_comments",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            ),
            307,
        )

    if "cancel_messages" in request.form:
        original_messages = json.loads(request.form["old_assessor_messages"])
        new_request_form = MultiDict(request.form)
        for key in request.form.keys():
            if "message_" in key:
                new_request_form.pop(key)

        for key, value in original_messages.items():
            new_request_form[key] = value

        request.form = ImmutableMultiDict(new_request_form)

    assigned_user_set = set(request.form.getlist("assigned_users"))
    selected_user_set = set(request.form.getlist("selected_users"))

    if not (selected_assessments := request.form.getlist("selected_assessments")):
        abort(500, "Required selected_assessments field to be populated")

    if not (assessor_role := request.form.getlist("assessor_role")):
        abort(500, "Required assessor_role field to be populated")

    if assigned_user_set == selected_user_set:
        abort(500, "No change in assignments has been made")

    assessor_messages = {}
    for key, value in request.form.items():
        if "message_" in key and value:
            assessor_messages[key] = escape(value)

    add_user_assignments = selected_user_set - assigned_user_set
    remove_user_assignments = assigned_user_set - selected_user_set

    assessor_role = assessor_role[0]

    form = AssignmentOverviewForm()

    thread_executor = ContextAwareExecutor(
        max_workers=4,
        thread_name_prefix="assignment-overview-request",
        flask_app=current_app,
    )

    fund = get_fund(
        fund_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    if not fund:
        return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)

    round = get_round(
        fund_short_name,
        round_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )

    round_details = {
        "assessment_deadline": round.assessment_deadline,
        "round_title": round.title,
        "fund_name": fund.name,
        "fund_short_name": fund_short_name,
        "round_short_name": round_short_name,
        "is_expression_of_interest": round.is_expression_of_interest,
    }

    # The first call is to get the location data such as country, region and local_authority
    # from all the existing applications (i.e without search parameters as we don't want to filter
    # the stats at all).  see https://dluhcdigital.atlassian.net/browse/FS-3249
    future_all_applications_metadata = thread_executor.submit(get_application_overviews, fund.id, round.id, "")

    # Get all the users for the fund
    future_users_for_fund = thread_executor.submit(
        get_users_for_fund,
        fund.short_name,
        None,  # round_short_name,
        True,
        False,
    )

    all_applications_metadata = future_all_applications_metadata.result()
    users_for_fund = future_users_for_fund.result()
    all_applications_ids = set((application["application_id"] for application in all_applications_metadata))
    all_user_ids = set((user["account_id"] for user in users_for_fund))

    if not all(user_id in all_user_ids for user_id in selected_user_set.union(assigned_user_set)):
        abort(
            403,
            "User does not have permission to make assignments for selected assessors",
        )

    if not all(application_id in all_applications_ids for application_id in selected_assessments):
        abort(
            403,
            "User does not have permission to make assignments for selected assessments",
        )

    if form.validate_on_submit():
        # Check for existing assignments between user and application
        future_to_app = {
            thread_executor.submit(
                get_application_assignments,
                application_id,
            ): application_id
            for application_id in selected_assessments
        }

        # Create set of assignments between users and assessments that already exist
        existing_assignments = set()

        for future in concurrent.futures.as_completed(future_to_app):
            application_id = future_to_app[future]
            data = future.result()
            if data:
                existing_assignments.update(assignment["user_id"] + "," + application_id for assignment in data)

        future_assignments = {}

        default_email_message = assessor_messages["message_to_all"] if "message_to_all" in assessor_messages else ""
        # Cartesian product over selected users and assessments. Check if the assignment already
        # exists or is a new one to be created (PUT vs POST)
        for user_id, application_id in itertools.product(add_user_assignments, selected_assessments):
            key = user_id + "," + application_id

            future = thread_executor.submit(
                assign_user_to_assessment,
                application_id,
                user_id,
                g.account_id,
                True if key in existing_assignments else False,
                True,
                True,
                (
                    assessor_messages["message_" + user_id]
                    if "message_" + user_id in assessor_messages
                    else default_email_message
                ),
            )
            future_assignments[future] = key

        # Deactive assignments for those users who have deselected.
        for user_id, application_id in itertools.product(remove_user_assignments, selected_assessments):
            key = user_id + "," + application_id

            future = thread_executor.submit(
                assign_user_to_assessment,
                application_id,
                user_id,
                g.account_id,
                True,
                False,
                True,
                (
                    assessor_messages["message_" + user_id]
                    if "message_" + user_id in assessor_messages
                    else default_email_message
                ),
            )
            future_assignments[future] = key

        # Check for those assignments that could not be created and log them
        for future in concurrent.futures.as_completed(future_assignments):
            if future.result() is None:
                user_id, application_id = future_assignments[future].split(",")
                current_app.logger.error(
                    "Could not create assignment for user {user_id} and application {application_id}",
                    extra=dict(user_id=user_id, application_id=application_id),
                )

        return redirect(
            url_for(
                "assessment_bp.fund_dashboard",
                fund_short_name=fund_short_name,
                round_short_name=round_short_name,
            )
        )

    thread_executor.executor.shutdown()

    # Get either name or email of those assessors that have been selected
    add_assign_user_names = (
        [
            user["full_name"] if user["full_name"] else user["email_address"]
            for user in users_for_fund
            if user["account_id"] in add_user_assignments
        ]
        if users_for_fund
        else []
    )

    unassign_user_names = (
        [
            user["full_name"] if user["full_name"] else user["email_address"]
            for user in users_for_fund
            if user["account_id"] in remove_user_assignments
        ]
        if users_for_fund
        else []
    )

    # Retain only those assessments that were selected by the user
    selected_assessment_overview = [
        assessment for assessment in all_applications_metadata if assessment["application_id"] in selected_assessments
    ]

    post_processed_overviews = get_assessment_progress(selected_assessment_overview, fund.id, round.id)

    post_processed_overviews = set_application_status_in_overview(post_processed_overviews)

    unfiltered_stats = process_assessments_stats(all_applications_metadata)

    return render_template(
        "assessments/assignment_overview.html",
        selected_assessments=selected_assessments,
        add_assign_user_names=add_assign_user_names,
        unassign_user_names=unassign_user_names,
        selected_users=selected_user_set,
        assigned_users=assigned_user_set,
        assessor_role=assessor_role,
        assessor_messages=assessor_messages,
        round_details=round_details,
        stats=unfiltered_stats,
        assessments=post_processed_overviews,
        form=form,
        assessment_statuses=assessment_statuses,
    )


@assessment_bp.route(
    "/fund_dashboard/<fund_short_name>/<round_short_name>/",
    methods=["GET"],
)
@check_access_fund_short_name_round_sn
def fund_dashboard(fund_short_name: str, round_short_name: str):
    # Create a unique key for the session based on the fund short name and round short name
    session_key = f"filter_params_{fund_short_name.upper()}_{round_short_name.upper()}"

    # If there are no query arguments in the request
    if not request.args:
        # Check if there are saved filter parameters in the session
        if session_key in session and session[session_key] is not None:
            filter_params = session[session_key]
            # Update the query arguments with the saved filter parameters
            request.args = ImmutableMultiDict(list(filter_params.items()))
    # If the 'clear_filters' flag is set in the query arguments, clear the session
    elif "clear_filters" in request.args:
        session[session_key] = None
    # Otherwise, save only relevant filter parameters to the session
    else:
        filter_params = {
            key: value
            for key, value in request.args.items()
            if key in ["search_term", "status", "assigned_to", "filter_by_tag"]
        }
        session[session_key] = filter_params

    fund = get_fund(
        fund_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    if not fund:
        return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)
    round = get_round(
        fund_short_name,
        round_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    if not round:
        return redirect(ASSESSMENT_TOOL_DASHBOARD_PATH)

    dashboard_data = _get_fund_dashboard_data(fund, round, request)

    return render_template("assessments/fund_dashboard.html", user=g.user, **dashboard_data)


@assessment_bp.route(
    "/application_id/<application_id>/sub_criteria_id/<sub_criteria_id>",
    methods=["POST", "GET"],
)
@check_access_application_id
def display_sub_criteria(
    application_id,
    sub_criteria_id,
):
    if sub_criteria_id == "all_uploaded_documents":
        return _handle_all_uploaded_documents(application_id)

    """
    Page showing sub criteria and themes for an application
    """
    current_app.logger.info("Processing GET to {request_path}.", extra=dict(request_path=request.path))
    sub_criteria = get_sub_criteria(application_id, sub_criteria_id)
    theme_id = request.args.get("theme_id", sub_criteria.themes[0].id)
    comment_form = CommentsForm()
    try:
        current_theme: Theme = next(iter(t for t in sub_criteria.themes if t.id == theme_id))
    except StopIteration:
        current_app.logger.warning("Unknown theme ID requested: {theme_id}", extra=dict(theme_id=theme_id))
        abort(404)
    add_comment_argument = request.args.get("add_comment") == "1"
    if add_comment_argument and comment_form.validate_on_submit():
        comment = comment_form.comment.data
        submit_comment(
            comment=comment,
            application_id=application_id,
            sub_criteria_id=sub_criteria_id,
            user_id=g.account_id,
            theme_id=theme_id,
            comment_type=CommentType.COMMENT.name,
        )

        return redirect(
            url_for(
                "assessment_bp.display_sub_criteria",
                application_id=application_id,
                sub_criteria_id=sub_criteria_id,
                theme_id=theme_id,
                _anchor="comments",
            )
        )

    state = get_state_for_tasklist_banner(application_id)
    flags_list = get_flags(application_id)

    comment_response = get_comments(
        application_id=application_id,
        sub_criteria_id=sub_criteria_id,
        theme_id=theme_id,
        comment_type=CommentType.COMMENT.name,
    )

    # TODO add test for this function in data_operations
    theme_matched_comments = (
        match_comment_to_theme(comment_response, sub_criteria.themes, state.fund_short_name)
        if comment_response
        else None
    )

    assessment_status = determine_assessment_status(sub_criteria.workflow_status, state.is_qa_complete)
    flag_status = determine_flag_status(flags_list)

    edit_comment_argument = request.args.get("edit_comment")
    comment_id = request.args.get("comment_id")
    show_comment_history = request.args.get("show_comment_history")

    if comment_id and show_comment_history:
        for comment_data in theme_matched_comments[theme_id]:
            if comment_data.id == comment_id:
                return render_template(
                    "assessments/comments_history.html",
                    comment_data=comment_data,
                    back_href=url_for(
                        "assessment_bp.display_sub_criteria",
                        application_id=application_id,
                        sub_criteria_id=sub_criteria_id,
                        theme_id=theme_id,
                        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
                    ),
                    application_id=application_id,
                    state=state,
                    flag_status=flag_status,
                    assessment_status=assessment_status,
                    migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
                )

    if edit_comment_argument and comment_form.validate_on_submit():
        comment = comment_form.comment.data
        submit_comment(comment=comment, comment_id=comment_id)

        return redirect(
            url_for(
                "assessment_bp.display_sub_criteria",
                application_id=application_id,
                sub_criteria_id=sub_criteria_id,
                theme_id=theme_id,
                migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
                _anchor="comments",
            )
        )

    common_template_config = {
        "sub_criteria": sub_criteria,
        "application_id": application_id,
        "comments": theme_matched_comments,
        "is_flaggable": False,  # Flag button is disabled in sub-criteria page,
        "display_comment_box": add_comment_argument,
        "display_comment_edit_box": edit_comment_argument,
        "comment_id": comment_id,
        "comment_form": comment_form,
        "current_theme": current_theme,
        "flag_status": flag_status,
        "assessment_status": assessment_status,
        "pagination": state.get_pagination_from_sub_criteria_id(sub_criteria_id),
    }

    theme_answers_response = get_sub_criteria_theme_answers_all(application_id, theme_id)

    answers_meta = applicants_response.create_ui_components(theme_answers_response, application_id)

    return render_template(
        "assessments/sub_criteria.html",
        answers_meta=answers_meta,
        state=state,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
        **common_template_config,
    )


@assessment_bp.route("/application/<application_id>/export", methods=["GET"])
@check_access_application_id(roles_required=[Config.LEAD_ASSESSOR])
def generate_doc_list_for_download(application_id):
    current_app.logger.info(
        "Generating docs for application id {application_id}", extra=dict(application_id=application_id)
    )
    state = get_state_for_tasklist_banner(application_id)
    short_id = state.short_id[-6:]
    flags_list = get_flags(application_id)
    flag_status = determine_flag_status(flags_list)

    application_json = get_application_json(application_id)
    supporting_evidence = get_files_for_application_upload_fields(
        application_id=application_id,
        short_id=short_id,
        application_json=application_json,
    )

    file_links = [
        (
            f"Download applicant answers as {file_type.upper()} file",
            url_for(
                "assessment_bp.download_application_answers",
                application_id=application_id,
                short_id=short_id,
                file_type=file_type,
            ),
        )
        for file_type in FILE_GENERATORS.keys()
    ]
    assessment_status = determine_assessment_status(state.workflow_status, state.is_qa_complete)

    return render_template(
        "assessments/contract_downloads.html",
        application_id=application_id,
        state=state,
        file_links=file_links,
        supporting_evidence=supporting_evidence,
        assessment_status=assessment_status,
        flag_status=flag_status,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


@assessment_bp.route("/application/<application_id>/export/<short_id>/answers.<file_type>")
@check_access_application_id(roles_required=[Config.LEAD_ASSESSOR])
def download_application_answers(application_id: str, short_id: str, file_type: str):
    current_app.logger.info(
        "Generating application Q+A download for application {application_id} in {file_type} format",
        extra=dict(application_id=application_id, file_type=file_type),
    )
    application_json = get_application_json(application_id)
    application_json_blob = application_json["jsonb_blob"]

    fund = get_fund(
        application_json["jsonb_blob"]["fund_id"],
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    round_ = get_round(
        fund.id,
        application_json["round_id"],
        use_short_name=False,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )

    qanda_dict = extract_questions_and_answers(application_json_blob["forms"])
    application_sections_display_config = get_application_sections_display_config(
        fund.id, round_.id, application_json["language"]
    )

    (
        form_name_to_title_map,
        form_name_to_path_map,
    ) = generate_maps_from_form_names(application_sections_display_config)

    qanda_dict = {key: qanda_dict[key] for key in form_name_to_title_map if key in qanda_dict}

    all_uploaded_documents = []
    if file_type == "pdf":
        all_uploaded_documents = get_all_uploaded_documents_theme_answers(application_id)

    args = ApplicationFileRepresentationArgs(
        fund=fund,
        round=round_,
        question_to_answer=qanda_dict,
        application_json=application_json,
        form_name_to_title_map=form_name_to_title_map,
        short_id=short_id,
        all_uploaded_documents=all_uploaded_documents,
    )

    return generate_file_content(args, file_type)


@assessment_bp.route(
    "/application/<application_id>/export/<file_name>",
    methods=["GET"],
)
def get_file(application_id: str, file_name: str):
    if request.args.get("quoted"):
        file_name = unquote_plus(file_name)
    short_id = request.args.get("short_id")
    data, mimetype = get_file_for_download_from_aws(application_id=application_id, file_name=file_name)
    if short_id:
        return download_file(data, mimetype, f"{short_id}_{file_name}")

    return download_file(data, mimetype, file_name)


def download_multiple_files(files, folder_name):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_archive:
        for file_name, file_data in files:
            zip_archive.writestr(file_name, file_data)

    zip_buffer.seek(0)

    return Response(
        zip_buffer.read(),
        mimetype="application/zip",
        headers={"Content-Disposition": f"attachment;filename={quote_plus(f'{folder_name}.zip')}"},
    )


@assessment_bp.route("/application/<application_id>", methods=["GET", "POST"])
@check_access_application_id
def application(application_id):
    """
    Application summary page
    Shows information about the fund, application ID
    and all the application questions and their assessment status
    :param application_id:
    :return:
    """

    if request.method == "POST":
        update_ar_status_to_completed(application_id)

    state = get_state_for_tasklist_banner(application_id)

    scoring_form = get_scoring_class(state.round_id)()

    fund_round = get_round(
        state.fund_id,
        state.round_id,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    user_id_list = []
    flags_list = get_flags(application_id)
    qa_complete = get_qa_complete(application_id)
    if qa_complete:
        user_id_list.append(qa_complete["user_id"])

    assessment_status = determine_assessment_status(state.workflow_status, state.is_qa_complete)
    flag_status = determine_flag_status(flags_list)

    if flags_list:
        for flag_data in flags_list:
            for flag_item in flag_data.updates:
                if flag_item["user_id"] not in user_id_list:
                    user_id_list.append(flag_item["user_id"])

    accounts_list = get_bulk_accounts_dict(
        user_id_list,
        state.fund_short_name,
    )

    teams_flag_stats = TeamsFlagData.from_flags(flags_list).teams_stats

    sub_criteria_status_completed = all_status_completed(state)
    form = AssessmentCompleteForm()
    associated_tags = get_associated_tags_for_application(application_id)
    add_comment_argument = request.args.get("add_comment") == "1"
    edit_comment_argument = request.args.get("edit_comment") == "1"
    comment_form = CommentsForm()

    if add_comment_argument and comment_form.validate_on_submit():
        comment = comment_form.comment.data
        # No sub_criteria_id and theme_id indicates it belongs to the entire application.
        submit_comment(
            comment=comment,
            application_id=application_id,
            sub_criteria_id="",
            user_id=g.account_id,
            theme_id="",
            comment_type=CommentType.WHOLE_APPLICATION.name,
        )

        return redirect(
            url_for(
                "assessment_bp.application",
                application_id=application_id,
                _anchor="comments",
            )
        )

    state = get_state_for_tasklist_banner(application_id)
    flags_list = get_flags(application_id)

    comment_response = get_comments(
        application_id=application_id,
        sub_criteria_id="",
        theme_id="",
        comment_type=CommentType.WHOLE_APPLICATION.name,
    )

    # TODO add test for this function in data_operations
    theme_matched_comments = (
        match_comment_to_theme(
            comment_response=comment_response,
            themes=None,
            fund_short_name=state.fund_short_name,
        )
        if comment_response
        else None
    )

    flag_status = determine_flag_status(flags_list)

    edit_comment_argument = request.args.get("edit_comment")
    comment_id = request.args.get("comment_id")
    show_comment_history = request.args.get("show_comment_history")

    if comment_id and show_comment_history:
        for comment_data in theme_matched_comments[""]:
            if comment_data.id == comment_id:
                return render_template(
                    "assessments/comments_history.html",
                    comment_data=comment_data,
                    back_href=url_for(
                        "assessment_bp.application",
                        application_id=application_id,
                        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
                    ),
                    application_id=application_id,
                    state=state,
                    flag_status=flag_status,
                    assessment_status=assessment_status,
                    migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
                )

    if edit_comment_argument and comment_form.validate_on_submit():
        comment = comment_form.comment.data
        submit_comment(comment=comment, comment_id=comment_id)

        return redirect(
            url_for(
                "assessment_bp.application",
                application_id=application_id,
                migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
                _anchor="comments",
            )
        )

    return render_template(
        "assessments/assessor_tasklist.html",
        sub_criteria_status_completed=sub_criteria_status_completed,
        tags=associated_tags,
        tag_config=Config.TAGGING_PURPOSE_CONFIG,
        form=form,
        state=state,
        application_id=application_id,
        accounts_list=accounts_list,
        teams_flag_stats=teams_flag_stats,
        flags_list=flags_list,
        is_flaggable=is_flaggable(flag_status),
        is_qa_complete=state.is_qa_complete,
        qa_complete=qa_complete,
        flag_status=flag_status,
        assessment_status=assessment_status,
        all_uploaded_documents_section_available=fund_round.all_uploaded_documents_section_available,
        max_possible_sub_criteria_score=scoring_form.max_score,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
        is_expression_of_interest=fund_round.is_expression_of_interest,
        display_comment_box=add_comment_argument,
        display_comment_edit_box=edit_comment_argument,
        comment_id=comment_id,
        comment_form=comment_form,
        comments=theme_matched_comments,
    )


@assessment_bp.route("/activity_trail/<application_id>", methods=["GET"])
@check_access_application_id
def activity_trail(application_id: str):
    state = get_state_for_tasklist_banner(application_id)

    # There is a better way of doing it by moving
    # all activity related logics to an endpoint in the
    # assessment store and write up a query to fetch all the information.

    # ALL FLAGS
    flags_list = get_flags(application_id)
    all_flags = Flags.from_list(flags_list)

    # ALL COMMENTS
    comments_list = get_comments(application_id)
    all_comments = Comments.from_list(comments_list)

    # ALL SCORES
    scores = get_score_and_justification(application_id=application_id, score_history=True)
    all_scores = Scores.from_list(scores)

    # ALL TAGS
    tags = get_all_associated_tags_for_application(application_id)
    all_tags = AssociatedTags.from_associated_tags_list(tags)

    round_data = get_round(fid=state.fund_id, rid=state.round_id)

    # Add search box and checkbox filters
    available_filters = select_filters(round_data.is_expression_of_interest)
    search_form = SearchForm(request.form)
    checkbox_form = CheckboxForm(request.form)

    # Filter all activities
    search_keyword = request.args.get("search")
    checkbox_filters = request.args.getlist("filter")
    all_activities = all_scores + all_comments + all_tags + all_flags

    update_user_info = add_user_info(all_activities, state)
    _all_activities = filter_all_activities(update_user_info, search_keyword, checkbox_filters)

    display_status = determine_display_status(
        state.workflow_status,
        flags_list,
        state.is_qa_complete,
    )

    return render_template(
        "assessments/activity_trail.html",
        application_id=application_id,
        state=state,
        activities=_all_activities,
        search_form=search_form,
        checkbox_form=checkbox_form,
        available_filters=available_filters,
        search_keyword=search_keyword,
        checkbox_filters=checkbox_filters,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
        display_status=display_status,
        is_expression_of_interest=round_data.is_expression_of_interest,
    )


@assessment_bp.route(
    "/assessor_export/<fund_short_name>/<round_short_name>/<report_type>",
    methods=["GET"],
)
@check_access_fund_short_name_round_sn(roles_required=[Config.LEAD_ASSESSOR])
def assessor_export(fund_short_name: str, round_short_name: str, report_type: str):
    _round = get_round(
        fund_short_name,
        round_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    export = get_applicant_export(_round.fund_id, _round.id, report_type)
    export = convert_datetime_to_bst(export)
    export = sanitise_export_data(export)
    en_export_data = generate_assessment_info_csv(export["en_list"])
    cy_export_data = generate_assessment_info_csv(export["cy_list"])

    formatted_datetime = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    files_to_download = [
        (f"{report_type.lower()}_{formatted_datetime}_en.csv", en_export_data),
        (f"{report_type.lower()}_{formatted_datetime}_cy.csv", cy_export_data),
    ]

    return download_multiple_files(files_to_download, report_type)


@assessment_bp.route(
    "/feedback_export/<fund_short_name>/<round_short_name>",
    methods=["GET"],
)
@check_access_fund_short_name_round_sn(roles_required=[Config.LEAD_ASSESSOR])
def feedback_export(fund_short_name: str, round_short_name: str):
    _round = get_round(
        fund_short_name,
        round_short_name,
        use_short_name=True,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    fund_id = _round.fund_id
    round_id = _round.id
    status_only = "SUBMITTED"

    content = get_applicant_feedback_and_survey_report(fund_id, round_id, status_only)
    if content:
        short_name = (fund_short_name + "_" + round_short_name).lower()
        return download_file(
            content,
            "application/vnd.ms-excel",
            f"fsd_feedback_{short_name}_{str(int(time.time()))}.xlsx",
        )
    else:
        abort(404)


@assessment_bp.route("/qa_complete/<application_id>", methods=["GET", "POST"])
@check_access_application_id(roles_required=[Config.LEAD_ASSESSOR])
def qa_complete(application_id):
    """
    QA complete form html page:
    Allows you to mark an application as QA_completed by submitting the form.
    Once submitted, a call is made to the application store endpoint to save
    the QA_COMPLETED flag in the database for the given application_id
    """

    form = MarkQaCompleteForm()

    if form.validate_on_submit():
        update_ar_status_to_qa_completed(application_id, g.account_id)
        return redirect(
            url_for(
                "assessment_bp.application",
                application_id=application_id,
            )
        )
    state = get_state_for_tasklist_banner(application_id)

    return render_template(
        "assessments/mark_qa_complete.html",
        application_id=application_id,
        state=state,
        form=form,
        referrer=request.referrer,
        assessment_status=assessment_statuses[state.workflow_status],
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


@assessment_bp.route("/entire_application/<application_id>", methods=["GET", "POST"])
@check_access_application_id(roles_required=[Config.LEAD_ASSESSOR, Config.ASSESSOR])
def view_entire_application(application_id):
    """The entire application renders all the questions and answers ordered by
    themes as per the application sub_criteria/themes.
    """
    state = get_state_for_tasklist_banner(application_id)
    fund_round_name = state.fund_short_name + state.round_short_name

    _data = get_all_sub_criterias_with_application_json(application_id)
    application_json = _data["application_json"]
    sub_criterias = _data["sub_criterias"]

    theme_ids = []
    for themes in _data.values():
        for theme in themes:
            if isinstance(theme, dict):
                theme_ids.extend(theme_id["id"] for theme_id in theme["themes"])

    map_appli_with_sub_cris_and_themes = map_application_with_sub_criterias_and_themes(
        application_json, sub_criterias, theme_ids
    )

    # add ordered themes config along with the fund_round_name to file
    # themes_mapping.py, function: ordered_themes
    order_application_by_themes = order_entire_application_by_themes(
        fund_round_name, map_appli_with_sub_cris_and_themes
    )
    map_answers = applicants_response.create_ui_componenets_for_list_data(application_id, order_application_by_themes)

    return render_template(
        "assessments/view_entire_application.html",
        state=state,
        application_id=application_id,
        mapped_answers=map_answers,
    )
