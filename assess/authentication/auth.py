from flask import g, redirect, request
from fsd_utils.authentication.models import User

from assess.services.data_services import get_funds
from assess.shared.helpers import get_ttl_hash
from config import Config


def auth_protect(minimum_roles_required: list, unprotected_routes: list):
    """
    Checks the authentication and authorisation attributes of the
    user accessing the service and allows them to access the requested
    resource if authorised, or redirect them to login (or a permissions
    error message) if not authenticated/authorised.

    The function also incorporates support for bypassing authorisation
    via setting of a DEBUG_USER_ROLE env var which will mimic the effect
    of a user with that role (only used when FLASK_ENV is "development").

    Args:
        minimum_roles_required: List[str]
            - a list of minimum roles a user must at least one of to be authorised
        unprotected_routes: List[str]
            - a list of routes e.g. ["/"]
                that can be accessed without authentication

    Returns:
        redirect (302) or None if authorised

    """
    # expand roles to include all fund short names as a prefix, e.g. "COMMENTER" becomes "COF_COMMENTER"
    minimum_roles_required = [
        f"{fund.short_name}_{role}".upper()
        for fund in get_funds(
            get_ttl_hash(seconds=Config.LRU_CACHE_TIME)
        )  # expensive call, so cache it & refresh every 5 minutes
        for role in minimum_roles_required
    ]

    if not g.is_authenticated and Config.FLASK_ENV == "development" and Config.DEBUG_USER_ON:
        g.is_authenticated = True
        g.account_id = Config.DEBUG_USER_ACCOUNT_ID
        g.user = User(**Config.DEBUG_USER)
        g.is_debug_user = True
        if request.path in ["/"]:
            return redirect(Config.DASHBOARD_ROUTE)

    elif g.is_authenticated:
        # Ensure that authenticated users have
        # all minimum required roles
        if not g.user.roles or not any(  # any of the minimum roles are present
            role_required in g.user.roles for role_required in minimum_roles_required
        ):
            return redirect(
                Config.AUTHENTICATOR_HOST + "/service/user" + "?roles_required=" + "|".join(minimum_roles_required)
            )
        elif request.path in ["", "/"]:
            return redirect(Config.DASHBOARD_ROUTE)
    elif request.path not in unprotected_routes and not request.path.startswith("/static/"):  # noqa
        # Redirect unauthenticated users to
        # login on the home page
        return redirect("/")
