import csv
from collections import OrderedDict
from io import StringIO
from typing import Dict, List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from flask import Response, url_for
from fsd_utils import NotifyConstants
from fsd_utils.mapping.application.application_utils import format_answer, simplify_title

from assess.assessments.models.common import Option, OptionGroup
from assess.services.aws import generate_url, list_files_by_prefix
from assess.services.models.flag import FlagType
from assess.services.models.fund import Fund
from assess.shared.filters import utc_to_bst
from assess.shared.helpers import determine_display_status
from assess.tagging.models.tag import AssociatedTag
from config import Config
from assess.config.display_value_mappings import assessment_statuses


def get_team_flag_stats(application_overviews) -> List[Dict]:
    def create_team_dict(team_name):
        return {
            "team_name": team_name,
            "raised": 0,
            "resolved": 0,
            "stopped": 0,
        }

    team_flag_stats = []

    for assessment in application_overviews:
        for flag in assessment.get("flags", []):
            latest_status = flag.get("latest_status")
            allocated_team = flag.get("latest_allocation")

            if allocated_team not in [team["team_name"] for team in team_flag_stats]:
                team_flag_stats.append(create_team_dict(allocated_team))

            for team in team_flag_stats:
                if team["team_name"] == allocated_team:
                    if latest_status == FlagType.RAISED.value:
                        team["raised"] += 1
                    elif latest_status == FlagType.STOPPED.value:
                        team["stopped"] += 1
                    elif latest_status == FlagType.RESOLVED.value:
                        team["resolved"] += 1

    return team_flag_stats


def generate_maps_from_form_names(
    data,
):
    form_name_to_title = OrderedDict()
    form_name_to_path = OrderedDict()

    for item in data:
        if item["form_name"]:
            form_name_to_title[item["form_name"]] = item["title"]
            form_name_to_path[item["form_name"]] = item["path"]

        if item["children"]:
            (
                child_form_name_to_title,
                child_form_name_to_path,
            ) = generate_maps_from_form_names(item["children"])
            form_name_to_title.update(child_form_name_to_title)
            form_name_to_path.update(child_form_name_to_path)

    return form_name_to_title, form_name_to_path


def set_application_status_in_overview(application_overviews):
    """Add the 'application_status' key and return the modified list of application overviews."""
    for overview in application_overviews:
        display_status = determine_display_status(
            overview["workflow_status"],
            overview["flags"],
            overview["is_qa_complete"],
        )
        status = ""
        for key, val in assessment_statuses.items():
            if val == display_status:
                status = key
                break
        if not status:
            status = display_status
        overview["application_status"] = status

    return application_overviews


def set_assigned_info_in_overview(application_overviews, users_for_fund):
    users_for_fund_dict = {user["account_id"]: user for user in users_for_fund} if users_for_fund else {}
    users_not_found = []
    for overview in application_overviews:
        overview["assigned_to_names"] = []
        overview["assigned_to_ids"] = []
        if "user_associations" in overview and overview["user_associations"]:
            for user_assocation in overview["user_associations"]:
                user_id = user_assocation["user_id"]
                if user_assocation["active"]:
                    overview["assigned_to_ids"].append(user_id)
                    try:
                        user_details = users_for_fund_dict[user_id]
                        overview["assigned_to_names"].append(
                            user_details["full_name"] if user_details["full_name"] else user_details["email_address"]
                        )
                    except KeyError:
                        users_not_found.append(user_id)

    return application_overviews, users_not_found


def get_tag_map_and_tag_options(tag_types, fund_round_tags, post_processed_overviews):
    tag_option_groups = [
        OptionGroup(
            label=", ".join(p.capitalize() for p in purposes),
            options=sorted(
                [
                    Option(value=tag.id, text_content=tag.value)
                    for tag in fund_round_tags
                    if tag.type_id in {tag_type.id for tag_type in tag_types if tag_type.purpose in purposes}
                ],
                key=lambda option: option.text_content,
            ),
        )
        for purposes in Config.TAGGING_FILTER_CONFIG
    ]
    tags_in_application_map = {}
    for overview in post_processed_overviews:
        tags_in_application_map[overview["application_id"]] = (
            [
                AssociatedTag(
                    application_id=overview["application_id"],
                    tag_id=item["tag"]["id"],
                    value=item["tag"]["value"],
                    user_id=item["user_id"],
                    associated=item["associated"],
                    purpose=item["tag"]["tag_type"]["purpose"],
                )
                for item in overview["tag_associations"]
                if item["associated"] is True and item["tag"]["active"] is True
            ]
            if overview["tag_associations"]
            else None
        )

    return tags_in_application_map, tag_option_groups


def generate_csv_of_application(q_and_a: dict, fund: Fund, application_json, fund_round_name=None):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Fund", fund_round_name, fund.id])
    writer.writerow(
        [
            "Application",
            application_json["short_id"],
            application_json["application_id"],
        ]
    )
    writer.writerow(["Section", "Question", "Answer"])
    for section_name, values in q_and_a.items():
        section_title = simplify_title(section_name, remove_text=["cof", "ns"])
        section_title = " ".join(section_title).capitalize()
        for questions, answers in values.items():
            if answers and isinstance(answers, str) and answers.startswith("- "):
                answers = f"'{answers}"

            if not answers:
                answers = "Not provided"

            writer.writerow([section_title, questions, format_answer(answer=answers, language="en")])
    return output.getvalue()


_EXCLUDED_HEADERS = (
    "Help with insolvency",
    "Help with organisation type",
    "Help with public authority",
    "Help gydag awdurdod cyhoeddus",
    "Help gyda'r math o sefydliad",
)


def generate_assessment_info_csv(data: dict):
    output = StringIO()
    headers = list(OrderedDict.fromkeys(key for d in data for key in d.keys() if key not in _EXCLUDED_HEADERS))
    csv_writer = csv.writer(output)

    if len(data) == 0:
        return output.getvalue()

    csv_writer.writerow(headers)

    for data_entry in data:
        rows = [data_entry.get(header, "") for header in headers]
        csv_writer.writerow(rows)

    return output.getvalue()


def download_file(data, mimetype, file_name):
    return Response(
        data,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment;filename={quote_plus(file_name)}"},
    )


def get_files_for_application_upload_fields(application_id: str, short_id: str, application_json: dict) -> List[tuple]:
    """
    This function retrieves the file names from an application_json
    then uses this to create a lsit of tuples containing the file name
    and download link for this file.

    Parameters:
    application_id (str): The unique identifier of the application.
    short_id (str): The unique short-hand identifier of the application.
    application_json (dict): The jsonified data for an application

    Returns:
    List[tuple]: A list of tuples, where each tuple contains the
    file name and its download link.
    """
    forms = application_json["jsonb_blob"]["forms"]
    file_names = []

    for form in forms:
        for question in form[NotifyConstants.APPLICATION_QUESTIONS_FIELD]:
            for field in question["fields"]:
                if field["type"] == "file" and field.get("answer"):
                    file_names.append(field["answer"])

    # files which used the old file upload component
    legacy_files = [
        (
            file,
            url_for(
                "assessment_bp.get_file",
                application_id=application_id,
                file_name=file,
                short_id=short_id,
            ),
        )
        for file in file_names
    ]

    # files which used the client side file upload component
    client_side_upload_files = list_files_by_prefix(application_id)
    files = [(file.filename, generate_url(file, short_id)) for file in client_side_upload_files]

    return legacy_files + files


def convert_bool_value(value, language=None):
    if value:
        return "Oes" if language == "cy" else "Yes"
    if not value:
        return "Nac Oes" if language == "cy" else "No"
    if value is None:
        return "Not sure"


def strip_tags(text):
    if text == ["none"]:
        return "Not sure"
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()


def _sanitise_data(data, language=None):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = _sanitise_data(value, language)

    if isinstance(data, list):
        data = [_sanitise_data(d, language) for d in data]

    if isinstance(data, bool):
        data = convert_bool_value(data, language)
    if isinstance(data, str):
        data = strip_tags(data)
    return data


def sanitise_export_data(data, language=None):
    if "cy_list" in data and data["cy_list"]:
        language = "cy"
        data["cy_list"] = _sanitise_data(data["cy_list"], language)

    if "en_list" in data and data["en_list"]:
        language = "en"
        data["en_list"] = _sanitise_data(data["en_list"], language)
    return data


def convert_datetime_to_bst(data):
    for _data in data.values():
        for _date in _data:
            date_submitted = _date.get("Date Submitted")
            if date_submitted:
                _date["Date Submitted"] = utc_to_bst(value=date_submitted, export_format=True)
    return data


def sort_assigned_column(first, second):
    """
    The ordering for the assigned column is as follows:
        Single assignee with name
        Single assignee with email
        Multiple assignees with names
        Multiple assignees with names and emails
        Multiple emails
        Unassigned
    """

    def get_hierachy_level(assignees):
        level = None
        # Check if project is unassigned. This is the highest lexicographic position
        if len(assignees) == 0:
            level = 6
        # Check if project has been assigned to a single individual
        elif len(assignees) == 1:
            # Named user has a lower lexicographic position than an email alias
            level = 2 if "@" in assignees[0] else 1
        else:
            # Otherwise multiple assignees. Named assignees come first
            if all("@" not in assignee for assignee in assignees):
                level = 3
            else:
                # Mixed named assignees and email aliases come next. Followed by email only aliases.
                level = 5 if all("@" in assignee for assignee in assignees) else 4
        return level

    first_level = get_hierachy_level(first["assigned_to_names"])
    second_level = get_hierachy_level(second["assigned_to_names"])

    if first_level < second_level:
        return -1
    elif first_level > second_level:
        return 1
    else:
        sorted_first = sorted(first["assigned_to_names"])
        sorted_second = sorted(second["assigned_to_names"])
        return -1 if sorted_first < sorted_second else 1 if sorted_first > sorted_second else 0
