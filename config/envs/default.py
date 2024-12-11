"""Flask configuration."""

import base64
from distutils.util import strtobool
from os import environ, getenv
import os
from pathlib import Path

from fsd_utils import CommonConfig, configclass


@configclass
class DefaultConfig:
    # Application Config
    FLASK_ENV = environ.get("FLASK_ENV", "development")
    SECRET_KEY = CommonConfig.SECRET_KEY
    SESSION_COOKIE_NAME = environ.get("SESSION_COOKIE_NAME", "session_cookie")
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_TIME_LIMIT = CommonConfig.WTF_CSRF_TIME_LIMIT
    MAINTENANCE_MODE = strtobool(getenv("MAINTENANCE_MODE", "False"))
    MAINTENANCE_END_TIME = getenv("MAINTENANCE_END_TIME", "soon")

    APPLY_HOST = getenv("APPLY_HOST", "frontend.levellingup.gov.localhost:3008")
    ASSESS_HOST = getenv("ASSESS_HOST", "assessment.levellingup.gov.localhost:3010")

    # assess STATIC_URL_PATH = "app/static"
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"
    LOCAL_SERVICE_NAME = "local_flask"
    FLASK_ROOT = str(Path(__file__).parent.parent.parent)

    # Funding Service Design
    FSD_USER_TOKEN_COOKIE_NAME = "fsd_user_token"
    AUTHENTICATOR_HOST = environ.get("AUTHENTICATOR_HOST", "https://authenticator.levellingup.gov.localhost:4004")
    ENTER_APPLICATION_URL = AUTHENTICATOR_HOST + "/service/magic-links/new"
    MAGIC_LINK_URL = (
        AUTHENTICATOR_HOST + "/service/magic-links/new?" + "fund={fund_short_name}&round={round_short_name}"
    )
    SESSION_COOKIE_DOMAIN = environ.get("SESSION_COOKIE_DOMAIN")
    COOKIE_DOMAIN = environ.get("COOKIE_DOMAIN", None)

    # RSA 256 KEYS
    RSA256_PUBLIC_KEY_BASE64 = environ.get("RSA256_PUBLIC_KEY_BASE64")
    if RSA256_PUBLIC_KEY_BASE64:
        RSA256_PUBLIC_KEY = base64.b64decode(RSA256_PUBLIC_KEY_BASE64).decode()

    # APIs Config
    TEST_APPLICATION_STORE_API_HOST = CommonConfig.TEST_APPLICATION_STORE_API_HOST
    TEST_FUND_STORE_API_HOST = CommonConfig.TEST_FUND_STORE_API_HOST
    TEST_ACCOUNT_STORE_API_HOST = CommonConfig.TEST_ACCOUNT_STORE_API_HOST

    ACCOUNT_STORE_API_HOST = environ.get("ACCOUNT_STORE_API_HOST", TEST_ACCOUNT_STORE_API_HOST)
    ACCOUNTS_ENDPOINT = "/accounts"
    APPLICATION_STORE_API_HOST = environ.get("APPLICATION_STORE_API_HOST", TEST_APPLICATION_STORE_API_HOST)
    GET_APPLICATION_ENDPOINT = APPLICATION_STORE_API_HOST + "/applications/{application_id}"
    SEARCH_APPLICATIONS_ENDPOINT = (
        APPLICATION_STORE_API_HOST + "/applications?order_by=last_edited&order_rev=1&{search_params}"
    )
    GET_APPLICATIONS_FOR_ACCOUNT_ENDPOINT = (
        APPLICATION_STORE_API_HOST + "/applications?account_id={account_id}" + "&order_by=last_edited&order_rev=1"
    )
    UPDATE_APPLICATION_FORM_ENDPOINT = APPLICATION_STORE_API_HOST + "/applications/forms"
    SUBMIT_APPLICATION_ENDPOINT = APPLICATION_STORE_API_HOST + "/applications/{application_id}/submit"
    FEEDBACK_ENDPOINT = APPLICATION_STORE_API_HOST + "/application/feedback"
    END_OF_APP_SURVEY_FEEDBACK_ENDPOINT = APPLICATION_STORE_API_HOST + "/application/end_of_application_survey_data"
    RESEARCH_SURVEY_ENDPOINT = APPLICATION_STORE_API_HOST + "/application/research"

    FUND_STORE_API_HOST = environ.get("FUND_STORE_API_HOST", TEST_FUND_STORE_API_HOST)
    GET_ALL_FUNDS_ENDPOINT = FUND_STORE_API_HOST + "/funds"
    GET_FUND_DATA_ENDPOINT = FUND_STORE_API_HOST + "/funds/{fund_id}"
    GET_ALL_ROUNDS_FOR_FUND_ENDPOINT = FUND_STORE_API_HOST + "/funds/{fund_id}/rounds"
    GET_ROUND_DATA_FOR_FUND_ENDPOINT = FUND_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}"
    GET_FUND_DATA_BY_SHORT_NAME_ENDPOINT = FUND_STORE_API_HOST + "/funds/{fund_short_name}"
    GET_ROUND_DATA_BY_SHORT_NAME_ENDPOINT = FUND_STORE_API_HOST + "/funds/{fund_short_name}/rounds/{round_short_name}"

    GET_APPLICATION_DISPLAY_FOR_FUND_ENDPOINT = (
        FUND_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}/sections/application?language={language}"
    )

    FORMS_TEST_HOST = "http://localhost:3009"
    FORMS_SERVICE_NAME = environ.get("FORMS_SERVICE_NAME", "xgov_forms_service")
    FORMS_SERVICE_PUBLIC_HOST = environ.get("FORMS_SERVICE_PUBLIC_HOST", FORMS_TEST_HOST)
    FORMS_SERVICE_PREVIEW_HOST = environ.get("FORMS_SERVICE_PREVIEW_HOST", FORMS_TEST_HOST)
    FORMS_SERVICE_JSONS_PATH = "form_jsons"

    FORMS_SERVICE_PRIVATE_HOST = getenv("FORMS_SERVICE_PRIVATE_HOST")

    FORM_GET_REHYDRATION_TOKEN_URL = (FORMS_SERVICE_PRIVATE_HOST or FORMS_SERVICE_PUBLIC_HOST) + "/session/{form_name}"

    FORM_REHYDRATION_URL = (FORMS_SERVICE_PRIVATE_HOST or FORMS_SERVICE_PUBLIC_HOST) + "/session/{rehydration_token}"
    
    # Content Security Policy
    SECURE_CSP = {
        "default-src": "'self'",
        "script-src": [
            "'self'",
            "'sha256-+6WnXIl4mbFTCARd8N3COQmT3bJJmo32N8q8ZSQAIcU='",
            "'sha256-l1eTVSK8DTnK8+yloud7wZUqFrI0atVo6VlC6PJvYaQ='",
            "'sha256-z+p4q2n8BOpGMK2/OMOXrTYmjbeEhWQQHC3SF/uMOyg='",
            "'sha256-RgdCrr7A9yqYVstE6QiM/9RNRj4bYipcUa2C2ywQT1A='",
            "'sha256-W6+G9WX7ZWCn2Tdi1uHvgAuT45Y2OUJa9kqVxgAM+vM='",
            "'sha256-RgdCrr7A9yqYVstE6QiM/9RNRj4bYipcUa2C2ywQT1A='",
            "'sha256-z+p4q2n8BOpGMK2/OMOXrTYmjbeEhWQQHC3SF/uMOyg='",
            "'sha256-l1eTVSK8DTnK8+yloud7wZUqFrI0atVo6VlC6PJvYaQ='",
            "'sha256-GUQ5ad8JK5KmEWmROf3LZd9ge94daqNvd8xy9YS1iDw='",
            "https://tagmanager.google.com",
            "https://www.googletagmanager.com",
            "https://*.google-analytics.com",
        ],
        "connect-src": [
            "'self'",
            "https://*.google-analytics.com",
        ],  # APPLICATION_STORE_API_HOST_PUBLIC,
        "img-src": ["data:", "'self'", "https://ssl.gstatic.com"],
    }

    # Talisman Config
    FSD_REFERRER_POLICY = "strict-origin-when-cross-origin"
    FSD_SESSION_COOKIE_SAMESITE = "Strict"
    FSD_PERMISSIONS_POLICY = {"interest-cohort": "()"}
    FSD_DOCUMENT_POLICY = {}
    FSD_FEATURE_POLICY = {
        "microphone": "'none'",
        "camera": "'none'",
        "geolocation": "'none'",
    }

    DENY = "DENY"
    SAMEORIGIN = "SAMEORIGIN"
    ALLOW_FROM = "ALLOW-FROM"
    ONE_YEAR_IN_SECS = 31556926
    FORCE_HTTPS = False

    TALISMAN_SETTINGS = {
        "feature_policy": FSD_FEATURE_POLICY,
        "permissions_policy": FSD_PERMISSIONS_POLICY,
        "document_policy": FSD_DOCUMENT_POLICY,
        "force_https": FORCE_HTTPS,
        "force_https_permanent": False,
        "force_file_save": False,
        "frame_options": "SAMEORIGIN",
        "frame_options_allow_from": None,
        "strict_transport_security": True,
        "strict_transport_security_preload": True,
        "strict_transport_security_max_age": ONE_YEAR_IN_SECS,
        "strict_transport_security_include_subdomains": True,
        "content_security_policy": SECURE_CSP,
        "content_security_policy_report_uri": None,
        "content_security_policy_report_only": False,
        # "content_security_policy_nonce_in": None,
        "referrer_policy": FSD_REFERRER_POLICY,
        "session_cookie_secure": True,
        "session_cookie_http_only": True,
        "session_cookie_samesite": FSD_SESSION_COOKIE_SAMESITE,
        "x_content_type_options": True,
        "x_xss_protection": True,
        "content_security_policy_nonce_in": ["script-src"],
    }

    USE_LOCAL_DATA = strtobool(getenv("USE_LOCAL_DATA", "False"))

    # Redis Feature Toggle Configuration
    REDIS_INSTANCE_URI = getenv("REDIS_INSTANCE_URI", "redis://localhost:6379")
    TOGGLES_URL = REDIS_INSTANCE_URI + "/0"
    FEATURE_CONFIG = {"TAGGING": True, "ASSESSMENT_ASSIGNMENT": False, **CommonConfig.dev_feature_configuration}

    # LRU cache settings
    LRU_CACHE_TIME = int(environ.get("LRU_CACHE_TIME", 3600))  # in seconds

    MIGRATION_BANNER_ENABLED = getenv("MIGRATION_BANNER_ENABLED", False)

    # Assess config
    TEXT_AREA_INPUT_MAX_CHARACTERS = 10000
    FSD_LOG_LEVEL = CommonConfig.FSD_LOG_LEVEL
    
    ASSESSMENT_HUB_ROUTE = "/assess"
    DASHBOARD_ROUTE = "/assess/assessor_tool_dashboard"
    
    SSO_LOGIN_URL = AUTHENTICATOR_HOST + "/sso/login"
    SSO_LOGOUT_URL = AUTHENTICATOR_HOST + "/sso/logout"

    ASSESSMENT_STORE_API_HOST = CommonConfig.ASSESSMENT_STORE_API_HOST

    FUNDS_ENDPOINT = CommonConfig.FUNDS_ENDPOINT
    FUND_ENDPOINT = CommonConfig.FUND_ENDPOINT + "?use_short_name={use_short_name}"
    GET_ROUND_DATA_FOR_FUND_ENDPOINT = FUND_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}"
    # TODO: Rework on the avialable teams allocated after implemented in fundstore
    GET_AVIALABLE_TEAMS_FOR_FUND = FUND_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}/available_flag_allocations"

     # Round Store Endpoints

    ROUNDS_ENDPOINT = CommonConfig.ROUNDS_ENDPOINT
    ROUND_ENDPOINT = CommonConfig.ROUND_ENDPOINT + "?use_short_name={use_short_name}"

    # Application Store Endpoints
    APPLICATION_ENDPOINT = CommonConfig.APPLICATION_ENDPOINT
    APPLICATION_STATUS_ENDPOINT = CommonConfig.APPLICATION_STATUS_ENDPOINT
    APPLICATION_SEARCH_ENDPOINT = CommonConfig.APPLICATION_SEARCH_ENDPOINT
    APPLICATION_METRICS_ENDPOINT = (
        APPLICATION_STORE_API_HOST + "/applications/reporting/applications_statuses_data?format=json"
    )
    APPLICATION_FEEDBACK_SURVEY_REPORT_ENDPOINT = (
        APPLICATION_STORE_API_HOST
        + "/applications/get_all_feedbacks_and_survey_report"
        + "?fund_id={fund_id}&round_id={round_id}&status_only={status_only}"
    )

    # Assessment store endpoints
    ASSESSMENTS_STATS_ENDPOINT = "/assessments/get-stats/{fund_id}?{params}"

    APPLICATION_OVERVIEW_ENDPOINT_FUND_ROUND_PARAMS = "/application_overviews/{fund_id}/{round_id}?{params}"

    APPLICATION_OVERVIEW_ENDPOINT_APPLICATION_ID = "/application_overviews/{application_id}"

    USER_APPLICATIONS_ENDPOINT = "/user/{user_id}/applications"

    APPLICATION_JSON_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/application/{application_id}/json"

    APPLICATION_METADATA_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/application/{application_id}/metadata"

    ALL_UPLOADED_DOCUMENTS_THEME_ANSWERS_ENDPOINT = (
        ASSESSMENT_STORE_API_HOST + "/application/{application_id}/all_uploaded_documents"
    )

    SUB_CRITERIA_THEME_ANSWERS_ENDPOINT = "/sub_criteria_themes/{application_id}"

    SUB_CRITERIA_OVERVIEW_ENDPOINT = "/sub_criteria_overview/{application_id}/{sub_criteria_id}"

    SUB_CRITERIA_BANNER_STATE_ENDPOINT = "/sub_criteria_overview/banner_state/{application_id}"

    USER_APPLICATIONS_ENDPOINT = "/user/{user_id}/applications"

    USER_ASSIGNEES_ENDPOINT = "/user/{assigner_id}/assignees"

    ASSESSMENT_SCORES_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/score"
    ASSESSMENT_UPDATE_STATUS = ASSESSMENT_STORE_API_HOST + "/application/{application_id}/status/complete"
    ASSESSMENT_UPDATE_QA_STATUS = ASSESSMENT_STORE_API_HOST + "/qa_complete/{application_id}/{user_id}"

    ASSESSMENT_GET_QA_STATUS_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/qa_complete/{application_id}"

    ASSESSMENT_COMMENT_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/comment"
    ASSESSMENT_PROGRESS_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/progress/{fund_id}/{round_id}"

    ASSESSMENT_FLAGS_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/flags/{application_id}"
    ASSESSMENT_FLAGS_POST_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/flags/"
    ASSESSMENT_FLAG_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/flag_data?flag_id={flag_id}"
    ASSESSMENT_TAGS_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}/tags?{params}"
    ASSESSMENT_TAG_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}/tags/{tag_id}"
    ASSESSMENT_UPDATE_TAGS_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}/tags"
    ASSESSMENT_ASSOCIATE_TAGS_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/application/{application_id}/tag"
    APPLICATION_ASSOCIATED_ALL_TAGS_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/application/{application_id}/tags"
    ASSESSMENT_GET_TAG_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}/tags/{tag_id}"
    ASSESSMENT_GET_TAG_USAGE_ENDPOINT = (
        ASSESSMENT_STORE_API_HOST + "/funds/{fund_id}/rounds/{round_id}/tags/{tag_id}/count"
    )
    ASSESSMENT_TAG_TYPES_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/tag_types"

    ASSESSMENT_ASSOCIATE_USER_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/application/{application_id}/user/{user_id}"

    ASSESSMENT_ASSIGNED_USERS_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/application/{application_id}/users"

    APPLICANT_EXPORT_ENDPOINT = (
        ASSESSMENT_STORE_API_HOST + "/application_fields_export/{fund_id}/{round_id}/{report_type}"
    )

    TAGGING_PURPOSE_CONFIG = {
        "GENERAL": {
            "colour": "blue",
        },
        "PEOPLE": {
            "colour": "grey",
        },
        "POSITIVE": {
            "colour": "green",
        },
        "NEGATIVE": {
            "colour": "red",
        },
        "ACTION": {
            "colour": "yellow",
        },
    }
    TAGGING_FILTER_CONFIG = (
        (
            "POSITIVE",
            "NEGATIVE",
            "ACTION",
        ),
        ("GENERAL",),
        ("PEOPLE",),
    )
    ASSESSMENT_SCORING_SYSTEM_ENDPOINT = ASSESSMENT_STORE_API_HOST + "/scoring-system/{round_id}"

    # Roles

    LEAD_ASSESSOR = "LEAD_ASSESSOR"
    ASSESSOR = "ASSESSOR"

    # Account store endpoints
    BULK_ACCOUNTS_ENDPOINT = ACCOUNT_STORE_API_HOST + "/bulk-accounts"
    USER_FUND_ENDPOINT = "/accounts/fund/{fund_short_name}"

    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = False

    COF_FUND_ID = "47aef2f5-3fcb-4d45-acb5-f0152b5f03c4"
    COF_ROUND_2_ID = "c603d114-5364-4474-a0c4-c41cbf4d3bbd"
    COF_ROUND_2_W3_ID = "5cf439bf-ef6f-431e-92c5-a1d90a4dd32f"

    DEFAULT_FUND_ID = COF_FUND_ID
    DEFAULT_ROUND_ID = COF_ROUND_2_W3_ID

    if "COPILOT_AWS_BUCKET_NAME" in os.environ:
        AWS_BUCKET_NAME = environ.get("COPILOT_AWS_BUCKET_NAME")
        AWS_REGION = environ.get("AWS_REGION")
        ASSETS_AUTO_BUILD = False
