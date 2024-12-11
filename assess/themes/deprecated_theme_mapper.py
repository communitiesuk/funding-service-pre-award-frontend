from collections import defaultdict
from typing import Any

from flask import current_app

from assess.config.themes_mapping import ordered_themes


# This code was copied directly from the assessments store in an attempt to consolidate all the transformation logic
# in one place. The goal of putting all the transformation logic in one place is so that we can eventually refactor
# it to be less complex and more simplified. There's a lot of complicated nuance that realistically doesn't need to
# exist, so this is the first step in removing it. Therefore, all the code that you see below is copied directly from
# assessments store and not uniquely written at the time of this commit.
def map_application_with_sub_criteria_themes_fields(
    application_json,
    sub_criterias,
    theme_id: str,
):
    questions = [questions for forms in application_json["jsonb_blob"]["forms"] for questions in forms["questions"]]
    themes_fields = get_themes_fields(
        sub_criterias,
        theme_id,
    )
    for theme in themes_fields:
        try:
            if isinstance(theme["field_id"], list):
                map_grouped_fields_answers(theme, questions)
            else:
                map_single_field_answer(theme, questions)
        except TypeError:
            current_app.logger.error("Incorrect theme id -> {theme_id}", extra=dict(theme_id=theme_id))
            return f"Incorrect theme id -> {theme_id}"

    convert_boolean_values(themes_fields)

    # Does not sort on the new version of add-another simply pass the object through for display by assessment frontend
    # the old version of add-another which was not scalable and did not allow the adding of N* fields
    deprecated_sort_add_another_component_contents(themes_fields)

    return format_add_another_component_contents(themes_fields)


def map_application_with_sub_criterias_and_themes(
    application_json,
    sub_criterias,
    theme_ids: list,
):
    mapped_appli_with_sub_cri = []
    for theme_id in theme_ids:
        _sub_cri_with_theme_id = map_sub_cri_with_theme_id(sub_criterias, theme_id)

        map_data = map_application_with_sub_criteria_themes_fields(application_json, sub_criterias, theme_id)

        sub_and_theme = {**_sub_cri_with_theme_id}

        # add sub criteria and theme id to the current data
        _map_data = map_data + [sub_and_theme]
        mapped_appli_with_sub_cri.append(_map_data)

    return mapped_appli_with_sub_cri


def map_sub_cri_with_theme_id(sub_criterias, theme_id):
    """Function returns mapped theme_id with sub criteria including
    view_entire_application config display_id"""
    for sub_criteria in sub_criterias:
        for theme in sub_criteria["themes"]:
            if theme_id == theme.get("id"):
                _theme_id = theme["id"].replace("_", " ").replace("-", " ").capitalize()

                view_entire_application_config = {
                    "display_id": "view_entire_application",
                    "sub_criteria": sub_criteria["name"],
                    "theme_id": _theme_id,
                }
                return view_entire_application_config


def get_themes_fields(sub_criterias, theme_id) -> str | Any:
    if theme_id == "all_uploaded_documents":
        return [
            {
                **answer,
                "question": f"{theme['name']}, {answer['question']}",
                "form_name": answer["form_name"],
            }
            for item in sub_criterias
            for theme in item["themes"]
            for answer in theme["answers"]
            if answer["field_type"] in ["clientSideFileUploadField", "fileUploadField"]
        ]
    else:
        try:
            return [
                theme.get("answers")
                for themes in sub_criterias
                for theme in themes.get("themes")
                if theme_id == theme.get("id")
            ][0]
        except IndexError:
            current_app.logger.error("Incorrect theme id -> {theme_id}", extra=dict(theme_id=theme_id))
            return f"Incorrect theme id -> {theme_id}"


def map_grouped_fields_answers(theme, questions):
    for question in questions:
        answer_list = tuple(
            (
                (app["title"], app["answer"])
                for app in question["fields"]
                for field_id in theme["field_id"]
                if "answer" in app.keys() and app["key"] == field_id
            )
        )
        if answer_list:
            theme["answer"] = answer_list


def map_single_field_answer(theme, questions):
    for question in questions:
        for app_fields in question["fields"]:
            if theme["field_id"] == app_fields["key"] and "answer" in app_fields.keys():
                # Some fields are optional so will have no answers
                theme["answer"] = app_fields.get("answer", None)


def convert_boolean_values(themes_fields) -> None:
    current_app.logger.info("Converting boolean values to strings")
    for field in themes_fields:
        if "answer" not in field.keys():
            continue
        elif field["answer"] is False:
            field.update(answer="No")
        elif field["answer"] is True:
            field.update(answer="Yes")


# supports the old version of add-another which was
# not scalable and did not allow the adding of N* fields
def deprecated_sort_add_another_component_contents(
    themes_fields: list[dict],
) -> None:
    for field in themes_fields:
        try:
            if field["presentation_type"] != "heading":
                continue

            field["answer"] = field["question"]
            for theme in themes_fields:
                if field["field_id"] not in theme.values():
                    continue

                if theme["presentation_type"] == "description":
                    description_answer = [description.rsplit(": ", 1)[0] for description in theme["answer"]]
                    theme["answer"] = description_answer

                if theme["presentation_type"] == "amount":
                    amount_answer = [amount.rsplit(": ", 1)[1] for amount in theme["answer"]]
                    theme["answer"] = amount_answer
        except (KeyError, IndexError):
            current_app.logger.debug(
                "Answer not provided for field_id: {field_id}", extra=dict(field_id=field["field_id"])
            )


def format_add_another_component_contents(  # noqa: C901
    themes_fields: list[dict],
) -> list[dict]:
    for field in themes_fields:
        if field.get("presentation_type") != "table":
            continue

        title, table_config = field["question"]
        field["question"] = title

        component_id_to_answer_list = {}
        # In some cases (optional or path based questions) there is no answer provided
        for answer_container in field.get("answer", []):
            for component_id, answer in answer_container.items():
                if component_id not in component_id_to_answer_list:
                    component_id_to_answer_list[component_id] = []
                component_id_to_answer_list[component_id].append(answer)

        table = []
        for component_id, column_config in table_config.items():
            frontend_format = None
            title = column_config["column_title"]
            answers = component_id_to_answer_list.get(component_id)

            # match the field type without case sensitivity
            for key, value in _MULTI_INPUT_FORMAT_FRONTEND.items():
                if key.lower() == column_config["type"].lower():
                    frontend_format = value
                    break
            if frontend_format is None:
                frontend_format = "text"

            pre_frontend_formatter = _MULTI_INPUT_FRE_FRONTEND_FORMATTERS.get(column_config["type"], lambda x: x)

            formatted_answers = (
                [
                    (
                        "Not provided."  # default value, if None or empty string provided
                        if (answer is None or answer == "")
                        else pre_frontend_formatter(answer)
                    )
                    for answer in answers
                ]
                if answers
                else None
            )

            if frontend_format == "monthYearField":
                formatted_answers = (
                    [f"{answer[component_id + '__month']}-{answer[component_id + '__year']}" for answer in answers]
                    if answers
                    else None
                )

            # Manualy extract `ukAddressField` as text if rendered as dict
            if column_config["type"] == "ukAddressField" and formatted_answers:
                for ind, answer in enumerate(formatted_answers):
                    if isinstance(answer, dict):
                        try:
                            formatted_answers[ind] = (
                                answer["addressLine1"]
                                + ", "
                                + answer.get("addressLine2", "")
                                + ", "
                                + answer["postcode"]
                                + ", "
                                + answer.get("county")
                                + ", "
                                + answer["town"]
                            ).replace(" ,", "")
                        except Exception:
                            formatted_answers[ind] = ", ".join(list(filter(None, answer.values())))

            if formatted_answers:
                table.append([title, formatted_answers, frontend_format])
        field["answer"] = table

    return themes_fields


# All in use children of multiInputField in cofr3/nstfr2
# If we use or add new children, we may need to add support
_MULTI_INPUT_FORMAT_FRONTEND = defaultdict(
    lambda: "text",
    {
        "numberField": "currency",
        "multilineTextField": "html",
        # the default should handle these, but let's be explicit
        "RadioField": "text",
        "textField": "text",
        "MonthYearField": "monthYearField",
        "yesNoField": "text",
    },
)

_MULTI_INPUT_FRE_FRONTEND_FORMATTERS = {
    "RadioField": lambda x: x.capitalize(),
    "yesNoField": lambda x: "Yes" if bool(x) else "No",
}


def order_entire_application_by_themes(fund_round_name, sub_criteria):
    _ordered_themes = []

    # Consider relocating the theme ordering logic to a utility function in 'utils'
    ordered_theme = ordered_themes(fund_round_name)

    for ordered_theme_id in ordered_theme:
        if ordered_theme_id:
            ordered_theme_id = ordered_theme_id.replace("-", " ").replace("_", " ").capitalize()
            for sub in sub_criteria:
                for theme_id in sub:
                    if theme_id.get("theme_id"):
                        _theme_id = theme_id["theme_id"]

                        if fund_round_name in [
                            "COFR4W2",
                            "COFR4W1",
                            "COFR3W2",
                            "COFR3W3",
                            "COFR2W3",
                            "COFR2W2",
                        ]:
                            if _theme_id == "Risk loss impact":
                                theme_id["theme_id"] = "Risk and impact of loss"
                            if _theme_id == "General info":
                                theme_id["theme_id"] = "General information"
                        if fund_round_name in ["COFR4W1", "COFR4W2"]:
                            if _theme_id == "Community use":
                                theme_id["theme_id"] = "Community use/significance"

                        if _theme_id == ordered_theme_id:
                            _ordered_themes.append(sub)
                            break
    return _ordered_themes
