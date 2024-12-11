from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Tuple
from urllib.parse import quote

from bs4 import BeautifulSoup
from flask import url_for

from assess.assessments.form_lists_helper import map_form_json_list_value
from assess.services.aws import list_files_in_folder
from assess.shared.filters import format_address, format_date

ANSWER_NOT_PROVIDED_DEFAULT = "<p>Not provided.</p>"


@dataclass
class ApplicantResponseComponent(ABC):
    @property
    @abstractmethod
    def key(self):
        raise NotImplementedError(f"key not implemented for {self.__class__.__name__}")

    @property
    def should_render(self):
        return True


@dataclass
class QuestionHeading(ApplicantResponseComponent):
    question: str

    key = "question_heading"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(question=data["question"])


@dataclass
class QuestionAnswerPair(ApplicantResponseComponent, ABC):
    question: str
    answer: str | float

    @property
    def should_render(self):
        return True

    @classmethod
    def from_dict(cls, data: dict):
        answer = data.get("answer")
        return cls(
            question=data["question"],
            answer=answer if answer else ANSWER_NOT_PROVIDED_DEFAULT,
        )


class AboveQuestionAnswerPair(QuestionAnswerPair):
    key = "question_above_answer"


class AboveQuestionAnswerPairHtml(QuestionAnswerPair):
    key = "question_above_answer_html"


class BesideQuestionAnswerPair(QuestionAnswerPair):
    key = "question_beside_answer"


@dataclass
class QuestionAnswerPairHref(QuestionAnswerPair, ABC):
    answer_href: str

    @classmethod
    def from_dict(cls, data: dict, href):  # noqa
        answer = data.get("answer")
        return cls(
            question=data["question"],
            answer=answer if answer else ANSWER_NOT_PROVIDED_DEFAULT,
            answer_href=href if answer else None,
        )


class AboveQuestionAnswerPairHref(QuestionAnswerPairHref):
    key = "question_above_href_answer"


class BesideQuestionAnswerPairHref(QuestionAnswerPairHref):
    key = "question_beside_href_answer"


@dataclass
class FormattedBesideQuestionAnswerPair(QuestionAnswerPair):
    formatter: callable

    key = "question_beside_with_formatted_answer"

    @classmethod
    def from_dict(cls, data: dict, formatter: callable):  # noqa
        return cls(
            question=data["question"],
            answer=(data.get("answer") if data.get("answer") else ANSWER_NOT_PROVIDED_DEFAULT),
            formatter=formatter if data.get("answer") else lambda x: x,
        )


@dataclass
class MonetaryKeyValues(ApplicantResponseComponent):
    caption: str
    column_description: str
    question_answer_pairs: List[Tuple[str, float]]
    total: float

    key = "monetary_key_values"

    @classmethod
    def from_dict(cls, data: dict):
        caption, question = data["question"]

        if "answer" not in data or not data["answer"]:
            return AboveQuestionAnswerPair(
                question=question,
                answer=ANSWER_NOT_PROVIDED_DEFAULT,
            )

        return cls(
            caption=caption,  # sometimes not present
            column_description=question,
            question_answer_pairs=[(desc, float(amt)) for desc, amt in data["answer"]],
            total=sum([float(amt) for _, amt in data["answer"]]),
        )


@dataclass
class QuestionAboveHrefAnswerList(ApplicantResponseComponent):
    question: str
    key_to_url_dict: dict[str, str]

    key = "question_above_href_answer_list"

    @classmethod
    def from_dict(cls, data: dict, key_to_url_dict: dict[str, str]):
        return cls(
            question=data["question"],
            key_to_url_dict=key_to_url_dict,
        )


@dataclass
class NewAddAnotherTable(ApplicantResponseComponent):
    caption: str
    head: List[dict[str, str]]
    rows: List[dict[str, str]]

    key = "new_add_another_table"

    @classmethod
    def from_dict(cls, data: dict):
        answer = data.get("answer")

        totals, headings = [], []
        for column_name, values, fmt in answer:
            if fmt == "currency":
                column_format = "numeric"
                totals.append(sum([float(val) for val in values]))
            else:
                column_format = ""
                totals.append(None)
            headings.append({"text": column_name, "format": column_format})

        rows = []
        num_columns = len(answer[0][1])  # Assuming all rows have the same number of values
        for j in range(num_columns):
            columns = []
            for _i, (_, values, fmt) in enumerate(answer):
                render_type = "html" if fmt == "html" else "text"
                render_val = values[j]
                format_val = ""

                if fmt == "currency":
                    render_val = f"£{render_val:.2f}"
                    format_val = "numeric"

                columns.append({render_type: render_val, "format": format_val})
            rows.append(columns)

        if any(totals):
            rows.append(
                [{"text": "Total", "classes": "govuk-table__header"}]
                + [
                    {
                        "text": f"£{val:.2f}" if val else "",
                        "format": "numeric" if val else "",
                    }
                    for val in totals[1:]
                ]  # we assume the first column is a string
            )

        return cls(
            caption=data["question"],
            head=headings,
            rows=rows,
        )


def _convert_to_month_year(input_date):
    """Convert input date string from MM-YYYY/YYYY-MM to Month Year
    Example converts (06-2023, 2023-06..) to June 2023."""
    try:
        date_object = datetime.strptime(input_date, "%Y-%m")
    except ValueError:
        date_object = datetime.strptime(input_date, "%m-%Y")
    date_object.strftime("%B %Y")
    return str(date_object.strftime("%B %Y"))


def _ui_component_from_factory(item: dict, application_id: str):  # noqa: C901
    """
    :param item: dict
    A dictionary representing the UI component to create. It must contain the following keys:
    - presentation_type (str): The type of presentation for the UI component. Can be one
      of the following values:
        - "grouped_fields": A group of related key-value pairs, used for financial tables.
        - "question_heading": A heading for a group of related questions.
        - "text": A simple text field.
        - "list": A list of items. (?)
        - "file": A file field.
        - "address": An address field.
    - field_type (str): The type of field for the UI component.
      Can be one of the following values:
        - "multilineTextField": A multi-line text field.
        - "websiteField": A website field.
        - "datePartsField": A date field.
        - "emailAddressField": An email address field.
        - "telephoneNumberField": A telephone number field.
        - answer (str): The answer for the UI component.

    :return (ApplicantResponseComponent): An instance of the UI component class.
    An instance of a subclass of UIComponent, representing the UI component for the given item.
    """
    presentation_type = item["presentation_type"]
    field_type = item.get("field_type")
    answer = item.get("answer")

    if answer and field_type in ("numberField",):
        if presentation_type not in ("grouped_fields",):
            item["answer"] = float(item["answer"])

    # TODO : Handle "monthYearField" field convertion in a better way if exists in "multiInputField"
    # Convert input date string from MM-YYYY/YYYY-MM to Month Year format (eg., 2023-06 to June 2023)
    if (answer and field_type == "monthYearField" and presentation_type == "text") or (
        answer and field_type == "multiInputField" and isinstance(answer, list)
    ):
        if isinstance(answer, list):
            try:
                for i, ans in enumerate(answer):
                    if ans[2] == "monthYearField":
                        for j, val in enumerate(ans[1]):
                            input_date = val
                            item["answer"][i][1][j] = _convert_to_month_year(input_date)
            except IndexError:
                pass
        else:
            item["answer"] = _convert_to_month_year(answer)

    if item.get("branched_field"):
        # In the case of the same question asked in two places (but with differing fields ids)
        # for example when asked in multiple paths within a form (branched_fields),
        # we specify the multiple field_id's ids in a grouping to pick up each possible form branch
        # we should only get one answer here so extract the first and only answer
        item["answer"] = item["answer"][0][1] if "answer" in item else None
        # currently only currencies, so we foramt, but we should add a formatter or some
        # configuration open to change it
        item["presentation_type"] = "currency"
        item["question"] = item["question"][0]
        presentation_type = "currency"

    if presentation_type == "grouped_fields":
        return MonetaryKeyValues.from_dict(item)

    elif presentation_type == "question_heading":
        return QuestionHeading.from_dict(item)

    elif presentation_type == "free_text":
        item = sanitise_html(item)
        return AboveQuestionAnswerPairHtml.from_dict(item)

    elif presentation_type == "table":
        if not item.get("answer"):
            return BesideQuestionAnswerPair(
                question=item["question"],
                answer=ANSWER_NOT_PROVIDED_DEFAULT,
            )

        return NewAddAnotherTable.from_dict(item)

    elif presentation_type == "currency":
        if item.get("answer") is not None and item.get("answer") != "":
            item["answer"] = "£{:.2f}".format(float(item["answer"]))
        return BesideQuestionAnswerPair.from_dict(item)

    elif presentation_type == "integer":
        if item.get("answer"):
            item["answer"] = "{}".format(int(item["answer"]))
        return BesideQuestionAnswerPair.from_dict(item)

    elif presentation_type in ("text", "list", "free_text"):
        if field_type in ("radiosField") and item.get("answer"):
            item["answer"] = map_form_json_list_value(item["answer"])
        if field_type in ("multilineTextField",):
            return AboveQuestionAnswerPair.from_dict(item)
        elif field_type in ("websiteField",):
            return BesideQuestionAnswerPairHref.from_dict(item, href=answer)
        elif field_type in ("datePartsField",):
            return FormattedBesideQuestionAnswerPair.from_dict(
                item,
                formatter=lambda x: format_date(x, from_="%Y-%m-%d", to_="%d %B %Y"),
            )
        elif field_type in ("emailAddressField",):
            return BesideQuestionAnswerPairHref.from_dict(item, href=f"mailto:{answer}")
        elif field_type in ("telephoneNumberField",):
            return BesideQuestionAnswerPairHref.from_dict(item, href=f"tel:{answer}")
        else:
            return BesideQuestionAnswerPair.from_dict(item)

    elif presentation_type == "file":
        presigned_url = url_for(
            "assessment_bp.get_file",
            application_id=application_id,
            file_name=answer if answer else "",
        )
        return AboveQuestionAnswerPairHref.from_dict(item, href=presigned_url)

    elif presentation_type == "s3bucketPath":
        folder_path = f"{application_id}/{item['form_name']}/{item['path']}/{item['field_id']}"
        file_keys = list_files_in_folder(folder_path) if answer else []
        key_to_url_dict = {
            key: url_for(
                "assessment_bp.get_file",
                application_id=application_id,
                file_name=quote(key, safe=""),
                quoted=True,
            )
            for key in file_keys
        }
        return QuestionAboveHrefAnswerList.from_dict(item, key_to_url_dict)

    elif presentation_type == "address":
        return FormattedBesideQuestionAnswerPair.from_dict(item, format_address)

    # Note that types "amount", "description" and "heading" are not used
    # here because they are grouped together in the "grouped_fields" type
    # in a pre-processing step
    raise NotImplementedError(f"Unknown presentation type: {presentation_type} for item: {item}")


def _convert_heading_description_amount(
    response: Iterable[dict],
) -> tuple[list[dict], set[str]]:
    """Convert a list of dictionaries representing a response question and
    answers into a tuple of a list of dictionaries representing grouped fields
    and a set of field IDs.

    :argument response: A list of dictionaries representing a response from
         the assessment store to questions and answers.

    :return (tuple[list[dict], set[str]]): A tuple of a list of dictionaries
    - A tuple of a list of dictionaries representing grouped fields and a set
      of field IDs.
    """
    field_ids = [
        item["field_id"] for item in response if item["presentation_type"] == "heading"
    ]  # gather field ids for headings with a presentation type of "heading"

    items = []
    for index, field_id in enumerate(field_ids):
        # gather all items with the same field id, we expect one of each type
        # "heading", "description" and "amount", if a field is missing we
        # raise an exception noting the incorrect configuration
        heading = _get_item_by_presentation_type_index(response, "heading", index)
        description = _get_item_by_presentation_type_index(response, "description", index)
        amount = _get_item_by_presentation_type_index(response, "amount", index)

        # if we dont have an answer, we add a default text element which
        # will eventually show "not provided" on the user interface
        if "answer" not in description or "answer" not in amount:
            items.append(_build_item(heading["question"], field_id))
            continue

        # assigning these keys to variables so it's clearer what they represent
        descriptions, amounts = description["answer"], amount["answer"]

        # remove any pound signs from the amounts, so we can convert them to floats
        poundless_amounts = [a.replace("£", "") for a in amounts]

        # convert the descriptions and amounts to the structure of a grouped field
        grouped_fields = list(zip(descriptions, map(float, poundless_amounts), strict=False))

        items.append(
            {
                "question": (heading["question"], description["question"]),
                "field_id": field_id,
                "answer": grouped_fields,
                "presentation_type": "grouped_fields",
            }
        )
    return items, set(field_ids)


def _build_item(
    question: str,
    field_id: str,
    presentation_type: str = "text",
) -> dict:
    return {
        "question": question,
        "field_type": "text",
        "field_id": field_id,
        "presentation_type": presentation_type,
    }


def _get_item_by_presentation_type_index(response: list[dict], presentation_type: str, index: int) -> dict:
    """Gets an item from a response dictionary based on its presentation type
    and index.

    Parameters:
    response (dict): The response dictionary to search in.
    presentation_type (str): The presentation type of the item to search for.
    index (int): The index of the item with the specified presentation type.

    :return (dict): The item with the specified presentation type and index.

    :raises ValueError: If the item with the specified presentation type and index
    """
    try:
        return next(
            item
            for idx, item in enumerate((item for item in response if item["presentation_type"] == presentation_type))
            if idx == index
        )
    except StopIteration as e:
        raise ValueError(
            "Could not find item with presentation_type:"
            f" {presentation_type} at index: {index}\nThis probably means"
            " there is an uneven number of 'heading', 'description' and"
            " 'amount' items\nThere should be an equal number of each of"
            " these items"
        ) from e


def _convert_checkbox_items(
    response: Iterable[dict],
) -> tuple[list[dict], set[str]]:
    """Convert checkbox items in the response into a tuple of a list of dictionary
    items and a set of field IDs.

    The list of dictionary items includes a question heading for the checkbox field,
    and a dictionary item for each selected checkbox option with the label of the
    selected option and the value "Yes". If no checkboxes are selected, a single
    dictionary item with the question heading is added to the list with the value
    "None selected."

    :argument response: A list of dictionaries representing a response from the
    assessment store to questions and answers.

    :return (tuple[list[dict], set[str]]): A tuple of a list of dictionary items
    and a set of field IDs.
    """
    checkbox_field_ids = {item["field_id"] for item in response if item["field_type"] == "checkboxesField"}
    checkbox_items = (i for i in response if i["field_id"] in checkbox_field_ids)

    text_items = []
    for item in checkbox_items:
        text_item = _build_item(
            item["question"],
            item["field_id"],
            "question_heading",
        )

        if len(item.get("answer", [])) == 0:  # if no checkboxes are selected
            text_item["presentation_type"] = "text"
            text_item["answer"] = "None selected."
            text_items.append(text_item)
            continue

        text_items.append(text_item)
        text_items.extend(
            {
                "question": map_form_json_list_value(answer),
                "field_type": item.get("field_type"),
                "field_id": item["field_id"],
                "answer": "Yes",
                "presentation_type": "text",
            }
            for answer in item["answer"]
        )

    return text_items, checkbox_field_ids


def _flatten_field_ids(field_id: str | tuple | list) -> list[str]:
    """Flatten a tuple or list of field IDs into a list of individual field
    IDs.

    :argument field_id: A tuple or list of field IDs.

    :return (list[str]): A list of individual field IDs.
    """
    field_ids = []
    if isinstance(field_id, (tuple, list)):
        field_ids.append(tuple(field_id))
        for fid in field_id:
            field_ids.append(fid)
    else:
        field_ids.append(field_id)
    return field_ids


def _convert_non_number_grouped_fields(
    response: Iterable[dict],
) -> tuple[list[dict], set[str]]:
    """This function takes a response, an iterable of dictionaries representing data
    fields, and returns a tuple containing a list of dictionaries representing
    individual text items and a set of field IDs that have been processed. The
    dictionaries in the list contain data for a single text field.

    - response (list[dict]): A list of dictionaries representing a response, the dict
    keys are:
        - "question": a string representing the question for the field
        - "field_type": a string representing the type of field, if applicable
        - "field_id": a string or list of strings representing the field ID(s)
        - "answer": a string representing the answer for the field
        - "presentation_type": a string set to "text"
    The input response should be an iterable of dictionaries with the following keys:

    - "presentation_type": a string representing the type of data field, which should
    be "grouped_fields" for the fields that this function processes
    - "field_type": a string representing the type of field, which should not be
    - "numberField" for the fields that this function processes
    - "question": a list of strings representing the questions for the fields
    - "field_id": a list of strings or lists of strings representing the field IDs for
    the fields
    - "answer": a list of tuples, where each tuple contains a string representing the
    question for the field and a string representing the answer for the field

    :argument response: An iterable of dictionaries representing data fields.

    :return (tuple[list[dict], set[str]]): A tuple containing a list of dictionaries
    representing individual text items and a set of field IDs that have been
    processed.
    """
    items_to_process = [
        item
        for item in response
        if item["presentation_type"] == "grouped_fields" and item["field_type"] != "numberField"
        # we ignore number fields as they are handled separately # noqa
    ]

    text_items = []
    for item in items_to_process:
        if "answer" not in item or len(item.get("answer", [])) == 0:
            text_items.append(_build_item(item["question"][0], item["field_id"]))
            continue

        for question_answer_tuple, field_id in zip(item["answer"], item["field_id"], strict=False):
            question, answer = question_answer_tuple
            text_items.append(
                {
                    "question": question,
                    "field_type": item.get("field_type"),
                    "field_id": field_id,
                    "answer": answer,
                    "presentation_type": "text",
                }
            )

    processed_field_ids = set()
    for item in items_to_process:
        processed_field_ids.update(_flatten_field_ids(item["field_id"]))

    return text_items, processed_field_ids


def _make_field_ids_hashable(item: dict) -> dict:
    field_id = item["field_id"]
    if isinstance(field_id, list):
        item["field_id"] = tuple(field_id)
    return item


def create_ui_components(
    response_with_some_unhashable_fields: list[dict], application_id: str
) -> List[ApplicantResponseComponent]:
    """Creates UI components for displaying applicant responses.

    This function takes a list of dictionaries representing applicant responses
    with some un-hashable fields and returns a list of ApplicantResponseComponent
    objects. The un-hashable fields are first made hashable by calling
    _make_field_ids_hashable. Then, the response is processed and grouped into
    different categories: heading and description with amounts, checkbox items
    and non-number grouped fields. These categories are then converted into their
    respective UI components and added to a list of post-processed items. The
    list of post-processed items is sorted based on the original order of the fields
    in the response and returned as a list of ApplicantResponseComponent objects.

    :argument response_with_some_unhashable_fields: A list of dictionaries

    :return (list[ApplicantResponseComponent]): A list of ApplicantResponseComponent objects
    """
    response = list(map(_make_field_ids_hashable, response_with_some_unhashable_fields))

    grouped_fields_items, gfi_field_ids = _convert_heading_description_amount(response)
    text_items_from_checkbox, tifc_field_ids = _convert_checkbox_items(response)
    (
        text_items_from_grouped_fields,
        tifgf_field_ids,
    ) = _convert_non_number_grouped_fields(response)

    processed_field_ids = gfi_field_ids | tifc_field_ids | tifgf_field_ids
    unprocessed_items = [i for i in response if i["field_id"] not in processed_field_ids]
    post_processed_items = (
        grouped_fields_items + text_items_from_checkbox + text_items_from_grouped_fields + unprocessed_items
    )

    field_ids_in_order = []
    for i in response:
        field_ids_in_order.extend(_flatten_field_ids(i["field_id"]))

    # we need to preserve the order of the fields from the back-end,
    # so we re-sort it here
    post_processed_items.sort(key=lambda x: field_ids_in_order.index(x["field_id"]))

    return [_ui_component_from_factory(item, application_id) for item in post_processed_items]


def sanitise_html(data):
    """
    Sanitizes the HTML content in the 'answer' key of the input 'data' dictionary.

    This function takes an input dictionary containing an 'answer' key with HTML content.
    It uses BeautifulSoup to parse the HTML and modifies specific elements.

    Parameters:
        data (dict): A dictionary containing an 'answer' key with HTML content.

    Returns:
        dict: A modified dictionary with the 'answer' key containing the govuk class and custom class.
    """

    answer = data.get("answer")
    if answer:
        soup = BeautifulSoup(answer, "html.parser")

        for tag in soup.find_all(["p", "ul", "ol"]):
            if tag.name == "p":
                tag["class"] = "govuk-body"
            if tag.name == "ul" or tag.name == "ol":
                if style_type := tag.get("style"):
                    style_type = style_type.replace("list-style-type:", "").strip(";").strip()
                    tag["class"] = f"list-type-{style_type}"
                else:
                    if tag.name == "ul":
                        tag["class"] = "govuk-list govuk-list--bullet"

                    if tag.name == "ol":
                        tag["class"] = "govuk-list govuk-list--number"

        data["answer"] = str(soup)
    return data


def create_ui_componenets_for_list_data(application_id: str, mapped_appli_with_sub_cri: list):
    answers_mapped = []
    for data in mapped_appli_with_sub_cri:
        _data = []
        view_entire_appli_config = {}
        for d in data:
            if "display_id" in d and d.get("display_id") == "view_entire_application":
                view_entire_appli_config.update(d)
                continue
            else:
                _data.append(d)

        answers_meta = create_ui_components(_data, application_id)
        subcri_and_theme = ConvertDictToClass(**view_entire_appli_config)

        # combine class of view entire application config
        answers_mapped.append(answers_meta + [subcri_and_theme])

    return answers_mapped


class ConvertDictToClass:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attributes = ", ".join([f"{key}={value!r}" for key, value in self.__dict__.items()])

        return f"{type(self).__name__}({attributes})"
