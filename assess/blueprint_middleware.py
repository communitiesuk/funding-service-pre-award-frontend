from flask import current_app, render_template, request
from fsd_utils.authentication.decorators import login_requested

from assess.assessments.routes import assessment_bp
from assess.authentication.auth import auth_protect
from assess.flagging.routes import flagging_bp
from assess.scoring.routes import scoring_bp
from assess.shared.routes import shared_bp
from assess.tagging.routes import tagging_bp

@assessment_bp.errorhandler(404)
@flagging_bp.errorhandler(404)
@scoring_bp.errorhandler(404)
@shared_bp.errorhandler(404)
@tagging_bp.errorhandler(404)
def not_found(error):
    current_app.logger.info("Encountered 404 against url {request_path}", extra=dict(request_path=request.path))
    return render_template("assess/404.html"), 404


@assessment_bp.errorhandler(403)
@flagging_bp.errorhandler(403)
@scoring_bp.errorhandler(403)
@shared_bp.errorhandler(403)
@tagging_bp.errorhandler(403)
def forbidden(error):
    # Override the default message to match design if no custom message is provided
    error.description = (
        "You do not have permission to access this page."
        if "It is either read-protected or not readable by the server." in error.description
        else error.description
    )

    current_app.logger.info("Encountered 403: {error}", extra=dict(error=str(error)))
    return (
        render_template("assess/403.html", error_description=error.description),
        403,
    )

@assessment_bp.errorhandler(503)
@flagging_bp.errorhandler(503)
@scoring_bp.errorhandler(503)
@shared_bp.errorhandler(503)
@tagging_bp.errorhandler(503)
def error_503(error):
    return render_template("assess/maintenance.html"), 503



@assessment_bp.errorhandler(500)
@assessment_bp.errorhandler(Exception)
@shared_bp.errorhandler(500)
@shared_bp.errorhandler(Exception)
@flagging_bp.errorhandler(500)
@flagging_bp.errorhandler(Exception)
@tagging_bp.errorhandler(500)
@tagging_bp.errorhandler(Exception)
@scoring_bp.errorhandler(500)
@scoring_bp.errorhandler(Exception)
def internal_server_error(error):
    current_app.logger.exception("Encountered 500: {error}", extra=dict(error=str(error)))
    return render_template("assess/500.html"), 500


@shared_bp.before_request
@tagging_bp.before_request
@flagging_bp.before_request
@scoring_bp.before_request
@assessment_bp.before_request
@login_requested
def assess_ensure_minimum_required_roles():
    return auth_protect(
        minimum_roles_required=["COMMENTER"],
        unprotected_routes=["/", "/healthcheck", "/cookie_policy"],
    )
