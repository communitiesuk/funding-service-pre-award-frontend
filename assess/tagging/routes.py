import copy
from typing import Dict

from flask import current_app, flash, g, redirect, render_template, request, url_for

from assess.authentication.validation import check_access_application_id, check_access_fund_id_round_id
from assess.services.data_services import (
    get_associated_tags_for_application,
    get_fund,
    get_round,
    get_tag,
    get_tag_for_fund_round,
    get_tag_types,
    get_tags_for_fund_round,
    post_new_tag_for_fund_round,
    update_associated_tags,
    update_tag,
    update_tags,
)
from assess.services.shared_data_helpers import get_state_for_tasklist_banner
from assess.shared.helpers import determine_assessment_status, get_ttl_hash, match_search_params
from assess.tagging.forms.tags import (
    DeactivateTagForm,
    EditTagForm,
    NewTagForm,
    ReactivateTagForm,
    TagAssociationForm,
)
from assess.tagging.models.tag import TagType
from config import Config
from common.blueprints import Blueprint
from assess.config.display_value_mappings import search_params_tag

TAG_DEACTIVATE_ERROR_MESSAGE = "Tag not deactivated."
TAG_REACTIVATE_ERROR_MESSAGE = "Tag not reactivated."


tagging_bp = Blueprint(
    "tagging_bp",
    __name__,
    url_prefix=Config.ASSESSMENT_HUB_ROUTE,
    template_folder="templates",
)


@tagging_bp.route("/application/<application_id>/tags", methods=["GET", "POST"])
@check_access_application_id(roles_required=["ASSESSOR"])
def load_change_tags(application_id):
    tag_association_form = TagAssociationForm()
    if request.method == "POST":
        associated_tags = get_associated_tags_for_application(application_id)
        association_form_data = tag_association_form.tags.data
        updated_tags = []

        if associated_tags and len(associated_tags) > len(association_form_data):
            # Create a list of dictionaries with tag_id and user_id
            updated_tags = [{"tag_id": tag_id, "user_id": g.account_id} for tag_id in association_form_data]
            # Fill remaining with a empty tag_id and current user account_id
            updated_tags.extend([{"tag_id": "", "user_id": g.account_id}])
        else:
            # If associated_tags is zero or null, or not greater than association_form_data
            updated_tags = [{"tag_id": tag_id, "user_id": g.account_id} for tag_id in association_form_data]

        update_associated_tags(application_id, updated_tags)
        return redirect(
            url_for(
                "assessment_bp.application",
                application_id=application_id,
            )
        )

    state = get_state_for_tasklist_banner(application_id)
    all_tags = get_tags_for_fund_round(state.fund_id, state.round_id, "")
    associated_tags = get_associated_tags_for_application(application_id)
    associated_tag_ids = (
        [tag.tag_id for tag in associated_tags]
        if associated_tags
        else current_app.logger.info("No associated tags found.")
    )

    active_tags = []
    for tag in all_tags:
        if associated_tag_ids and tag.id in associated_tag_ids:
            tag.associated = True
        if tag.active:
            active_tags.append(tag)
    assessment_status = determine_assessment_status(state.workflow_status, state.is_qa_complete)
    return render_template(
        "tagging/change_tags.html",
        form=tag_association_form,
        state=state,
        available_tags=active_tags,
        tag_config=Config.TAGGING_PURPOSE_CONFIG,
        application_id=application_id,
        assessment_status=assessment_status,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


def get_fund_round(fund_id, round_id) -> Dict:
    fund = get_fund(
        fund_id,
        use_short_name=False,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    round = get_round(
        fund_id,
        round_id,
        use_short_name=False,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    fund_round = {
        "fund_name": fund.name,
        "round_name": round.title,
        "fund_id": fund_id,
        "round_id": round_id,
    }
    return fund_round


@tagging_bp.route("/tags/manage/<fund_id>/<round_id>", methods=["GET"])
@check_access_fund_id_round_id(roles_required=["ASSESSOR"])
def load_fund_round_tags(fund_id, round_id):
    fund_round = get_fund_round(fund_id, round_id)
    search_params, show_clear_filters = match_search_params(copy.deepcopy(search_params_tag), request.args)
    tags = get_tags_for_fund_round(fund_id, round_id, search_params)
    tag_types = get_tag_types()
    tag_types.insert(0, TagType(id="all", purpose="All", description="all"))
    tag_status_configs = [
        {"text": "Only active tags", "value": "True"},
        {"text": "Only inactive tags", "value": "False"},
    ]
    return render_template(
        "tagging/manage_tags.html",
        fund_round=fund_round,
        search_params=search_params,
        tags=tags,
        show_clear_filters=show_clear_filters,
        tag_types=tag_types,
        tag_status_configs=tag_status_configs,
        tag_config=Config.TAGGING_PURPOSE_CONFIG,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


FLAG_ERROR_MESSAGE = "Tags must be unique, only contain apostrophes, hyphens, letters, digits, and spaces."


@tagging_bp.route("/tags/create/<fund_id>/<round_id>", methods=["GET", "POST"])
@check_access_fund_id_round_id(roles_required=["ASSESSOR"])
def create_tag(fund_id, round_id):
    errors = None
    go_back = request.args.get("go_back") or False
    new_tag_form = NewTagForm()
    tag_types = get_tag_types()
    new_tag_form.type.choices = [tag_type.id for tag_type in tag_types]
    fund_round = get_fund_round(fund_id, round_id)
    fund_round_tags = get_tags_for_fund_round(fund_id, round_id)
    if new_tag_form.validate_on_submit():
        current_app.logger.info("Tag creation form validated")
        tag = {
            "value": new_tag_form.value.data,
            "tag_type_id": new_tag_form.type.data,
            "creator_user_id": g.account_id,
        }

        # check if tag already exits for fund-round TODO: Move logic to the datastore to reduce calls?
        for tag_item in fund_round_tags:
            if tag["value"] == tag_item.value:
                errors = {"value": ["Tag already exists for this round. Please ensure that the tag is unique."]}
                return render_template(
                    "tagging/create_tag.html",
                    form=new_tag_form,
                    tag_types=tag_types,
                    tag_config=Config.TAGGING_PURPOSE_CONFIG,
                    fund_round=fund_round,
                    errors=errors,
                    migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
                )

        tag_created = post_new_tag_for_fund_round(fund_id, round_id, tag)

        if not tag_created:
            errors = {
                "value": [
                    "Failed to create tag. Tags must be unique, only contain"
                    " apostrophes, hyphens, letters, digits, and spaces."
                ]
            }
            return render_template(
                "tagging/create_tag.html",
                form=new_tag_form,
                tag_types=tag_types,
                tag_config=Config.TAGGING_PURPOSE_CONFIG,
                fund_round=fund_round,
                errors=errors,
                migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
            )
        if go_back and tag_created:
            return redirect(
                url_for(
                    "tagging_bp.load_fund_round_tags",
                    fund_id=fund_id,
                    round_id=round_id,
                )
            )

        return redirect(url_for("tagging_bp.create_tag", fund_id=fund_id, round_id=round_id))

    elif request.method == "POST":
        current_app.logger.info("Tag creation form failed validation: {errors}", extra=dict(errors=new_tag_form.errors))
        errors = new_tag_form.errors

    return render_template(
        "tagging/create_tag.html",
        form=new_tag_form,
        tag_types=tag_types,
        tag_config=Config.TAGGING_PURPOSE_CONFIG,
        fund_round=fund_round,
        errors=errors,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


@tagging_bp.route("/tags/deactivate/<fund_id>/<round_id>/<tag_id>", methods=["GET", "POST"])
@check_access_fund_id_round_id(roles_required=["ASSESSOR"])
def deactivate_tag(fund_id, round_id, tag_id):
    deactivate_tag_form = DeactivateTagForm()
    tag_to_deactivate = get_tag_for_fund_round(fund_id, round_id, tag_id)
    fund = get_fund(
        fund_id,
        use_short_name=False,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    round = get_round(
        fund_id,
        round_id,
        use_short_name=False,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    fund_round = {
        "fund_name": fund.name,
        "round_name": round.title,
        "fund_id": fund_id,
        "round_id": round_id,
    }
    if deactivate_tag_form.validate_on_submit():
        current_app.logger.info(
            "Tag deactivation form validated, deactivating tag_id: {tag_id}.", extra=dict(tag_id=tag_id)
        )
        tag_update_to_deactivate = [{"id": tag_id, "active": False}]
        tag_deactivated = update_tags(fund_id, round_id, tag_update_to_deactivate)
        if tag_deactivated:
            return redirect(
                url_for(
                    "tagging_bp.load_fund_round_tags",
                    fund_id=fund_id,
                    round_id=round_id,
                )
            )
        flash(TAG_DEACTIVATE_ERROR_MESSAGE)

    elif request.method == "POST":
        current_app.logger.info(
            "Tag deactivation form failed validation: {errors}", extra=dict(errors=deactivate_tag_form.errors)
        )
        flash(TAG_DEACTIVATE_ERROR_MESSAGE)
    return render_template(
        "tagging/deactivate_tag.html",
        form=deactivate_tag_form,
        tag=tag_to_deactivate,
        tag_config=Config.TAGGING_PURPOSE_CONFIG,
        fund_round=fund_round,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


@tagging_bp.route("/tags/reactivate/<fund_id>/<round_id>/<tag_id>", methods=["GET", "POST"])
@check_access_fund_id_round_id(roles_required=["ASSESSOR"])
def reactivate_tag(fund_id, round_id, tag_id):
    reactivate_tag_form = ReactivateTagForm()
    tag_to_reactivate = get_tag_for_fund_round(fund_id, round_id, tag_id)
    fund = get_fund(
        fund_id,
        use_short_name=False,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    round = get_round(
        fund_id,
        round_id,
        use_short_name=False,
        ttl_hash=get_ttl_hash(Config.LRU_CACHE_TIME),
    )
    fund_round = {
        "fund_name": fund.name,
        "round_name": round.title,
        "fund_id": fund_id,
        "round_id": round_id,
    }
    if reactivate_tag_form.validate_on_submit():
        current_app.logger.info(
            "Tag reactivation form validated, reactivating tag_id: {tag_id}.", extra=dict(tag_id=tag_id)
        )
        tag_to_reactivate = [{"id": tag_id, "active": True}]
        tag_reactivated = update_tags(fund_id, round_id, tag_to_reactivate)
        if tag_reactivated:
            return redirect(
                url_for(
                    "tagging_bp.load_fund_round_tags",
                    fund_id=fund_id,
                    round_id=round_id,
                )
            )
        flash(TAG_REACTIVATE_ERROR_MESSAGE)
    elif request.method == "POST":
        current_app.logger.info(
            "Tag reactivation form failed validation: {errors}", extra=dict(errors=reactivate_tag_form.errors)
        )
        flash(TAG_REACTIVATE_ERROR_MESSAGE)
    return render_template(
        "tagging/reactivate_tag.html",
        form=reactivate_tag_form,
        tag=tag_to_reactivate,
        tag_config=Config.TAGGING_PURPOSE_CONFIG,
        fund_round=fund_round,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


@tagging_bp.route("/tags/edit/<fund_id>/<round_id>/<tag_id>", methods=["GET", "POST"])
@check_access_fund_id_round_id(roles_required=["ASSESSOR"])
def edit_tag(fund_id, round_id, tag_id):
    edit_tag_form = EditTagForm()
    fund_round = get_fund_round(fund_id, round_id)
    tag = get_tag(fund_id, round_id, tag_id)
    if request.method == "GET":
        current_app.logger.info("Loading edit tag page for id {tag_id}", extra=dict(tag_id=tag_id))

    elif request.method == "POST":
        current_app.logger.info("In edit tag post")
        if edit_tag_form.validate_on_submit():
            # Save changes
            payload = {"id": tag_id, "value": edit_tag_form.value.data}
            if update_tag(fund_id, round_id, payload):
                return redirect(
                    url_for(
                        "tagging_bp.load_fund_round_tags",
                        fund_id=fund_id,
                        round_id=round_id,
                    )
                )
            else:
                flash("An error occurred and your changes were not saved. Please try again later.")
        else:
            current_app.logger.info(
                "Edit tag form failed validation: {errors}", extra=dict(errors=edit_tag_form.errors)
            )
            flash(FLAG_ERROR_MESSAGE)

    return render_template(
        "tagging/edit_tag.html",
        form=edit_tag_form,
        fund_round=fund_round,
        tag=tag,
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )
