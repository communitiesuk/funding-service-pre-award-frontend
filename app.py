from os import getenv
from urllib.parse import urlencode, urljoin

from flask import Flask, current_app, g, make_response, render_template, request, url_for
from flask_assets import Environment
from flask_babel import Babel, gettext, pgettext
from flask_compress import Compress
from flask_redis import FlaskRedis
from flask_session import Session
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from fsd_utils import init_sentry
from fsd_utils.healthchecks.checkers import FlaskRunningChecker, RedisChecker
from fsd_utils.healthchecks.healthcheck import Healthcheck
from fsd_utils.logging import logging
from fsd_utils.services.aws_extended_client import SQSExtendedClient
from fsd_utils.toggles.toggles import create_toggles_client, initialise_toggles_redis_store, load_toggles
from jinja2 import ChoiceLoader, PackageLoader, PrefixLoader

import static_assets
from apply.filters import (
    custom_format_datetime,
    date_format_short_month,
    datetime_format,
    datetime_format_full_month,
    datetime_format_short_month,
    kebab_case_to_human,
    snake_case_to_human,
    status_translation,
    string_to_datetime,
)
from apply.helpers import find_fund_and_round_in_request, find_fund_in_request
from assess.shared.filters import (
    add_to_dict,
    all_caps_to_human,
    assess_datetime_format,
    ast_literal_eval,
    datetime_format_24hr,
    format_address,
    format_project_ref,
    remove_dashes_underscores_capitalize,
    remove_dashes_underscores_capitalize_keep_uppercase,
    slash_separated_day_month_year,
    utc_to_bst,
)
from common.locale_selector.get_lang import get_lang
from common.locale_selector.set_lang import LanguageSelector
from config import Config

redis_mlinks = FlaskRedis(config_prefix="REDIS_MLINKS")


def create_app() -> Flask:  # noqa: C901
    init_sentry()

    flask_app = Flask(
        __name__,
        static_url_path="/assets",
        static_folder="static",
        host_matching=True,
        static_host="<host_from_current_request>",
    )

    flask_app.config.from_object("config.Config")

    toggle_client = None
    if getenv("FLASK_ENV") != "unit_test":
        initialise_toggles_redis_store(flask_app)
        toggle_client = create_toggles_client()
        load_toggles(Config.FEATURE_CONFIG, toggle_client)

    babel = Babel(flask_app)
    babel.locale_selector_func = get_lang
    LanguageSelector(flask_app)

    # Bundle and compile assets
    assets = Environment()
    assets.init_app(flask_app)
    static_assets.init_assets(flask_app, auto_build=Config.ASSETS_AUTO_BUILD)

    flask_app.jinja_loader = ChoiceLoader(
        [
            PackageLoader("apply"),
            PackageLoader("assess"),
            # move everything into one templates folder for assess rather than nesting in blueprints
            PackageLoader("assess.shared"),
            PackageLoader("assess.assessments"),
            PackageLoader("assess.flagging"),
            PackageLoader("assess.tagging"),
            PackageLoader("assess.scoring"),
            PackageLoader("authenticator.frontend"),
            PrefixLoader({"govuk_frontend_jinja": PackageLoader("govuk_frontend_jinja")}),
        ]
    )

    flask_app.jinja_env.trim_blocks = True
    flask_app.jinja_env.lstrip_blocks = True
    flask_app.jinja_env.add_extension("jinja2.ext.i18n")
    flask_app.jinja_env.globals["get_lang"] = get_lang
    flask_app.jinja_env.globals["pgettext"] = pgettext

    flask_app.jinja_env.filters["datetime_format_short_month"] = datetime_format_short_month
    flask_app.jinja_env.filters["datetime_format_full_month"] = datetime_format_full_month
    flask_app.jinja_env.filters["string_to_datetime"] = string_to_datetime
    flask_app.jinja_env.filters["custom_format_datetime"] = custom_format_datetime
    flask_app.jinja_env.filters["date_format_short_month"] = date_format_short_month
    flask_app.jinja_env.filters["datetime_format"] = datetime_format
    flask_app.jinja_env.filters["snake_case_to_human"] = snake_case_to_human
    flask_app.jinja_env.filters["kebab_case_to_human"] = kebab_case_to_human
    flask_app.jinja_env.filters["status_translation"] = status_translation

    # Assess filters
    flask_app.jinja_env.filters["ast_literal_eval"] = ast_literal_eval
    flask_app.jinja_env.filters["assess_datetime_format"] = assess_datetime_format
    flask_app.jinja_env.filters["utc_to_bst"] = utc_to_bst
    flask_app.jinja_env.filters["add_to_dict"] = add_to_dict
    flask_app.jinja_env.filters["slash_separated_day_month_year"] = slash_separated_day_month_year
    flask_app.jinja_env.filters["all_caps_to_human"] = all_caps_to_human
    flask_app.jinja_env.filters["datetime_format_24hr"] = datetime_format_24hr
    flask_app.jinja_env.filters["format_project_ref"] = format_project_ref
    flask_app.jinja_env.filters["remove_dashes_underscores_capitalize"] = remove_dashes_underscores_capitalize
    flask_app.jinja_env.filters["remove_dashes_underscores_capitalize_keep_uppercase"] = (
        remove_dashes_underscores_capitalize_keep_uppercase
    )
    flask_app.jinja_env.filters["format_address"] = format_address

    # Initialise logging
    logging.init_app(flask_app)

    # Initialize sqs extended client
    create_sqs_extended_client(flask_app)
    # Initialise Sessions
    session = Session()
    session.init_app(flask_app)

    # Initialise Redis Magic Links Store
    redis_mlinks.init_app(flask_app)

    # Configure application security with Talisman
    Talisman(flask_app, **Config.TALISMAN_SETTINGS)

    # This section is needed for url_for("foo", _external=True) to
    # automatically generate http scheme when this sample is
    # running on localhost, and to generate https scheme when it is
    # deployed behind reversed proxy.
    # See also #proxy_setups section at
    # flask.palletsprojects.com/en/1.0.x/deploying/wsgi-standalone
    from werkzeug.middleware.proxy_fix import ProxyFix

    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_proto=1, x_host=1)

    csrf = CSRFProtect()
    csrf.init_app(flask_app)

    Compress(flask_app)

    # These are required to associated errorhandlers and before/after request decorators with their blueprints
    import assess.blueprint_middleware  # noqa
    import apply.default.error_routes  # noqa

    from apply.default.account_routes import account_bp
    from apply.default.application_routes import application_bp
    from apply.default.content_routes import content_bp
    from apply.default.eligibility_routes import eligibility_bp
    from apply.default.routes import default_bp
    from assess.assessments.routes import assessment_bp
    from assess.flagging.routes import flagging_bp
    from assess.scoring.routes import scoring_bp
    from assess.shared.routes import shared_bp
    from assess.tagging.routes import tagging_bp
    from common.error_routes import internal_server_error, not_found
    from authenticator.frontend.default.routes import (
        default_bp as authenticator_default_bp,
    )
    from authenticator.frontend.magic_links.routes import magic_links_bp
    from authenticator.frontend.sso.routes import sso_bp
    from authenticator.frontend.user.routes import user_bp
    from authenticator.api.magic_links.routes import api_magic_link_bp
    from authenticator.api.session.auth_session import api_sessions_bp
    from authenticator.api.sso.routes import api_sso_bp

    flask_app.register_error_handler(404, not_found)
    flask_app.register_error_handler(500, internal_server_error)

    flask_app.register_blueprint(default_bp, host=flask_app.config["APPLY_HOST"])
    flask_app.register_blueprint(application_bp, host=flask_app.config["APPLY_HOST"])
    flask_app.register_blueprint(content_bp, host=flask_app.config["APPLY_HOST"])
    flask_app.register_blueprint(eligibility_bp, host=flask_app.config["APPLY_HOST"])
    flask_app.register_blueprint(account_bp, host=flask_app.config["APPLY_HOST"])

    flask_app.register_blueprint(shared_bp, host=flask_app.config["ASSESS_HOST"])
    flask_app.register_blueprint(tagging_bp, host=flask_app.config["ASSESS_HOST"])
    flask_app.register_blueprint(flagging_bp, host=flask_app.config["ASSESS_HOST"])
    flask_app.register_blueprint(scoring_bp, host=flask_app.config["ASSESS_HOST"])
    flask_app.register_blueprint(assessment_bp, host=flask_app.config["ASSESS_HOST"])

    flask_app.register_blueprint(authenticator_default_bp, host=flask_app.config["AUTH_HOST"])
    flask_app.register_blueprint(magic_links_bp, host=flask_app.config["AUTH_HOST"])
    flask_app.register_blueprint(sso_bp, host=flask_app.config["AUTH_HOST"])
    flask_app.register_blueprint(user_bp, host=flask_app.config["AUTH_HOST"])
    flask_app.register_blueprint(api_magic_link_bp, host=flask_app.config["AUTH_HOST"])
    flask_app.register_blueprint(api_sso_bp, host=flask_app.config["AUTH_HOST"])
    flask_app.register_blueprint(api_sessions_bp, host=flask_app.config["AUTH_HOST"])

    @flask_app.url_defaults
    def inject_host_from_current_request(endpoint, values):
        if app.url_map.is_endpoint_expecting(endpoint, "host_from_current_request"):
            values["host_from_current_request"] = request.host

    @flask_app.url_value_preprocessor
    def pop_host_from_current_request(endpoint, values):
        if values is not None:
            values.pop("host_from_current_request", None)

    @flask_app.context_processor
    def inject_global_constants():
        if request.host == current_app.config["APPLY_HOST"]:
            return dict(
                stage="beta",
                service_meta_author="Department for Levelling up Housing and Communities",
                toggle_dict={feature.name: feature.is_enabled() for feature in toggle_client.list()}
                if toggle_client
                else {},
                support_desk_apply=Config.SUPPORT_DESK_APPLY,
            )
        elif request.host == current_app.config["ASSESS_HOST"]:
            return dict(
                stage="beta",
                service_title="Assessment Hub – GOV.UK",
                service_meta_description="Assessment Hub",
                service_meta_keywords="Assessment Hub",
                service_meta_author="DLUHC",
                sso_logout_url=flask_app.config.get("SSO_LOGOUT_URL"),
                g=g,
                toggle_dict=(
                    {feature.name: feature.is_enabled() for feature in toggle_client.list()} if toggle_client else {}
                ),
                support_desk_assess=Config.SUPPORT_DESK_ASSESS,
            )
        elif request.host == current_app.config["AUTH_HOST"]:
            query_params = urlencode({"fund": request.args.get("fund", ""), "round": request.args.get("round", "")})
            return dict(
                stage="beta",
                service_meta_author="Ministry of Housing, Communities and Local Government",
                accessibility_statement_url=urljoin(Config.APPLICANT_FRONTEND_HOST, "/accessibility_statement"),  # noqa
                cookie_policy_url=urljoin(Config.APPLICANT_FRONTEND_HOST, "/cookie_policy"),
                contact_us_url=urljoin(Config.APPLICANT_FRONTEND_HOST, f"/contact_us?{query_params}"),
                privacy_url=urljoin(Config.APPLICANT_FRONTEND_HOST, f"/privacy?{query_params}"),
                feedback_url=urljoin(Config.APPLICANT_FRONTEND_HOST, f"/feedback?{query_params}"),
            )

    @flask_app.context_processor
    def utility_processor():
        def _get_service_title():
            fund = None
            if request.view_args or request.args or request.form:
                try:
                    fund = find_fund_in_request()
                except Exception as e:  # noqa
                    current_app.logger.warning(
                        "Exception: %s, occured when trying to reach url: %s, with view_args: %s, and args: %s",
                        e,
                        request.url,
                        request.view_args,
                        request.args,
                    )
            if fund:
                return gettext("Apply for") + " " + fund.title
            elif (
                request.args
                and (return_app := request.args.get("return_app"))
                and request.host == current_app.config["AUTH_HOST"]
            ):
                return Config.SAFE_RETURN_APPS[return_app].service_title

            return gettext("Access Funding")

        return dict(get_service_title=_get_service_title)

    @flask_app.context_processor
    def inject_content_urls():
        try:
            fund, round = find_fund_and_round_in_request()
            if fund and round:
                return dict(
                    accessibility_statement_url=url_for(
                        "content_routes.accessibility_statement",
                        fund=fund.short_name,
                        round=round.short_name,
                    ),
                    contact_us_url=url_for(
                        "content_routes.contact_us",
                        fund=fund.short_name,
                        round=round.short_name,
                    ),
                    privacy_url=url_for(
                        "content_routes.privacy",
                        fund=fund.short_name,
                        round=round.short_name,
                    ),
                    feedback_url=url_for(
                        "content_routes.feedback",
                        fund=fund.short_name,
                        round=round.short_name,
                    ),
                )
        except Exception as e:  # noqa
            current_app.logger.warning(
                "Exception: %s, occured when trying to reach url: %s, with view_args: %s, and args: %s",
                e,
                request.url,
                request.view_args,
                request.args,
            )
        return dict(
            accessibility_statement_url=url_for("content_routes.accessibility_statement"),
            contact_us_url=url_for("content_routes.contact_us"),
            privacy_url=url_for("content_routes.privacy"),
            feedback_url=url_for("content_routes.feedback"),
        )

    @flask_app.after_request
    def after_request(response):
        if request.path.endswith("js") or request.path.endswith("css"):
            response.headers["Cache-Control"] = "public, max-age=3600"

        elif "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    @flask_app.before_request
    def filter_all_requests():
        if flask_app.config.get("MAINTENANCE_MODE") and not (
            request.path.endswith("js") or request.path.endswith("css") or request.path.endswith("/healthcheck")
        ):
            current_app.logger.warning(
                "Application is in the Maintenance mode reach url: {url}", extra=dict(url=request.url)
            )

            if request.host == current_app.config["ASSESS_HOST"]:
                maintenance_template = "assess/maintenance.html"
            else:
                maintenance_template = "apply/maintenance.html"

            return (
                render_template(
                    maintenance_template,
                    maintenance_end_time=flask_app.config.get("MAINTENANCE_END_TIME"),
                ),
                503,
            )

        if request.path == "/favicon.ico":
            return make_response("404"), 404

    health = Healthcheck(flask_app)
    health.add_check(FlaskRunningChecker())
    health.add_check(RedisChecker(redis_mlinks))

    return flask_app


def create_sqs_extended_client(flask_app):
    if (
        getenv("AWS_ACCESS_KEY_ID", "Access Key Not Available") == "Access Key Not Available"
        and getenv("AWS_SECRET_ACCESS_KEY", "Secret Key Not Available") == "Secret Key Not Available"
    ):
        flask_app.extensions["sqs_extended_client"] = SQSExtendedClient(
            region_name=Config.AWS_REGION,
            endpoint_url=getenv("AWS_ENDPOINT_OVERRIDE", None),
            large_payload_support=Config.AWS_MSG_BUCKET_NAME,
            always_through_s3=True,
            delete_payload_from_s3=True,
            logger=flask_app.logger,
        )
    else:
        flask_app.extensions["sqs_extended_client"] = SQSExtendedClient(
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION,
            endpoint_url=getenv("AWS_ENDPOINT_OVERRIDE", None),
            large_payload_support=Config.AWS_MSG_BUCKET_NAME,
            always_through_s3=True,
            delete_payload_from_s3=True,
            logger=flask_app.logger,
        )


app = create_app()
