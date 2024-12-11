import inspect
from dataclasses import asdict, dataclass, field
from datetime import datetime

from flask import current_app
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField

from assess.services.data_services import get_bulk_accounts_dict
from assess.services.models.assessor_task_list import AssessorTaskList
from assess.services.models.flag import Flag, FlagType
from assess.tagging.models.tag import AssociatedTag


@dataclass
class BaseModel:
    @classmethod
    def from_list(cls, data_list: list[dict]):
        return [
            cls(
                **{k: v for k, v in d.items() if k in inspect.signature(cls).parameters and k != "date_created"},
                date_created=cls._format_date(d.get("date_created")),
            )
            for d in data_list
        ]

    @staticmethod
    def _format_date(date_str):
        if date_str:
            return datetime.fromisoformat(date_str).strftime("%Y-%m-%d %H:%M:%S")
        return date_str


@dataclass
class AssociatedTags(AssociatedTag):
    full_name: str = ""
    email_address: str = ""
    highest_role: str = ""
    email_address: str = ""
    date_created: str = field(default="", metadata={"name": "created_at"})

    @classmethod
    def from_associated_tags_list(cls, associated_tags_list):
        """Change the  attribute 'created_at' to 'date_created'"""
        return [cls(**asdict(tag), date_created=tag.created_at) for tag in associated_tags_list]


@dataclass
class Flags(BaseModel):
    allocation: str
    date_created: str
    id: str
    justification: str
    status: FlagType
    user_id: str
    sections_to_flag: list = ""
    full_name: str = ""
    email_address: str = ""
    highest_role: str = ""

    @classmethod
    def process_flags(cls, flags_list) -> list[dict]:
        """
        Retrive all flags from updates & add sections_to_flag to RAISED flag.

        Args: flags_list (list): A list of flags.

        Returns:
            list[dict]: A list of dictionaries containing flags with additional attribute.
        """
        result = []

        for flag in flags_list:
            for update in flag.updates:
                if update.get("status").name == "RAISED":
                    sections_to_flag = flag.sections_to_flag

                    updated_update = {
                        **update,
                        "sections_to_flag": sections_to_flag,
                    }
                    result.append(updated_update)
                else:
                    result.append(update)
        return result

    @classmethod
    def from_list(cls, flags_list: list[Flag]):
        if flags_list:
            flags = cls.process_flags(flags_list)
            return super().from_list(flags)
        else:
            return []


@dataclass
class Comments(BaseModel):
    id: str
    comment: str
    comment_type: str
    date_created: str
    sub_criteria_id: str
    theme_id: str
    user_id: str
    full_name: str = ""
    highest_role: str = ""
    email_address: str = ""

    @classmethod
    def process_comments(cls, comments_list: list) -> list[dict]:
        """
        Retrieve all comments from updates and add the following attributes to each comment:
        - "user_id"
        - "sub_criteria_id"
        - "theme_id"
        - "comment_type"
        - "full_name"
        - "email_address"
        - "highest_role"

        Args: comments_list (list): A list of comments.

        Returns:
            list[dict]: A list of dictionaries containing comments with additional attributes.
        """
        result = []

        for comment in comments_list:
            for update in comment.get("updates"):
                updated_update = {
                    **update,
                    "user_id": comment.get("user_id"),
                    "sub_criteria_id": comment.get("sub_criteria_id"),
                    "theme_id": comment.get("theme_id"),
                    "comment_type": comment.get("comment_type"),
                    "full_name": comment.get("full_name"),
                    "email_address": comment.get("email_address"),
                    "highest_role": comment.get("highest_role"),
                }
                result.append(updated_update)

        return result

    @classmethod
    def from_list(cls, comments_list: list[dict]):
        if comments_list:
            comments = cls.process_comments(comments_list)
            return super().from_list(comments)
        else:
            return []


@dataclass
class Scores(BaseModel):
    application_id: str
    date_created: str
    id: str
    justification: str
    score: int
    sub_criteria_id: str
    user_id: str
    full_name: str = ""
    highest_role: str = ""
    email_address: str = ""


def get_user_info(lst: list, state: AssessorTaskList) -> dict:
    if lst is None:
        return []

    user_ids = {item.user_id for item in lst if item.user_id}

    if user_ids:
        current_app.logger.info("Retrieving account information")
        account_list = get_bulk_accounts_dict(
            list(user_ids),
            state.fund_short_name,
        )
        return account_list
    else:
        return []


def add_user_info(list_data: list, state) -> list:
    account_info = get_user_info(list_data, state)
    if list_data is None:
        return []

    for item in list_data:
        user_id = item.user_id

        if user_id in account_info:
            user_data = account_info[user_id]
            current_app.logger.info("Adding account information.")
            for key, value in user_data.items():
                setattr(item, key, value)
    return list_data


def order_by_dates(lst: list) -> tuple:
    """Sorts a list of items by 'date_created' in descending order"""

    return sorted(lst, key=lambda item: item.date_created, reverse=True)


class SearchForm(FlaskForm):
    search = StringField("Search")


class CheckboxForm(FlaskForm):
    all_activity = BooleanField("All activity", default=True)
    comments = BooleanField("Comments")
    assessment_status = BooleanField("Assessment status")
    score = BooleanField("Score")
    flag = BooleanField("Flags")
    tag = BooleanField("Tags")


def map_activities_classes_with_checkbox_filters(filters):
    filters = [f.replace(" ", "") for f in filters if f != "All activity"]
    _filters = []
    for filter in filters:
        if filter == "Score":
            _filters.append("Scores")
        if filter == "Tags":
            _filters.append("AssociatedTags")
        else:
            _filters.append(filter)

    return _filters


def filter_all_activities(all_activities: list, search_keyword: str = "", filters: list = None):
    all_activities = order_by_dates(all_activities)
    filtered_classes = map_activities_classes_with_checkbox_filters(filters)

    if not search_keyword and not filtered_classes:
        return all_activities

    if search_keyword and filtered_classes:
        return [
            activity
            for activity in all_activities
            if any(search_keyword.lower() in str(attr).lower() for attr in asdict(activity).values())
            and any(class_name.lower() == activity.__class__.__name__.lower() for class_name in filtered_classes)
        ]

    if not search_keyword and filters:
        return [
            activity
            for activity in all_activities
            if any(class_name.lower() == activity.__class__.__name__.lower() for class_name in filtered_classes)
        ]

    if search_keyword and not filtered_classes:
        return [
            activity
            for activity in all_activities
            if any(search_keyword.lower() in str(attr).lower() for attr in asdict(activity).values())
        ]

    else:
        return all_activities


def select_filters(is_expression_of_interest):
    if is_expression_of_interest:
        return ["All activity", "Comments", "Flags", "Tags"]
    else:
        return ["All activity", "Comments", "Score", "Flags", "Tags"]
