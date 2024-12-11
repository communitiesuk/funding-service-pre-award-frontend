import json  # noqa

import pytest  # noqa
from flask import Flask

import assess
from assess.assessments.models.applicants_response import (
    ANSWER_NOT_PROVIDED_DEFAULT,
)
from assess.assessments.models.applicants_response import (
    AboveQuestionAnswerPair,
)
from assess.assessments.models.applicants_response import (
    AboveQuestionAnswerPairHref,
)
from assess.assessments.models.applicants_response import (
    ApplicantResponseComponent,
)
from assess.assessments.models.applicants_response import (
    BesideQuestionAnswerPair,
)
from assess.assessments.models.applicants_response import (
    BesideQuestionAnswerPairHref,
)
from assess.assessments.models.applicants_response import (
    FormattedBesideQuestionAnswerPair,
)
from assess.assessments.models.applicants_response import MonetaryKeyValues
from assess.assessments.models.applicants_response import NewAddAnotherTable
from assess.assessments.models.applicants_response import (
    QuestionAboveHrefAnswerList,
)
from assess.assessments.models.applicants_response import QuestionHeading
from assess.assessments.models.applicants_response import (
    _convert_checkbox_items,
)
from assess.assessments.models.applicants_response import (
    _convert_heading_description_amount,
)
from assess.assessments.models.applicants_response import (
    _convert_non_number_grouped_fields,
)
from assess.assessments.models.applicants_response import _flatten_field_ids
from assess.assessments.models.applicants_response import (
    _make_field_ids_hashable,
)
from assess.assessments.models.applicants_response import (
    _ui_component_from_factory,
)
from assess.assessments.models.applicants_response import create_ui_components
from assess.assessments.models.applicants_response import sanitise_html
from assess.assessments.routes import assessment_bp
from assess.shared.filters import format_address
from tests.assess_tests.api_data.test_data import TestSanitiseData


class TestApplicantResponseComponentConcreteSubclasses:
    def test_monetary_key_values_should_render(self):
        data = {
            "question": ("Test caption", "Test question"),
            "answer": [
                ("Test description 1", 10.0),
                ("Test description 2", 20.0),
            ],
        }
        key_values = MonetaryKeyValues.from_dict(data)
        assert key_values.caption == "Test caption"
        assert key_values.column_description == "Test question"
        assert key_values.question_answer_pairs == [
            ("Test description 1", 10.0),
            ("Test description 2", 20.0),
        ]
        assert key_values.should_render is True

    @pytest.mark.parametrize(
        "mkv_data",
        [
            {"question": ("Test caption", "Test question"), "answer": []},
            {"question": ("Test caption", "Test question"), "answer": None},
            {"question": ("Test caption", "Test question")},
        ],
    )
    def test_monetary_key_values_should_default_to_not_provided(self, mkv_data):
        above_qa_pair = MonetaryKeyValues.from_dict(mkv_data)

        assert isinstance(above_qa_pair, AboveQuestionAnswerPair)
        assert above_qa_pair.question == "Test question"
        assert above_qa_pair.answer == ANSWER_NOT_PROVIDED_DEFAULT

    @pytest.mark.parametrize(
        "new_add_another_data",
        [
            {
                "question": "Test caption",
                "answer": [
                    ["Example text child", ["test1", "test2"], "text"],
                    ["Example currency child", [1, 2], "currency"],
                    [
                        "Example month year child",
                        ["2020-01", "2020-02"],
                        "text",
                    ],
                    ["Example yes no child", ["Yes", "No"], "text"],
                    ["Example radio child", ["Low", "High"], "text"],
                    [
                        "Example multiline text child",
                        ["test\r\n1", "test\r\n2"],
                        "html",
                    ],
                ],
            },
        ],
    )
    def test_new_add_another_table_should_render(self, new_add_another_data):
        new_add_another_table = NewAddAnotherTable.from_dict(new_add_another_data)

        assert isinstance(new_add_another_table, NewAddAnotherTable)
        assert new_add_another_table.caption == "Test caption"
        assert new_add_another_table.head == [
            {"text": "Example text child", "format": ""},
            {"text": "Example currency child", "format": "numeric"},
            {"text": "Example month year child", "format": ""},
            {"text": "Example yes no child", "format": ""},
            {"text": "Example radio child", "format": ""},
            {"text": "Example multiline text child", "format": ""},
        ]
        assert new_add_another_table.rows == [
            [
                {"text": "test1", "format": ""},
                {"text": "£1.00", "format": "numeric"},
                {"text": "2020-01", "format": ""},
                {"text": "Yes", "format": ""},
                {"text": "Low", "format": ""},
                {"html": "test\r\n1", "format": ""},
            ],
            [
                {"text": "test2", "format": ""},
                {"text": "£2.00", "format": "numeric"},
                {"text": "2020-02", "format": ""},
                {"text": "No", "format": ""},
                {"text": "High", "format": ""},
                {"html": "test\r\n2", "format": ""},
            ],
            [
                {"text": "Total", "classes": "govuk-table__header"},
                {"text": "£3.00", "format": "numeric"},
                {"text": "", "format": ""},
                {"text": "", "format": ""},
                {"text": "", "format": ""},
                {"text": "", "format": ""},
            ],
        ]

    @pytest.mark.parametrize(
        "clazz, data",
        [
            (
                AboveQuestionAnswerPair,
                {"question": "What is your name?", "answer": "John Doe"},
            ),
            (
                BesideQuestionAnswerPair,
                {"question": "What is your name?", "answer": "John Doe"},
            ),
        ],
    )
    def test_question_answer_pair_should_render(self, clazz, data):
        qa_pair = clazz.from_dict(data)
        assert qa_pair.question == "What is your name?"
        assert qa_pair.answer == data["answer"]
        assert qa_pair.should_render is True

    @pytest.mark.parametrize(
        "clazz, data",
        [
            (
                AboveQuestionAnswerPair,
                {"question": "What is your name?", "answer": None},
            ),
            (
                BesideQuestionAnswerPair,
                {"question": "What is your name?", "answer": None},
            ),
        ],
    )
    def test_question_answer_pair_should_render_default(self, clazz, data):
        qa_pair = clazz.from_dict(data)
        assert qa_pair.question == "What is your name?"
        assert qa_pair.answer == ANSWER_NOT_PROVIDED_DEFAULT

    @pytest.mark.parametrize(
        "clazz, data",
        [
            (
                AboveQuestionAnswerPairHref,
                {"question": "What is your name?", "answer": "John Doe"},
            ),
            (
                BesideQuestionAnswerPairHref,
                {"question": "What is your name?", "answer": "John Doe"},
            ),
        ],
    )
    def test_question_answer_pair_href_should_render(self, clazz, data):
        qa_pair = clazz.from_dict(data, "https://example.com")
        assert qa_pair.question == "What is your name?"
        assert qa_pair.answer == data["answer"]
        assert qa_pair.answer_href == "https://example.com"

    @pytest.mark.parametrize(
        "clazz, data",
        [
            (
                AboveQuestionAnswerPairHref,
                {"question": "What is your name?", "answer": None},
            ),
            (
                BesideQuestionAnswerPairHref,
                {"question": "What is your name?", "answer": None},
            ),
        ],
    )
    def test_question_answer_pair_href_should_render_default(self, clazz, data):
        qa_pair = clazz.from_dict(data, "https://example.com")
        assert qa_pair.question == "What is your name?"
        assert qa_pair.answer == ANSWER_NOT_PROVIDED_DEFAULT
        assert qa_pair.answer_href is None

    def test_question_above_href_answer_list_should_render(self):
        data = {"question": "What are your favorite foods?"}
        key_to_url_dict = {
            "Pizza": "https://pizza.com",
            "Burgers": "https://burgers.com",
            "Tacos": "https://tacos.com",
        }
        question_answer_list = QuestionAboveHrefAnswerList.from_dict(data, key_to_url_dict)
        assert question_answer_list.question == "What are your favorite foods?"
        assert question_answer_list.key_to_url_dict == key_to_url_dict
        assert question_answer_list.should_render is True


class TestApplicatorsResponseComponentFactory:
    test_app = Flask("app")
    test_app.config["SERVER_NAME"] = "example.org:5000"
    test_app.register_blueprint(assessment_bp)

    @pytest.mark.parametrize(
        "item, expected_class",
        [
            (
                {
                    "presentation_type": "grouped_fields",
                    "answer": [("foo", "1"), ("bar", "2")],
                    "question": ["foo", "foo"],
                },
                MonetaryKeyValues,
            ),
            (
                {
                    "presentation_type": "text",
                    "field_type": "multilineTextField",
                    "answer": "lorem ipsum",
                    "question": "foo",
                },
                AboveQuestionAnswerPair,
            ),
            (
                {
                    "presentation_type": "text",
                    "field_type": "websiteField",
                    "answer": "https://www.example.com",
                    "question": "foo",
                },
                BesideQuestionAnswerPairHref,
            ),
            (
                {
                    "presentation_type": "text",
                    "field_type": "textField",
                    "answer": "lorem ipsum",
                    "question": "foo",
                },
                BesideQuestionAnswerPair,
            ),
            (
                {
                    "presentation_type": "integer",
                    "field_type": "numberField",
                    "answer": "100.0",
                    "question": "foo",
                },
                BesideQuestionAnswerPair,
            ),
            (
                {
                    "presentation_type": "text",
                    "field_type": "monthYearField",
                    "answer": "06-2023",
                    "question": "foo",
                },
                BesideQuestionAnswerPair,
            ),
            (
                {
                    "presentation_type": "table",
                    "field_type": "multiInputField",
                    "answer": [
                        ["", "", "html"],
                        ["", ["06-2023"], "monthYearField"],
                    ],
                    "question": "foo",
                },
                NewAddAnotherTable,
            ),
            (
                {
                    "presentation_type": "file",
                    "answer": "https://www.example.com/file.pdf",
                    "question": "foo",
                },
                AboveQuestionAnswerPairHref,
            ),
            (
                {
                    "presentation_type": "address",
                    "answer": "123 Main St",
                    "question": "foo",
                },
                FormattedBesideQuestionAnswerPair,
            ),
            (
                {
                    "presentation_type": "grouped_fields",
                    "answer": [("foo", "1"), ("bar", "2")],
                    "question": ["foo", "foo"],
                },
                MonetaryKeyValues,
            ),
            (
                {
                    "answer": [["Both revenue and capital", "1"]],
                    "branched_field": "1",
                    "field_id": ("pVBwci", "GRWtfV"),
                    "field_type": "numberField",
                    "form_name": "funding-required-ns",
                    "presentation_type": "grouped_fields",
                    "question": [
                        "How much revenue are you applying for? 1 April 2023 to 31 March 2024",
                        "How much revenue are you applying for? 1 April 2023 to 31 March 2024",
                    ],
                },
                BesideQuestionAnswerPair,
            ),
        ],
    )
    def test__ui_component_from_factory(self, item, expected_class):
        with self.test_app.app_context():
            result = _ui_component_from_factory(item, "app_123")
            assert isinstance(result, expected_class)


class TestConvertHeadingDescriptionAmountToGroupedFields:
    @pytest.mark.parametrize(
        "response, expected_grouped_fields_items, expected_field_ids",
        [
            (
                [
                    {
                        "presentation_type": "heading",
                        "field_id": "foo",
                        "question": "Foo",
                    },
                    {
                        "presentation_type": "description",
                        "field_id": "foo",
                        "question": "Description",
                    },
                    {
                        "presentation_type": "amount",
                        "field_id": "foo",
                        "question": "Amount",
                    },
                ],
                [
                    {
                        "question": "Foo",
                        "field_type": "text",
                        "field_id": "foo",
                        "presentation_type": "text",
                    }
                ],
                {"foo"},
            ),
            (
                [
                    {
                        "presentation_type": "heading",
                        "field_id": "foo",
                        "question": "Foo",
                    },
                    {
                        "presentation_type": "description",
                        "field_id": "foo",
                        "question": "Description",
                        "answer": ["lorem", "ipsum"],
                    },
                    {
                        "presentation_type": "amount",
                        "field_id": "foo",
                        "question": "Amount",
                        "answer": ["£1.23", "4.56"],
                    },
                ],
                [
                    {
                        "question": ("Foo", "Description"),
                        "field_id": "foo",
                        "answer": [("lorem", 1.23), ("ipsum", 4.56)],
                        "presentation_type": "grouped_fields",
                    }
                ],
                {"foo"},
            ),
            (
                [
                    {
                        "presentation_type": "heading",
                        "field_id": "foo",
                        "question": "Foo",
                    },
                    {
                        "presentation_type": "heading",
                        "field_id": "bar",
                        "question": "Bar",
                    },
                    {
                        "presentation_type": "description",
                        "field_id": "foo",
                        "question": "Description",
                        "answer": ["lorem", "ipsum"],
                    },
                    {
                        "presentation_type": "description",
                        "field_id": "bar",
                        "question": "Description",
                        "answer": ["dolor", "sit"],
                    },
                    {
                        "presentation_type": "amount",
                        "field_id": "foo",
                        "question": "Amount",
                        "answer": ["1.23", "4.56"],
                    },
                    {
                        "presentation_type": "amount",
                        "field_id": "bar",
                        "question": "Amount",
                        "answer": ["7.89", "0.12"],
                    },
                ],
                [
                    {
                        "question": ("Foo", "Description"),
                        "field_id": "foo",
                        "answer": [("lorem", 1.23), ("ipsum", 4.56)],
                        "presentation_type": "grouped_fields",
                    },
                    {
                        "question": ("Bar", "Description"),
                        "field_id": "bar",
                        "answer": [("dolor", 7.89), ("sit", 0.12)],
                        "presentation_type": "grouped_fields",
                    },
                ],
                {"foo", "bar"},
            ),
        ],
    )
    def test__convert_heading_description_amount(self, response, expected_grouped_fields_items, expected_field_ids):
        result, field_ids = _convert_heading_description_amount(response)
        assert result == expected_grouped_fields_items
        assert field_ids == expected_field_ids

    def test__convert_heading_description_amount_should_throw_when_bad_config(
        self,
    ):
        response = [
            {
                "presentation_type": "heading",
                "field_id": "foo",
                "question": "Foo",
            },
            {
                "presentation_type": "description",
                "field_id": "foo",
                "question": "Description",
                "answer": ["lorem", "ipsum"],
            },
            {
                "presentation_type": "amount",
                "field_id": "foo",
                "question": "Amount",
                "answer": ["1.23", "4.56"],
            },
            {
                "presentation_type": "heading",
                "field_id": "bar",
                "question": "Bar",
            },
        ]

        with pytest.raises(ValueError) as exc_info:
            _convert_heading_description_amount(response)

        assert (
            str(exc_info.value) == "Could not find item with presentation_type: description at"
            " index: 1\nThis probably means there is an uneven number of"
            " 'heading', 'description' and 'amount' items\nThere should be"
            " an equal number of each of these items"
        )


class TestConvertCheckboxItems:
    @pytest.mark.parametrize(
        "response, expected_text_items, expected_field_ids",
        [
            (
                [
                    {
                        "question": "Foo",
                        "field_type": "checkboxesField",
                        "field_id": "foo",
                        "answer": ["Lorem de", "Ipsum do"],
                    }
                ],
                [
                    {
                        "question": "Foo",
                        "field_type": "text",
                        "field_id": "foo",
                        "presentation_type": "question_heading",
                    },
                    {
                        "question": "Lorem de",
                        "field_type": "checkboxesField",
                        "field_id": "foo",
                        "answer": "Yes",
                        "presentation_type": "text",
                    },
                    {
                        "question": "Ipsum do",
                        "field_type": "checkboxesField",
                        "field_id": "foo",
                        "answer": "Yes",
                        "presentation_type": "text",
                    },
                ],
                {"foo"},
            ),
            (
                [
                    {
                        "question": "Foo",
                        "field_type": "checkboxesField",
                        "field_id": "foo",
                        "answer": [],
                    }
                ],
                [
                    {
                        "question": "Foo",
                        "field_type": "text",
                        "field_id": "foo",
                        "presentation_type": "text",
                        "answer": "None selected.",
                    },
                ],
                {"foo"},
            ),
            (
                [
                    {
                        "question": "Foo",
                        "field_type": "checkboxesField",
                        "field_id": "foo",
                        "answer": ["Lorem", "Ipsum"],
                    },
                    {
                        "question": "Bar",
                        "field_type": "checkboxesField",
                        "field_id": "bar",
                        "answer": ["Dolor", "Sit"],
                    },
                ],
                [
                    {
                        "question": "Foo",
                        "field_type": "text",
                        "field_id": "foo",
                        "presentation_type": "question_heading",
                    },
                    {
                        "question": "Lorem",
                        "field_type": "checkboxesField",
                        "field_id": "foo",
                        "answer": "Yes",
                        "presentation_type": "text",
                    },
                    {
                        "question": "Ipsum",
                        "field_type": "checkboxesField",
                        "field_id": "foo",
                        "answer": "Yes",
                        "presentation_type": "text",
                    },
                    {
                        "question": "Bar",
                        "field_type": "text",
                        "field_id": "bar",
                        "presentation_type": "question_heading",
                    },
                    {
                        "question": "Dolor",
                        "field_type": "checkboxesField",
                        "field_id": "bar",
                        "answer": "Yes",
                        "presentation_type": "text",
                    },
                    {
                        "question": "Sit",
                        "field_type": "checkboxesField",
                        "field_id": "bar",
                        "answer": "Yes",
                        "presentation_type": "text",
                    },
                ],
                {"foo", "bar"},
            ),
        ],
    )
    def test__convert_checkbox_items(self, response, expected_text_items, expected_field_ids):
        result, field_ids = _convert_checkbox_items(response)
        assert result == expected_text_items
        assert field_ids == expected_field_ids


class TestConvertNonNumberGroupedFields:
    @pytest.mark.parametrize(
        "response, expected_text_items, expected_field_ids",
        [
            (
                [
                    {
                        "question": ["Question 1", "Question 1"],
                        "field_id": ["foo"],
                        "answer": ["Answer 1"],
                        "presentation_type": "grouped_fields",
                        "field_type": "numberField",
                    }
                ],
                [],
                set(),
            ),
            (
                [
                    {
                        "question": ["Caption", "Caption"],
                        "field_id": ["foo"],
                        "answer": [("Subquestion 1", "Subanswer 1")],
                        "presentation_type": "grouped_fields",
                        "field_type": "textField",
                    }
                ],
                [
                    {
                        "question": "Subquestion 1",
                        "field_id": "foo",
                        "answer": "Subanswer 1",
                        "presentation_type": "text",
                        "field_type": "textField",
                    }
                ],
                {("foo",), "foo"},
            ),
            (
                [
                    {
                        "question": ["Caption", "Caption"],
                        "field_id": ["foo"],
                        "presentation_type": "grouped_fields",
                        "field_type": "textField",
                    }
                ],
                [
                    {
                        "question": "Caption",
                        "field_type": "text",
                        "field_id": ["foo"],
                        "presentation_type": "text",
                    }
                ],
                {("foo",), "foo"},
            ),
            (
                [
                    {
                        "question": ["Caption", "Caption"],
                        "field_id": ["foo"],
                        "presentation_type": "grouped_fields",
                        "answer": [],
                        "field_type": "textField",
                    }
                ],
                [
                    {
                        "question": "Caption",
                        "field_type": "text",
                        "field_id": ["foo"],
                        "presentation_type": "text",
                    }
                ],
                {("foo",), "foo"},
            ),
            (
                [
                    {
                        "question": ["Header", "Header"],
                        "field_id": ["foo", "bar"],
                        "answer": [
                            ("Question 1", "Answer 1"),
                            ("Question 2", "Answer 2"),
                        ],
                        "presentation_type": "grouped_fields",
                        "field_type": "textField",
                    }
                ],
                [
                    {
                        "question": "Question 1",
                        "field_id": "foo",
                        "answer": "Answer 1",
                        "presentation_type": "text",
                        "field_type": "textField",
                    },
                    {
                        "question": "Question 2",
                        "field_id": "bar",
                        "answer": "Answer 2",
                        "presentation_type": "text",
                        "field_type": "textField",
                    },
                ],
                {("foo", "bar"), "foo", "bar"},
            ),
        ],
    )
    def test__convert_non_number_grouped_fields(self, response, expected_text_items, expected_field_ids):
        result, field_ids = _convert_non_number_grouped_fields(response)
        assert result == expected_text_items
        assert field_ids == expected_field_ids


class TestUtilMethods:
    @pytest.mark.parametrize(
        "field_id, expected_field_ids",
        [
            ("foo", ["foo"]),
            (("foo", "bar"), [("foo", "bar"), "foo", "bar"]),
            (["foo", "bar"], [("foo", "bar"), "foo", "bar"]),
        ],
    )
    def test__flatten_field_ids(self, field_id, expected_field_ids):
        assert _flatten_field_ids(field_id) == expected_field_ids

    @pytest.mark.parametrize(
        "item, expected",
        [
            ({"field_id": 1}, {"field_id": 1}),
            ({"field_id": [1, 2, 3]}, {"field_id": (1, 2, 3)}),
        ],
    )
    def test__make_field_ids_hashable(self, item, expected):
        result = _make_field_ids_hashable(item)
        assert result == expected


def test_create_ui_components_retains_order(monkeypatch):
    test_app = Flask("app")
    test_app.config["SERVER_NAME"] = "example.org:5000"
    test_app.register_blueprint(assessment_bp)
    response_with_unhashable_fields = [
        {
            "field_id": "field_1",
            "question": "First",
            "answer": "John Doe",
            "presentation_type": "text",
            "field_type": "textField",
        },
        {
            "field_id": ["field_2", "field_3"],
            "question": "Second heading!",
            "answer": ["Second", "Third"],
            "presentation_type": "list",
            "field_type": "checkboxesField",
        },
        {
            "field_id": "field_4",
            "question": "Fourth",
            "answer": "Software Engineer",
            "presentation_type": "text",
            "field_type": "textField",
        },
        {
            "presentation_type": "heading",
            "field_id": "field_5",
            "question": "Fifth",
            "field_type": "multiInputField",
        },
        {
            "presentation_type": "description",
            "field_id": "field_5",
            "question": "Description",
            "field_type": "multiInputField",
            "answer": ["Subquestion 1", "Subquestion 2"],
        },
        {
            "presentation_type": "amount",
            "field_id": "field_5",
            "question": "Amount",
            "field_type": "multiInputField",
            "answer": ["1.23", "4.56"],
        },
        {
            "field_id": "field_6",
            "question": "Sixth",
            "answer": "Yes",
            "presentation_type": "text",
            "field_type": "multilineTextField",
        },
        {
            "caption": "Foo",
            "question": "Description",
            "field_id": ["field_7", "field_8"],
            "answer": [("Seventh", "a-website"), ("Eigth", "another-website")],
            "presentation_type": "grouped_fields",
            "field_type": "websiteField",
        },
        {
            "field_id": "field_9",
            "question": "Ninth",
            "answer": "Yes",
            "presentation_type": "address",
            "field_type": "UkAddressField",
        },
        {
            "field_id": "field_10",
            "question": "Tenth",
            "answer": "afile.doc",
            "presentation_type": "file",
            "field_type": "fileUploadField",
        },
        {
            "field_id": "field_11",
            "form_name": "mock_form_name",
            "path": "mock_path",
            "question": "Eleventh",
            "answer": "filename.png",  # we dynamically grab the state of the bucket
            "presentation_type": "s3bucketPath",
            "field_type": "clientSideFileUploadField",
        },
        {
            "field_id": "NdFwgy",
            "form_name": "funding-required",
            "field_type": "multiInputField",
            "presentation_type": "table",
            "question": "Twelve",
            "answer": [
                ["Description", ["first", "second"], "text"],
                ["Amount", [100, 50.25], "currency"],
            ],
        },
    ]

    monkeypatch.setattr(
        assess.assessments.models.applicants_response,
        "list_files_in_folder",
        lambda x: ["form_name/path/name/filename.png"],
    )

    with test_app.app_context():
        ui_components = create_ui_components(response_with_unhashable_fields, "app_123")

    assert all(isinstance(ui_component, ApplicantResponseComponent) for ui_component in ui_components)

    assert len(ui_components) == 13

    assert isinstance(ui_components[0], BesideQuestionAnswerPair)
    assert ui_components[0].question == "First"

    assert isinstance(ui_components[1], QuestionHeading)
    assert ui_components[1].question == "Second heading!"

    assert isinstance(ui_components[2], BesideQuestionAnswerPair)
    assert ui_components[2].question == "Second"

    assert isinstance(ui_components[3], BesideQuestionAnswerPair)
    assert ui_components[3].question == "Third"

    assert isinstance(ui_components[4], BesideQuestionAnswerPair)
    assert ui_components[4].question == "Fourth"

    assert isinstance(ui_components[5], MonetaryKeyValues)
    assert ui_components[5].caption == "Fifth"
    assert ui_components[5].question_answer_pairs[0][0] == "Subquestion 1"
    assert ui_components[5].question_answer_pairs[1][0] == "Subquestion 2"

    assert isinstance(ui_components[6], AboveQuestionAnswerPair)
    assert ui_components[6].question == "Sixth"

    assert isinstance(ui_components[7], BesideQuestionAnswerPairHref)
    assert ui_components[7].question == "Seventh"

    assert isinstance(ui_components[8], BesideQuestionAnswerPairHref)
    assert ui_components[8].question == "Eigth"

    assert isinstance(ui_components[9], FormattedBesideQuestionAnswerPair)
    assert ui_components[9].question == "Ninth"
    assert ui_components[9].formatter == format_address

    assert isinstance(ui_components[10], AboveQuestionAnswerPairHref)
    assert ui_components[10].question == "Tenth"

    assert isinstance(ui_components[11], QuestionAboveHrefAnswerList)
    assert ui_components[11].question == "Eleventh"
    assert isinstance(ui_components[11].key_to_url_dict, dict)
    assert ui_components[11].key_to_url_dict == {
        "form_name/path/name/filename.png": (
            "http://example.org:5000/assess/application/app_123/export/"
            "form_name%252Fpath%252Fname%252Ffilename.png?quoted=True"
        )
    }

    assert isinstance(ui_components[12], NewAddAnotherTable)
    assert ui_components[12].caption == "Twelve"
    assert ui_components[12].head == [
        {"text": "Description", "format": ""},
        {"text": "Amount", "format": "numeric"},
    ]
    assert ui_components[12].rows == [
        [
            {"text": "first", "format": ""},
            {"text": "£100.00", "format": "numeric"},
        ],
        [
            {"text": "second", "format": ""},
            {"text": "£50.25", "format": "numeric"},
        ],
        [
            {"text": "Total", "classes": "govuk-table__header"},
            {"text": "£150.25", "format": "numeric"},
        ],
    ]


@pytest.mark.parametrize(
    "tag, style",
    [
        ("ul", "circle"),
        ("ul", "square"),
        ("ul", ""),
        ("ol", "lower-alpha"),
        ("ol", "upper-alpha"),
        ("ol", "lower-roman"),
        ("ol", "upper-roman"),
        ("ol", "lower-greek"),
        ("ol", ""),
        ("p", ""),
    ],
)
def test_sanitise_html(tag, style):
    test_data = TestSanitiseData(tag=tag, style=style)
    response = sanitise_html(test_data.input.copy())
    assert response["answer"] == test_data.response["answer"].replace("'", '"')
