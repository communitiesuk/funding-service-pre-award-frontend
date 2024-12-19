import traceback

from flask import current_app, render_template

from common.blueprints import Blueprint
from config import Config

default_bp = Blueprint("default_bp", __name__, template_folder="templates")


@default_bp.route("/")
def index():
    return render_template("authenticator/index.html")


@default_bp.errorhandler(404)
def not_found(error):
    return render_template(
        "authenticator/404.html",
        is_error=True,
        support_desk_apply=Config.SUPPORT_DESK_APPLY,
    ), 404


@default_bp.errorhandler(500)
def internal_server_error(error):
    error_message = f"Encountered 500: {error}"
    stack_trace = traceback.format_exc()
    current_app.logger.error(
        "{error_message}\n{stack_trace}", extra=dict(error_message=error_message, stack_trace=stack_trace)
    )

    return render_template("authenticator/500.html", is_error=True), 500
