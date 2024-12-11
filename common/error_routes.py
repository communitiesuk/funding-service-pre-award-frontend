from flask import request, current_app, render_template, redirect
from fsd_utils.authentication.decorators import login_requested

from assess.authentication.auth import auth_protect


def not_found(error):
    current_app.logger.error(error)

    if request.host == current_app.config['ASSESS_HOST']:
        @login_requested
        def check_auth():
            pass

        check_auth()

        return auth_protect(
            minimum_roles_required=["COMMENTER"],
            unprotected_routes=["/", "/healthcheck", "/cookie_policy"],
        ) or redirect('/')

    return render_template("apply/404.html", is_error=True), 404
    

def internal_server_error(error):
    current_app.logger.error(error)

    if request.host == current_app.config['ASSESS_HOST']:
        return render_template("assess/500.html", is_error=True), 500

    return render_template("apply/500.html", is_error=True), 500
