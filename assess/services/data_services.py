from copy import deepcopy
from functools import lru_cache
from typing import Collection, Dict, List, Optional, Set, Union
from urllib.parse import urlencode

import requests
from flask import abort, current_app
from fsd_utils.locale_selector.get_lang import get_lang

from assess.scoring.models.score import Score
from assess.services.models.application import Application
from assess.services.models.banner import Banner
from assess.services.models.comment import Comment, CommentType
from assess.services.models.flag import Flag, FlagType
from assess.services.models.fund import Fund
from assess.services.models.round import Round
from assess.services.models.sub_criteria import SubCriteria
from assess.shared.helpers import get_ttl_hash
from assess.tagging.models.tag import AssociatedTag, Tag, TagType
from assess.themes.deprecated_theme_mapper import (
    map_application_with_sub_criteria_themes_fields,
)
from config import Config


def get_data(endpoint: str, payload: Dict = None):
    try:
        if payload:
            current_app.logger.info(
                "Fetching data from '{endpoint}', with payload: {payload}.",
                extra=dict(endpoint=endpoint, payload=payload),
            )
            response = requests.get(endpoint, payload)
        else:
            current_app.logger.info("Fetching data from '{endpoint}'.", extra=dict(endpoint=endpoint))
            response = requests.get(endpoint)
        if response.status_code == 200:
            if "application/json" == response.headers["Content-Type"]:
                return response.json()
            else:
                return response.content
        elif response.status_code in [204, 404]:
            current_app.logger.warning(
                "Request successful but no resources returned for endpoint '{endpoint}'.", extra=dict(endpoint=endpoint)
            )
        else:
            current_app.logger.error("Could not get data for endpoint '{endpoint}' ", extra=dict(endpoint=endpoint))
    except requests.exceptions.RequestException as e:
        current_app.logger.exception("{e}", extra=dict(e=str(e)))


def get_assessment_progress(application_metadata, fund_id, round_id):
    application_ids_list = {"application_ids": [x.get("application_id") for x in application_metadata]}
    endpoint_url = Config.ASSESSMENT_PROGRESS_ENDPOINT.format(fund_id=fund_id, round_id=round_id)
    current_app.logger.info(
        "Fetching assessment progress from '{endpoint_url}', with json payload: {application_ids_list}.",
        extra=dict(endpoint_url=endpoint_url, application_ids_list=application_ids_list),
    )
    response = requests.post(endpoint_url, json=application_ids_list)

    if not response.ok:
        current_app.logger.error(
            "Could not get assessment progress for endpoint '{endpoint_url}'", extra=dict(endpoint_url=endpoint_url)
        )
        return application_metadata

    response_json = response.json()
    for res in response_json:
        for am in application_metadata:
            if am.get("application_id") == res.get("application_id"):
                am["progress"] = res.get("progress")

    return application_metadata


def call_search_applications(params: dict | str):
    applications_endpoint = Config.APPLICATION_STORE_API_HOST + Config.APPLICATION_SEARCH_ENDPOINT.format(
        params=urlencode(params)
    )
    applications_response = get_data(applications_endpoint)
    return applications_response


def get_application_assignments(application_id, only_active=False):
    application_assignments_endpoint = Config.ASSESSMENT_ASSIGNED_USERS_ENDPOINT.format(application_id=application_id)
    current_app.logger.info(
        "Endpoint '{application_assignments_endpoint}'.",
        extra=dict(application_assignments_endpoint=application_assignments_endpoint),
    )
    query_params = {"active": "true"} if only_active else {}
    response = get_data(application_assignments_endpoint, query_params)

    return response if response is not None else []


def get_application_overviews(fund_id, round_id, search_params):
    overviews_endpoint = (
        Config.ASSESSMENT_STORE_API_HOST
    ) + Config.APPLICATION_OVERVIEW_ENDPOINT_FUND_ROUND_PARAMS.format(
        fund_id=fund_id, round_id=round_id, params=urlencode(search_params)
    )
    current_app.logger.info("Endpoint '{overviews_endpoint}'.", extra=dict(overviews_endpoint=overviews_endpoint))
    overviews_response = get_data(overviews_endpoint)

    return overviews_response


def get_users_for_fund(
    fund_short_name,
    round_short_name=None,
    include_assessors=None,
    include_commenters=None,
):
    query_params = {}
    if round_short_name:
        query_params["round_short_name"] = round_short_name

    if include_assessors:
        query_params["include_assessors"] = include_assessors

    if include_commenters:
        query_params["include_commenters"] = include_commenters

    users_for_fund = (Config.ACCOUNT_STORE_API_HOST) + Config.USER_FUND_ENDPOINT.format(fund_short_name=fund_short_name)

    current_app.logger.info("Endpoint '{users_for_fund}'.", extra=dict(users_for_fund=users_for_fund))
    users_for_fund_response = get_data(users_for_fund, query_params)

    return users_for_fund_response


def get_tags_for_fund_round(fund_id, round_id, search_params: dict | None = None) -> List[Tag]:
    if search_params is None:
        search_params = {}
    endpoint = Config.ASSESSMENT_TAGS_ENDPOINT.format(
        fund_id=fund_id, round_id=round_id, params=urlencode(search_params)
    )
    response = get_data(endpoint)
    if response is not None:
        current_app.logger.info("tags returned: {len}", extra=dict(len=len(response)))
        result = [Tag.from_dict(item) for item in response]
        return result
    else:
        current_app.logger.info(
            "No tags found for fund {fund_id}, round {round_id}.", extra=dict(fund_id=fund_id, round_id=round_id)
        )
        return []


def get_tag_for_fund_round(fund_id, round_id, tag_id) -> Tag:
    endpoint = Config.ASSESSMENT_TAG_ENDPOINT.format(fund_id=fund_id, round_id=round_id, tag_id=tag_id)
    response = get_data(endpoint)
    if response is not None:
        current_app.logger.info("tag returned: {len}", extra=dict(len=len(response)))
        result = Tag.from_dict(response)
        return result
    else:
        current_app.logger.info(
            "No tag found for fund {fund_id}, round {round_id}, tag_id {tag_id}.",
            extra=dict(fund_id=fund_id, round_id=round_id, tag_id=tag_id),
        )
        return None


def update_tags(fund_id, round_id, tags) -> bool:
    endpoint = Config.ASSESSMENT_UPDATE_TAGS_ENDPOINT.format(fund_id=fund_id, round_id=round_id)
    payload = [
        {
            "id": tag.get("id", None),
            "tag_type_id": tag.get("tag_type_id", None),
            "active": tag.get("active", None),
        }
        for tag in tags
    ]

    current_app.logger.info("Requesting update for of the following tags: {payload}", extra=dict(payload=payload))
    response = requests.put(endpoint, json=payload)

    was_successful = response.ok
    if not was_successful:
        current_app.logger.error(
            "Update associated tags failed, code: {status_code}.", extra=dict(status_code=response.status_code)
        )
    return was_successful


def get_tag_types() -> List[TagType]:
    endpoint = Config.ASSESSMENT_TAG_TYPES_ENDPOINT
    response = get_data(endpoint)
    if response is not None:
        current_app.logger.info("tags returned: {len}", extra=dict(len=len(response)))
        result = [TagType.from_dict(item) for item in response]
        return result
    else:
        current_app.logger.info("No tag types found.")
        return []


def post_new_tag_for_fund_round(fund_id, round_id, tag) -> bool:
    endpoint = Config.ASSESSMENT_TAGS_ENDPOINT.format(fund_id=fund_id, round_id=round_id, params=None)
    current_app.logger.info(
        "Posting the following tag: {tag}for fund {fund_id} and round {round_id}.",
        extra=dict(tag=tag, fund_id=fund_id, round_id=round_id),
    )
    response = requests.post(endpoint, json=tag)
    tag_created = response.ok
    if not tag_created:
        current_app.logger.error("Post tag failed, code: {status_code}.", extra=dict(status_code=response.status_code))

    return tag_created


def get_associated_tags_for_application(application_id) -> List[Tag]:
    endpoint = Config.ASSESSMENT_ASSOCIATE_TAGS_ENDPOINT.format(application_id=application_id)
    result = get_data(endpoint)
    if result:
        current_app.logger.info("tags returned: {len}", extra=dict(len=len(result)))
        result = [AssociatedTag.from_dict(item) for item in result if item["associated"] is True]
        return result
    else:
        current_app.logger.info(
            "No associated tags found for application: {application_id}.", extra=dict(application_id=application_id)
        )
        return None


def get_all_associated_tags_for_application(application_id) -> List[Tag]:
    endpoint = Config.APPLICATION_ASSOCIATED_ALL_TAGS_ENDPOINT.format(application_id=application_id)
    result = get_data(endpoint)
    if result:
        result = [AssociatedTag.from_dict(item) for item in result]
        return result
    else:
        current_app.logger.info(
            "No associated tags found for application: {application_id}.", extra=dict(application_id=application_id)
        )
        return []


def update_associated_tags(application_id, tags) -> bool:
    endpoint = Config.ASSESSMENT_ASSOCIATE_TAGS_ENDPOINT.format(application_id=application_id)
    payload = [{"id": tag["tag_id"], "user_id": tag["user_id"]} for tag in tags]

    current_app.logger.info(
        "Requesting the following tags: {payload} associate with application_id '{application_id}'",
        extra=dict(payload=payload, application_id=application_id),
    )
    response = requests.put(endpoint, json=payload)
    was_successful = response.ok
    if not was_successful:
        current_app.logger.error(
            "Update associated tags failed, code: {status_code}.", extra=dict(status_code=response.status_code)
        )
    return was_successful


@lru_cache(maxsize=1)
def get_funds(ttl_hash=None) -> Union[List[Fund], None]:
    del ttl_hash  # unused, but required for lru_cache
    current_app.logger.info("Fetching funds from fund store.")
    endpoint = Config.FUND_STORE_API_HOST + Config.FUNDS_ENDPOINT
    response = get_data(endpoint)
    if response and len(response) > 0:
        funds = []
        for fund in response:
            funds.append(Fund.from_json(fund))
        return funds
    current_app.logger.error("Error retrieving funds from fund store, please check this.")
    return []


def get_all_fund_short_codes() -> Set[str]:
    all_funds = get_funds(get_ttl_hash(seconds=Config.LRU_CACHE_TIME))
    return {fund.short_name for fund in all_funds} if all_funds else {}


@lru_cache(maxsize=1)
def get_fund(fid: str, use_short_name: bool = False, ttl_hash=None) -> Union[Fund, None]:
    del ttl_hash  # unused, but required for lru_cache
    endpoint = Config.FUND_STORE_API_HOST + Config.FUND_ENDPOINT.format(fund_id=fid, use_short_name=use_short_name)
    response = get_data(endpoint)
    if not response:
        return None

    fund = Fund.from_json(response)
    if "rounds" in response and len(response["rounds"]) > 0:
        for fund_round in response["rounds"]:
            fund.add_round(Round.from_json(fund_round))
    return fund


@lru_cache(maxsize=1)
def get_rounds(fund_id: str, ttl_hash=None) -> list[Round]:
    del ttl_hash  # unused, but required for lru_cache
    endpoint = Config.FUND_STORE_API_HOST + Config.ROUNDS_ENDPOINT.format(fund_id=fund_id)
    response = get_data(endpoint)

    rounds = []
    if response and len(response) > 0:
        for round_data in response:
            rounds.append(Round.from_dict(round_data))
    return rounds


@lru_cache(maxsize=1)
def get_round(fid: str, rid: str, use_short_name: bool = False, ttl_hash=None) -> Union[Round, None]:
    del ttl_hash  # unused, but required for lru_cache
    round_endpoint = Config.FUND_STORE_API_HOST + Config.ROUND_ENDPOINT.format(
        fund_id=fid, round_id=rid, use_short_name=use_short_name
    )
    round_response = get_data(round_endpoint)
    current_app.logger.info(round_response)
    if round_response and "assessment_deadline" in round_response:
        round_dict = Round.from_dict(round_response)
        return round_dict
    return None


@lru_cache(maxsize=1)
def get_available_teams(fund_id: str, round_id: str, ttl_hash=None) -> list:
    del ttl_hash  # unused, but required for lru_cache
    teams_available = get_data(
        Config.GET_AVIALABLE_TEAMS_FOR_FUND.format(
            fund_id=fund_id,
            round_id=round_id,
        )
    )
    return teams_available or []


def get_bulk_accounts_dict(account_ids: List, fund_short_name: str):
    if account_ids:
        account_ids_to_retrieve = list(set(account_ids))
        account_url = Config.BULK_ACCOUNTS_ENDPOINT
        account_params = {"account_id": account_ids_to_retrieve}
        users_result = get_data(account_url, account_params)
        if Config.FLASK_ENV == "development":
            debug_user_config = deepcopy(Config.DEBUG_USER)
            debug_user_config["email_address"] = Config.DEBUG_USER["email"]
            debug_user_config["highest_role_map"] = {fund_short_name: Config.DEBUG_USER_ROLE}
            users_result[Config.DEBUG_USER_ACCOUNT_ID] = debug_user_config

        for user_result in users_result.values():
            # we only need the highest role for the fund we are currently viewing
            highest_role = user_result["highest_role_map"].get(fund_short_name, "")
            user_result["highest_role"] = highest_role
            del user_result["highest_role_map"]

        return users_result
    else:
        current_app.logger.info("No account ids supplied")
        return {}


def get_score_and_justification(application_id, sub_criteria_id=None, score_history=True):
    score_url = Config.ASSESSMENT_SCORES_ENDPOINT
    score_params = {
        "application_id": application_id,
        "sub_criteria_id": sub_criteria_id,
        "score_history": score_history,
    }
    score_response = get_data(score_url, score_params)
    if score_response:
        current_app.logger.info(
            "Response from Assessment Store: '{score_response}'.", extra=dict(score_response=score_response)
        )

    else:
        current_app.logger.info(
            "No scores found for application: {application_id}, sub_criteria_id: {sub_criteria_id}",
            extra=dict(application_id=application_id, sub_criteria_id=sub_criteria_id),
        )
    return score_response


def match_score_to_user_account(scores, fund_short_name):
    account_ids = [score["user_id"] for score in scores]
    bulk_accounts_dict = get_bulk_accounts_dict(
        account_ids,
        fund_short_name,
    )
    scores_with_account: list[Score] = [
        Score.from_dict(
            score
            | {
                "user_full_name": bulk_accounts_dict[score["user_id"]]["full_name"],
                "user_email": bulk_accounts_dict[score["user_id"]]["email_address"],
                "highest_role": bulk_accounts_dict[score["user_id"]]["highest_role"],
            }
        )
        for score in scores
    ]
    return scores_with_account


def submit_score_and_justification(score, justification, application_id, user_id, sub_criteria_id):
    data_dict = {
        "score": score,
        "justification": justification,
        "user_id": user_id,
        "application_id": application_id,
        "sub_criteria_id": sub_criteria_id,
    }
    url = Config.ASSESSMENT_SCORES_ENDPOINT
    response = requests.post(url, json=data_dict)
    current_app.logger.info("Response from Assessment Store: '{data}'.", extra=dict(data=response.json()))
    return response.ok


def get_applications(params: dict) -> Union[List[Application], None]:
    applications_response = call_search_applications(params)
    if applications_response and len(applications_response) > 0:
        applications = []
        for application_data in applications_response:
            applications.append(Application.from_json(application_data))

        return applications
    return None


def get_application_stats(fund_ids: List = None, round_ids: List = None):
    url = Config.APPLICATION_METRICS_ENDPOINT
    url += f"&fund_id={'&fund_id='.join(fund_ids)}" if fund_ids else None
    url += f"&round_id={'&round_id='.join(round_ids)}" if round_ids else None
    return get_data(url)


def get_assessments_stats(fund_id: str, round_ids: Collection[str], search_params: dict | None = None) -> dict | None:
    if search_params is None:
        search_params = {}
    assessments_stats_endpoint = (Config.ASSESSMENT_STORE_API_HOST) + Config.ASSESSMENTS_STATS_ENDPOINT.format(
        fund_id=fund_id, params=urlencode(search_params)
    )
    current_app.logger.info(
        "Endpoint '{assessments_stats_endpoint}'.", extra=dict(assessments_stats_endpoint=assessments_stats_endpoint)
    )
    response = requests.post(assessments_stats_endpoint, json={"round_ids": list(round_ids)})
    return response.json()


def get_assessor_task_list_state(application_id: str) -> Union[dict, None]:
    overviews_endpoint = (
        Config.ASSESSMENT_STORE_API_HOST
    ) + Config.APPLICATION_OVERVIEW_ENDPOINT_APPLICATION_ID.format(application_id=application_id)

    metadata = get_data(overviews_endpoint)
    return metadata


def get_application_metadata(application_id: str) -> Union[dict, None]:
    application_endpoint = Config.APPLICATION_METADATA_ENDPOINT.format(application_id=application_id)
    application_metadata = get_data(application_endpoint)
    return application_metadata


def get_questions(application_id):
    """_summary_: Function is set up to retrieve
    the data from application store with
    get_data() function.
    Args:
        application_id: Takes an application_id.
    Returns:
        Returns a dictionary of questions & their statuses.
    """
    status_endpoint = Config.APPLICATION_STORE_API_HOST + Config.APPLICATION_STATUS_ENDPOINT.format(
        application_id=application_id
    )

    questions = get_data(status_endpoint)
    if questions:
        data = {title: status for title, status in questions.items()}
        return data


def get_sub_criteria(application_id, sub_criteria_id):
    """_summary_: Function is set up to retrieve
    the data from assessment store with
    get_data() function.
    Args:
        application_id:
        sub_criteria_id
    Returns:
      {
        "sub_criteria_id": "",
        "sub_criteria_name": "",
        "score_submitted": "",
        "themes": []
    }
    """
    sub_criteria_endpoint = Config.ASSESSMENT_STORE_API_HOST + Config.SUB_CRITERIA_OVERVIEW_ENDPOINT.format(
        application_id=application_id, sub_criteria_id=sub_criteria_id
    )
    sub_criteria_response = get_data(sub_criteria_endpoint)
    if sub_criteria_response and "id" in sub_criteria_response:
        return SubCriteria.from_filtered_dict(sub_criteria_response)
    else:
        current_app.logger.warning(
            "sub_criteria: '{sub_criteria_id}' not found.", extra=dict(sub_criteria_id=sub_criteria_id)
        )
        abort(404, description=f"sub_criteria: '{sub_criteria_id}' not found.")


def get_sub_criteria_banner_state(application_id: str):
    SUB_CRITERIA_BANNER_STATE_ENDPOINT = (
        Config.ASSESSMENT_STORE_API_HOST
        + Config.SUB_CRITERIA_BANNER_STATE_ENDPOINT.format(application_id=application_id)
    )

    banner = get_data(SUB_CRITERIA_BANNER_STATE_ENDPOINT)

    if banner:
        return Banner.from_filtered_dict(banner)
    else:
        current_app.logger.warning(
            "banner_state: '{application_id}' not found.", extra=dict(application_id=application_id)
        )
        abort(404, description=f"banner_state: '{application_id}' not found.")


def get_flag(flag_id: str) -> Optional[Flag]:
    flag = get_data(Config.ASSESSMENT_FLAG_ENDPOINT.format(flag_id=flag_id))
    if flag:
        return Flag.from_dict(flag)
    else:
        current_app.logger.warning("flag for id: '{flag_id}' not found.", extra=dict(flag_id=flag_id))
        return None


def get_flags(application_id: str) -> List[Flag]:
    flag = get_data(Config.ASSESSMENT_FLAGS_ENDPOINT.format(application_id=application_id))
    if flag:
        return Flag.from_list(flag)
    else:
        return []


def get_qa_complete(application_id: str) -> dict:
    qa_complete = get_data(Config.ASSESSMENT_GET_QA_STATUS_ENDPOINT.format(application_id=application_id))
    return qa_complete


def submit_flag(
    application_id: str,
    flag_type: str,
    user_id: str,
    justification: str = None,
    section: str = None,
    allocation: str = None,
    flag_id: str = None,
) -> Flag | None:
    """Submits a new flag to the assessment store for an application.
    Returns Flag if a flag is created

    :param application_d: The application the flag belongs to.
    :param flag_type: The type of flag (e.g: 'FLAGGED' or 'STOPPED')
    :param user_id: The id of the user raising the flag
    :param justification: The justification for raising the flag
    :param section: The assessment section the flag has been raised for.
    """
    flag_type = FlagType[flag_type]
    if flag_id:
        flag = requests.put(
            Config.ASSESSMENT_FLAGS_POST_ENDPOINT,
            json={
                "assessment_flag_id": flag_id,
                "justification": justification,
                "user_id": user_id,
                "allocation": allocation,
                "status": flag_type.value,
            },
        )
    else:
        flag = requests.post(
            Config.ASSESSMENT_FLAGS_POST_ENDPOINT,
            json={
                "application_id": application_id,
                "justification": justification,
                "sections_to_flag": section,
                "user_id": user_id,
                "allocation": allocation,
                "status": flag_type.value,
            },
        )
    if flag:
        flag_json = flag.json()
        return Flag.from_dict(flag_json)


def get_all_uploaded_documents_theme_answers(
    application_id: str,
) -> Union[list, None]:
    return get_sub_criteria_theme_answers_all(
        application_id,
        "all_uploaded_documents",
    )


def get_sub_criteria_theme_answers_all(
    application_id: str,
    theme_id: str,
) -> Union[list, None]:
    theme_mapping_data_url = (
        f"{Config.ASSESSMENT_STORE_API_HOST}"
        f"{Config.SUB_CRITERIA_THEME_ANSWERS_ENDPOINT.format(application_id=application_id)}"
    )
    theme_mapping_data = get_data(theme_mapping_data_url)
    return map_application_with_sub_criteria_themes_fields(
        theme_mapping_data["application_json"],
        theme_mapping_data["sub_criterias"],
        theme_id,
    )


def get_all_sub_criterias_with_application_json(application_id: str):
    theme_mapping_data_url = (
        f"{Config.ASSESSMENT_STORE_API_HOST}"
        f"{Config.SUB_CRITERIA_THEME_ANSWERS_ENDPOINT.format(application_id=application_id)}"
    )
    theme_mapping_data = get_data(theme_mapping_data_url)
    return theme_mapping_data


def get_comments(
    application_id: str = None,
    sub_criteria_id: str = None,
    theme_id: str = None,
    comment_id: str = None,
    comment_type: CommentType = None,
):
    """_summary_: Get comments from the assessment store
    Args:
        application_id: application_id,
        sub_criteria_id: sub_criteria_id
        theme_id: optional theme_id (else returns all comments for subcriteria)
    Returns:
        Returns a dictionary of comments.
    """
    query_params = {
        "application_id": application_id,
        "sub_criteria_id": sub_criteria_id,
        "theme_id": theme_id,
        "comment_id": comment_id,
        "comment_type": comment_type,
    }
    # Strip theme_id from dict if None
    query_params_strip_nones = {k: v for k, v in query_params.items() if v is not None}
    comment_endpoint = f"{Config.ASSESSMENT_COMMENT_ENDPOINT}?{urlencode(query=query_params_strip_nones)}"
    comment_response = get_data(comment_endpoint)

    if not comment_response or len(comment_response) == 0:
        current_app.logger.info(
            "No comments found for application: {application_id}, sub_criteria_id: {sub_criteria_id}",
            extra=dict(application_id=application_id, sub_criteria_id=sub_criteria_id),
        )
        return None
    else:
        return comment_response


def match_comment_to_theme(comment_response, themes, fund_short_name):
    """_summary_: match the comment response to its theme and account information
    Args:
        comment_response: assessment store comments response for a theme,
        themes: list of subcriteria themes
        fund_short_name: fund short name
    Returns:
        Returns a dictionary of comments.
    """
    account_ids = [comment["user_id"] for comment in comment_response]
    bulk_accounts_dict = get_bulk_accounts_dict(
        account_ids,
        fund_short_name,
    )

    comments: list[Comment] = [
        Comment.from_dict(
            comment
            | {
                "full_name": bulk_accounts_dict[comment["user_id"]]["full_name"],
                "email_address": bulk_accounts_dict[comment["user_id"]]["email_address"],
                "highest_role": bulk_accounts_dict[comment["user_id"]]["highest_role"],
                "fund_short_name": fund_short_name,
            }
        )
        for comment in comment_response
    ]

    if not themes:
        theme_id_to_comments_list_map = {"": [comment for comment in comments if comment.theme_id == ""]}
    else:
        theme_id_to_comments_list_map = {
            theme.id: [comment for comment in comments if comment.theme_id == theme.id] for theme in themes
        }

    return theme_id_to_comments_list_map


def submit_comment(
    comment,
    application_id=None,
    sub_criteria_id=None,
    user_id=None,
    theme_id=None,
    comment_id=None,
    comment_type=None,
):
    if not comment_id:
        data_dict = {
            "comment": comment,
            "user_id": user_id,
            "application_id": application_id,
            "sub_criteria_id": sub_criteria_id,
            "comment_type": comment_type,
            "theme_id": theme_id,
        }
        url = Config.ASSESSMENT_COMMENT_ENDPOINT
        response = requests.post(url, json=data_dict)
    else:
        data_dict = {
            "comment": comment,
            "comment_id": comment_id,
        }
        url = Config.ASSESSMENT_COMMENT_ENDPOINT
        response = requests.put(url, json=data_dict)

    current_app.logger.info("Response from Assessment Store: '{data}'.", extra=dict(data=response.json()))
    return response.ok


def get_application_json(application_id):
    endpoint = Config.APPLICATION_JSON_ENDPOINT.format(application_id=application_id)
    response = requests.get(endpoint)
    return response.json()


def get_default_round_data():
    language = {"language": get_lang()}
    round_request_url = Config.GET_ROUND_DATA_FOR_FUND_ENDPOINT.format(
        fund_id=Config.DEFAULT_FUND_ID, round_id=Config.DEFAULT_ROUND_ID
    )
    round_response = get_data(round_request_url, language)
    return round_response


def get_application_sections_display_config(fund_id: str, round_id: str, language: str):
    application_display_request_url = Config.GET_APPLICATION_DISPLAY_FOR_FUND_ENDPOINT.format(
        fund_id=fund_id, round_id=round_id, language=language
    )
    application_display_response = get_data(application_display_request_url)
    return application_display_response


def get_tag(fund_id, round_id, tag_id) -> Tag:
    endpoint = Config.ASSESSMENT_GET_TAG_ENDPOINT.format(fund_id=fund_id, round_id=round_id, tag_id=tag_id)
    response = get_data(endpoint)
    if response:
        return Tag.from_dict(response)
    return None


def update_tag(fund_id: str, round_id: str, updated_tag: Dict) -> Tag:
    endpoint = Config.ASSESSMENT_UPDATE_TAGS_ENDPOINT.format(fund_id=fund_id, round_id=round_id)
    response = requests.put(url=endpoint, json=[updated_tag])
    if response.status_code == 200:
        return response.json()[0]

    current_app.logger.error("Unable to update tag: {updated_tag}", extra=dict(updated_tag=updated_tag))
    return None


def get_applicant_export(fund_id, round_id, report_type):
    applicant_export_endpoint = Config.APPLICANT_EXPORT_ENDPOINT.format(
        fund_id=fund_id, round_id=round_id, report_type=report_type
    )

    current_app.logger.info(
        "Endpoint '{applicant_export_endpoint}'.", extra=dict(applicant_export_endpoint=applicant_export_endpoint)
    )
    applicant_export_response = get_data(applicant_export_endpoint)

    return applicant_export_response


def get_applicant_feedback_and_survey_report(fund_id, round_id, status_only):
    applicant_feedback_endpoint = Config.APPLICATION_FEEDBACK_SURVEY_REPORT_ENDPOINT.format(
        fund_id=fund_id, round_id=round_id, status_only=status_only
    )

    current_app.logger.info(
        "Endpoint '{applicant_feedback_endpoint}'.", extra=dict(applicant_feedback_endpoint=applicant_feedback_endpoint)
    )
    response = get_data(applicant_feedback_endpoint)

    return response


def get_scoring_system(round_id: str) -> List[Flag]:
    scoring_endpoint = Config.ASSESSMENT_SCORING_SYSTEM_ENDPOINT.format(round_id=round_id)
    current_app.logger.info("Calling endpoint '{scoring_endpoint}'.", extra=dict(scoring_endpoint=scoring_endpoint))
    scoring_system = get_data(scoring_endpoint)["scoring_system"]
    return scoring_system


def assign_user_to_assessment(
    application_id: str,
    user_id: str,
    assigner_id: str,
    update: Optional[bool] = False,
    active: Optional[bool] = True,
    send_email: Optional[bool] = False,
    email_content: Optional[str] = None,
):
    """Creates a user association between a user and an application.
    Internally, this is how we assign a user to an assessment.

    :param application_id: The application to be assigned
    :param user_id: The id of the user to be assigned
    :param assigner_id: The id of the user who is creating the assignment
    :param update: update assignment if it already exists
    :param active: Whether or not to mark the assignment as active (only used if update is True)
    :param send_email: If an email notification should be sent when the (un)assignment is processed
    :param email_content: Custom message to be sent by email (only applicable if send_email is True)
    """
    assignment_endpoint = Config.ASSESSMENT_ASSOCIATE_USER_ENDPOINT.format(
        application_id=application_id, user_id=user_id
    )
    json_body = {"active": active, "send_email": send_email, "assigner_id": assigner_id}
    if email_content:
        json_body["email_content"] = email_content
    if update:
        response = requests.put(assignment_endpoint, json=json_body)
    else:
        response = requests.post(assignment_endpoint, json=json_body)
    if not response.ok:
        current_app.logger.error(
            "Could not get assign user {user_id} to application {application_id}",
            extra=dict(user_id=user_id, application_id=application_id),
        )
        return None

    return response.json()
