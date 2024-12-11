from flask import current_app, render_template

from assess.services.data_services import get_default_round_data
from common.blueprints import Blueprint
from config import Config

shared_bp = Blueprint("shared_bp", __name__, template_folder="templates")


@shared_bp.route("/")
def index():
    return render_template(
        "shared/index.html",
        login_url=Config.SSO_LOGIN_URL,
        logout_url=Config.SSO_LOGOUT_URL,
        assessment_url=Config.ASSESSMENT_HUB_ROUTE + "/fund_dashboard/",
    )


@shared_bp.route("/cookie_policy", methods=["GET"])
def cookie_policy():
    current_app.logger.info("Cookie policy page loaded.")
    return render_template(
        "assess/cookie_policy.html",
        migration_banner_enabled=Config.MIGRATION_BANNER_ENABLED,
    )


@shared_bp.route("/help", methods=["GET"])
def get_help():
    round_data = get_default_round_data() or {}
    return render_template(
        "assess/get_help.html",
        # TODO: this contact information is for the round, so different email.
        # contact_details=round_data.get('contact_details'),
        contact_details={"email_address": "fundingservice.support@communities.gov.uk"},
        support_availability=round_data.get("support_availability"),
    )
