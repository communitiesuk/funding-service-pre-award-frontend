from flask import current_app, redirect, render_template, request
from fsd_utils.authentication.decorators import login_requested

from assess.authentication.auth import auth_protect
from config import Config


def not_found(error):
    current_app.logger.debug(error)

    if request.host == current_app.config["ASSESS_HOST"]:

        @login_requested
        def check_auth():
            pass

        check_auth()

        return auth_protect(
            minimum_roles_required=["COMMENTER"],
            unprotected_routes=["/", "/healthcheck", "/cookie_policy"],
        ) or redirect("/")

    if request.host == current_app.config["AUTH_HOST"]:
        return render_template(
            "authenticator/404.html",
            is_error=True,
            support_desk_apply=Config.SUPPORT_DESK_APPLY,
        ), 404

    return render_template(
        "apply/404.html",
        is_error=True,
        support_desk_apply=Config.SUPPORT_DESK_APPLY,
    ), 404


def internal_server_error(error):
    current_app.logger.error(error)

    if request.host == current_app.config["ASSESS_HOST"]:
        return render_template("assess/500.html", is_error=True), 500

    if request.host == current_app.config["AUTHENTICATOR_HOST"]:
        return render_template("authenticator/500.html", is_error=True), 500

    return render_template("apply/500.html", is_error=True), 500
