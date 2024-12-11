from unittest.mock import Mock

import pytest

from assess.themes.deprecated_theme_mapper import (
    deprecated_sort_add_another_component_contents,
    format_add_another_component_contents,
)


@pytest.mark.parametrize(
    "answer_from_form_runner, expected_description, expected_amount",
    [
        (
            ["An Answer : £1"],
            ["An Answer "],
            ["£1"],
        ),
        (
            ["An Answer : with colon : £1"],
            ["An Answer : with colon "],
            ["£1"],
        ),
        (
            ["An : Answer : with : lots: of :colons : £1"],
            ["An : Answer : with : lots: of :colons "],
            ["£1"],
        ),
        (
            ["An Answer : £1", "Another Answer : £2"],
            ["An Answer ", "Another Answer "],
            ["£1", "£2"],
        ),
    ],
)
def test_deprecated_sort_add_another_component_contents(
    answer_from_form_runner, expected_description, expected_amount, app
):
    themes_answers = [
        {
            "presentation_type": "heading",
            "question": "Test Heading",
            "field_id": "123",
            "answer": "Test Heading",
        },
        {
            "presentation_type": "description",
            "question": "Test Description",
            "field_id": "123",
            "answer": answer_from_form_runner,
        },
        {
            "presentation_type": "amount",
            "question": "Test Amount",
            "field_id": "123",
            "answer": answer_from_form_runner,
        },
    ]

    deprecated_sort_add_another_component_contents(themes_answers)

    assert themes_answers[0]["answer"] == "Test Heading"
    assert themes_answers[1]["answer"] == expected_description
    assert themes_answers[2]["answer"] == expected_amount


@pytest.mark.parametrize(
    "pre_question, post_question, answer_from_form_runner, expected_nested_table_tuple",
    [
        (
            [  # pre_question
                "Question title",
                {
                    "aaaaaa": {
                        "column_title": "Example text child",
                        "type": "textField",
                    },
                    "bbbbbb": {
                        "column_title": "Example currency child",
                        "type": "numberField",
                    },
                    "cccccc": {
                        "column_title": "Example month year child",
                        "type": "MonthYearField",
                    },
                    "dddddd": {
                        "column_title": "Example yes no child",
                        "type": "yesNoField",
                    },
                    "eeeeee": {
                        "column_title": "Example radio child",
                        "type": "RadioField",
                    },
                    "ffffff": {
                        "column_title": "Example multiline text child",
                        "type": "multilineTextField",
                    },
                    "gggggg": {
                        "column_title": "Example month year child 2",
                        "type": "MonthYearField",
                    },
                    "hhhhhh": {
                        "column_title": "Example uk address child",
                        "type": "ukAddressField",
                    },
                },
            ],
            "Question title",  # post_question
            [  # answer_from_form_runner
                {
                    "aaaaaa": "test1",
                    "bbbbbb": 1,
                    "cccccc": {"cccccc__month": "01", "cccccc__year": "2020"},
                    "dddddd": True,
                    "eeeeee": "low",
                    "ffffff": "test\r\n1",
                    "gggggg": {"gggggg__month": "01", "gggggg__year": "2021"},
                    "hhhhhh": {
                        "addressLine1": "address line 1",
                        "addressLine2": "",
                        "county": "",
                        "postcode": "te4 2nf",
                        "town": "test",
                    },
                },
                {
                    "aaaaaa": "test2",
                    "bbbbbb": 2,
                    "cccccc": {"cccccc__month": "02", "cccccc__year": "2020"},
                    "dddddd": False,
                    "eeeeee": "high",
                    "ffffff": "test\r\n2",
                    "gggggg": {"gggggg__month": "05", "gggggg__year": "2021"},
                    "hhhhhh": "test, null, te3 2nf, null, te4 2nf",
                },
            ],
            [  # expected_nested_table_tuple
                ["Example text child", ["test1", "test2"], "text"],
                ["Example currency child", [1, 2], "currency"],
                [
                    "Example month year child",
                    ["01-2020", "02-2020"],
                    "monthYearField",
                ],
                ["Example yes no child", ["Yes", "No"], "text"],
                ["Example radio child", ["Low", "High"], "text"],
                [
                    "Example multiline text child",
                    ["test\r\n1", "test\r\n2"],
                    "html",
                ],
                [
                    "Example month year child 2",
                    ["01-2021", "05-2021"],
                    "monthYearField",
                ],
                [
                    "Example uk address child",
                    [
                        "address line 1, te4 2nf, test",
                        "test, null, te3 2nf, null, te4 2nf",
                    ],
                    "text",
                ],
            ],
        ),
    ],
)
def test_format_add_another_component_contents(
    pre_question,
    post_question,
    answer_from_form_runner,
    expected_nested_table_tuple,
    app,
):
    themes_answer = {
        "field_id": "NdFwgy",
        "field_type": "multiInputField",
        "presentation_type": "table",
        "question": pre_question,
        "answer": answer_from_form_runner,
    }

    (theme_answer,) = format_add_another_component_contents([themes_answer])

    assert theme_answer["question"] == post_question
    assert theme_answer["answer"] == expected_nested_table_tuple


def test_deprecated_sort_add_another_component_contents_log_when_no_answer(
    monkeypatch,
):
    current_app = Mock()
    monkeypatch.setattr("assess.themes.deprecated_theme_mapper.current_app", current_app)

    themes_answers = [
        {
            "presentation_type": "heading",
            "question": "Test Heading",
            "field_id": "123",
        },
        {
            "presentation_type": "description",
            "question": "Test Description",
            "field_id": "123",
        },
        {
            "presentation_type": "amount",
            "question": "Test Amount",
            "field_id": "123",
        },
    ]

    deprecated_sort_add_another_component_contents(themes_answers)

    current_app.logger.debug.assert_called_with(
        "Answer not provided for field_id: {field_id}", extra=dict(field_id="123")
    )
