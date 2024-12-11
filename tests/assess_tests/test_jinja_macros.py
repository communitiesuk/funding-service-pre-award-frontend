import re
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup
from flask import g, get_template_attribute, render_template_string
from flask_wtf.csrf import generate_csrf
from fsd_utils.authentication.models import User

from assess.assessments.forms.comments_form import CommentsForm
from assess.assessments.models.applicants_response import (
    AboveQuestionAnswerPair,
    AboveQuestionAnswerPairHref,
    AboveQuestionAnswerPairHtml,
    BesideQuestionAnswerPair,
    BesideQuestionAnswerPairHref,
    FormattedBesideQuestionAnswerPair,
    MonetaryKeyValues,
    NewAddAnotherTable,
    QuestionAboveHrefAnswerList,
    QuestionHeading,
)
from assess.assessments.models.round_status import RoundStatus
from assess.authentication.validation import AssessmentAccessController
from assess.scoring.forms.rescore_form import RescoreForm
from assess.scoring.forms.scores_and_justifications import OneToFiveScoreForm, ZeroToThreeScoreForm
from assess.services.models.assessor_task_list import _Criteria, _CriteriaSubCriteria, _SubCriteria
from assess.shared.filters import format_address
from config.envs.unit_test import UnitTestConfig


def default_flask_g():
    g.user = User(
        full_name="Test Lead Assessor",
        email="test@example.com",
        roles=["COF_LEAD_ASSESSOR", "COF_ASSESSOR", "COF_COMMENTER"],
        highest_role_map={"COF": "LEAD_ASSESSOR"},
    )
    g.access_controller = AssessmentAccessController("COF")
    return g


class TestJinjaMacros(object):
    def test_criteria_macro_lead_assessor(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{criteria_element(criteria, name_classes, application_id, max_possible_sub_criteria_score)}}",
                criteria_element=get_template_attribute("assess/macros/criteria_element.html", "criteria_element"),
                criteria=_Criteria(
                    name="Example title",
                    total_criteria_score=2,
                    number_of_scored_sub_criteria=2,
                    weighting=0.5,
                    sub_criterias=[
                        _CriteriaSubCriteria(
                            id="1",
                            name="Sub Criteria 1",
                            status="NOT_STARTED",
                            theme_count=1,
                            score=0,
                        ),
                        _CriteriaSubCriteria(
                            id="2",
                            name="Sub Criteria 2",
                            status="NOT_STARTED",
                            theme_count=2,
                            score=2,
                        ),
                    ],
                ),
                name_classes="example-class",
                application_id=1,
                max_possible_sub_criteria_score=4,
                g=default_flask_g(),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert soup.find("h3", class_="example-class").text == "Example title", "Title not found"

            assert (
                soup.find("p", class_="govuk-body govuk-!-margin-bottom-2").text.strip() == "50% of overall score."
            ), "Weighting not found"

            table = soup.find(
                "table",
                class_="govuk-table govuk-!-margin-bottom-6 govuk-table-no-bottom-border",
            )

            assert table is not None, "Table should have border negation class"

            assert len(soup.find_all("table")) == 1, "Should have 1 table"
            assert len(table.find_all("thead")) == 1, "Should have 1 table header"
            assert len(table.find_all("tbody")) == 1, "Should have 1 table body"
            assert len(table.find_all("tr")) == 4, "Should have 4 table rows"

            assert table.find("strong", text="Total criteria score") is not None, "Should have Total criteria score"
            assert table.find("th", text="Score out of 4") is not None, "Should have Score out of 4 column"
            assert soup.find_all("td", class_="govuk-table__cell--numeric")[0].text == "0", "Should have 0 score"
            assert soup.find_all("td", class_="govuk-table__cell--numeric")[2].text == "2", "Should have 2 score"
            assert (
                soup.find_all("td", class_="govuk-table__cell--numeric")[4].text == "2 of 8"
            ), "Should have 2 of 8 score"

    def test_criteria_macro_commenter(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            g.user = User(
                full_name="Test Commenter",
                email="test@example.com",
                roles=["COF_COMMENTER"],
                highest_role_map={"COF": "COMMENTER"},
            )
            g.access_controller = AssessmentAccessController("COF")
            rendered_html = render_template_string(
                "{{criteria_element(criteria, name_classes, application_id)}}",
                criteria_element=get_template_attribute("assess/macros/criteria_element.html", "criteria_element"),
                criteria=_Criteria(
                    name="Example title",
                    total_criteria_score=0,
                    number_of_scored_sub_criteria=0,
                    weighting=0.5,
                    sub_criterias=[
                        _CriteriaSubCriteria(
                            id="1",
                            name="Sub Criteria 1",
                            status="NOT_STARTED",
                            theme_count=1,
                            score=2,
                        ),
                        _CriteriaSubCriteria(
                            id="2",
                            name="Sub Criteria 2",
                            status="NOT_STARTED",
                            theme_count=2,
                            score=2,
                        ),
                    ],
                ),
                name_classes="example-class",
                application_id=1,
                g=g,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert len(soup.select("tr")) == 3, "Should have 3 table rows"

            assert not soup.find("strong", text="Total criteria score"), "Should not have Total criteria score"

            assert not soup.find("th", text="Score out of 5"), "Should not have Score out of 5 column"

    def test_section_macro(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{section_element(name, sub_criterias, application_id)}}",
                section_element=get_template_attribute("assess/macros/section_element.html", "section_element"),
                name="Example title",
                sub_criterias=[
                    _SubCriteria(
                        id="1",
                        name="Sub Criteria 1",
                    ),
                    _SubCriteria(
                        id="2",
                        name="Sub Criteria 2",
                    ),
                ],
                application_id=1,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert soup.find(
                "h2",
                {"class": "govuk-heading-l govuk-!-margin-top-4"},
                text="Example title",
            ), "Title not found"

    @pytest.mark.parametrize(
        "scoring_system_form,expected_score_option_count,error_present",
        [(OneToFiveScoreForm, 5, True), (ZeroToThreeScoreForm, 4, False)],
    )
    def test_score_macro(
        self,
        app,
        scoring_system_form,
        expected_score_option_count,
        error_present,
    ):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            form = scoring_system_form()
            form.score.errors = error_present
            rendered_html = render_template_string(
                "{{scores(form)}}",
                scores=get_template_attribute("assess/macros/scores.html", "scores"),
                form=form,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert (
                soup.find("legend", {"class": "govuk-body"}).text.strip() == "You can rescore at any point."
            ), "Title not found"

            radios = soup.find_all("div", {"class": "govuk-radios__item"})
            assert len(radios) == expected_score_option_count, f"Should have {expected_score_option_count} radios"

            score_spans = soup.find_all("span", {"class": "govuk-!-font-weight-bold"})
            assert (
                len(score_spans) == expected_score_option_count
            ), f"Should have {expected_score_option_count} score values for radios"

            if error_present:
                assert soup.find("p", {"class": "govuk-error-message"}).text.strip() == "Error: Select a score"
            else:
                assert soup.find("p", {"class": "govuk-error-message"}) == None  # noqa

    def test_comment_macro(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{comment_box(comment_form)}}",
                comment_box=get_template_attribute("assess/macros/comments_box.html", "comment_box"),
                comment_form=CommentsForm(),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            add_comment_label = soup.find("label")
            assert add_comment_label.text.strip() == "Add a comment"
            assert add_comment_label is not None, "Add Comment label not found"

            save_comment_button = soup.find("button")
            assert save_comment_button.text.strip() == "Save comment"
            assert save_comment_button is not None, "Save comment button not found"

    def test_justification_macro(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            form = OneToFiveScoreForm()
            form.justification.errors = True
            rendered_html = render_template_string(
                "{{justification(form)}}",
                justification=get_template_attribute("assess/macros/justification.html", "justification"),
                form=form,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            title_label = soup.find("label")
            assert title_label.text.strip() == "Add rationale for this score"
            assert title_label is not None, "Title not found"

            error_message = soup.find("p", class_="govuk-error-message")
            assert error_message.text.strip() == "Error: Please provide rationale for this score"
            assert error_message is not None, "Intentional error not found"

    def test_monetary_key_values(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            meta = MonetaryKeyValues.from_dict(
                {
                    "question": ("Test Caption", "Test Description"),
                    "answer": [("Question 1", "50.00"), ("Question 2", "100.00")],
                }
            )

            rendered_html = render_template_string(
                "{{ monetary_key_values(meta) }}",
                monetary_key_values=get_template_attribute(
                    "assess/macros/theme/monetary_key_values.jinja2",
                    "monetary_key_values",
                ),
                meta=meta,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert soup.find("caption", text="Test Caption"), "Caption not found"
            assert soup.find("th", text="Test Description"), "Column description not found"
            assert soup.find("td", text="£50.00"), "First answer not found"
            assert soup.find("td", text="£100.00"), "Second answer not found"
            assert soup.find("td", text="Total"), "Total header not found"
            assert soup.find("td", text="£150.00"), "Total not found"

    def test_new_add_another_table(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            meta = NewAddAnotherTable.from_dict(
                {
                    "question": "Test Caption",
                    "answer": [
                        ["Test Description", ["first", "second"], "text"],
                        ["Test Amount", [100, 50.25], "currency"],
                    ],
                }
            )

            rendered_html = render_template_string(
                "{{ new_add_another_table(meta) }}",
                new_add_another_table=get_template_attribute(
                    "assess/macros/theme/new_add_another_table.jinja2",
                    "new_add_another_table",
                ),
                meta=meta,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert soup.find("caption", text="Test Caption")
            assert soup.find("th", text="Test Description")
            assert soup.find("th", text="Test Amount")

            assert soup.find("td", text="first")
            assert soup.find("td", text="£100.00")

            assert soup.find("td", text="second")
            assert soup.find("td", text="£50.25")

            assert soup.find("td", text="Total")
            assert soup.find("td", text="£150.25")

    @pytest.mark.parametrize(
        "clazz, macro_name, answer, expected",
        [
            (
                AboveQuestionAnswerPair,
                "question_above_answer",
                50.00,
                "£50.00",
            ),
            (
                BesideQuestionAnswerPair,
                "question_beside_answer",
                "Test Answer",
                "Test Answer",
            ),
            (
                AboveQuestionAnswerPairHtml,
                "question_above_answer_html",
                "<p>This is <strong>free text answer</strong></p>",
                "<p>This is <strong>free text answer</strong></p>",
            ),
        ],
    )
    def test_question_above_answer(self, app, clazz, macro_name, answer, expected):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            meta = clazz.from_dict({"question": "Test Question", "answer": answer})

            rendered_html = render_template_string(
                f"{{{{ {macro_name}(meta) }}}}",
                **{macro_name: get_template_attribute(f"assess/macros/theme/{macro_name}.jinja2", macro_name)},
                meta=meta,
            )

            assert "Test Question" in rendered_html, "Question not found"
            assert expected in rendered_html, "Answer not found"

    def test_question_above_answer_html(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            meta = AboveQuestionAnswerPairHtml.from_dict(
                {
                    "question": "Test Caption",
                    "answer": "<p>This is</p> <strong>free text answer</strong>",
                }
            )

            rendered_html = render_template_string(
                "{{ question_above_answer_html(meta) }}",
                question_above_answer_html=get_template_attribute(
                    "assess/macros/theme/question_above_answer_html.jinja2",
                    "question_above_answer_html",
                ),
                meta=meta,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert soup.find("p", text="This is") is not None, "<p> tag text not found"
            assert soup.find("strong", text="free text answer") is not None, "<strong> tag text not found"

    @pytest.mark.parametrize(
        "clazz, macro_name",
        [
            (AboveQuestionAnswerPairHref, "question_above_href_answer"),
            (BesideQuestionAnswerPairHref, "question_beside_href_answer"),
        ],
    )
    def test_question_above_href_answer(self, app, clazz, macro_name):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            meta = clazz.from_dict(
                {"question": "Test Question", "answer": "Test Answer"},
                href="http://www.example.com",
            )

            rendered_html = render_template_string(
                f"{{{{ {macro_name}(meta) }}}}",
                **{macro_name: get_template_attribute(f"assess/macros/theme/{macro_name}.jinja2", macro_name)},
                meta=meta,
            )

            allowlist = [
                "http://www.example.com",
            ]

            assert "Test Question" in rendered_html, "Question not found"
            assert "Test Answer" in rendered_html, "Answer not found"
            assert any(href in rendered_html for href in allowlist), "Link href not found"

    def test_question_above_href_answer_list(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            meta = QuestionAboveHrefAnswerList.from_dict(
                {"question": "Test Question"},
                key_to_url_dict={
                    "File 1": "http://example.com/file1.pdf",
                    "File 2": "http://example.com/file2.pdf",
                },
            )

            rendered_html = render_template_string(
                "{{ question_above_href_answer_list(meta) }}",
                question_above_href_answer_list=get_template_attribute(
                    "assess/macros/theme/question_above_href_answer_list.jinja2",
                    "question_above_href_answer_list",
                ),
                meta=meta,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert "Test Question" in rendered_html, "Question not found"
            assert soup.find("a", href="http://example.com/file1.pdf").text == "File 1", "File 1 not found"
            assert soup.find("a", href="http://example.com/file2.pdf").text == "File 2", "File 2 not found"
            assert not soup.find(text="Not provided."), "Unexpected 'Not provided."

    def test_question_beside_with_formatted_answer_multiline(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            meta = FormattedBesideQuestionAnswerPair.from_dict(
                {
                    "question": "Test Question",
                    "answer": "Test Address, null, Test Town Or City, null, QQ12 7QQ",
                },
                formatter=format_address,
            )

            rendered_html = render_template_string(
                "{{ question_beside_with_formatted_answer(meta) }}",
                question_beside_with_formatted_answer=get_template_attribute(
                    "assess/macros/theme/question_beside_with_formatted_answer.jinja2",
                    "question_beside_with_formatted_answer",
                ),
                meta=meta,
            )

            assert "Test Question" in rendered_html, "Answer not found"
            assert "Test Address<br>" in rendered_html, "First line of address not found"
            assert "Test Town Or City<br>" in rendered_html, "Second line of address not found"
            assert "QQ12 7QQ" in rendered_html, "Third line of address not found"

    @pytest.mark.parametrize(
        "clazz, arguments, expected_unique_id",
        [
            (
                MonetaryKeyValues,
                {
                    "data": {
                        "question": ("Test Caption", "unique-key-1"),
                        "answer": [
                            ("Question 1", "50.00"),
                            ("Question 2", "100.00"),
                        ],
                    }
                },
                "unique-key-1",
            ),
            (
                AboveQuestionAnswerPair,
                {"data": {"question": "unique-key-2", "answer": 50.00}},
                "unique-key-2",
            ),
            (
                BesideQuestionAnswerPair,
                {
                    "data": {
                        "question": "unique-key-3",
                        "answer": "Test Answer",
                    }
                },
                "unique-key-3",
            ),
            (
                AboveQuestionAnswerPairHref,
                {
                    "data": {
                        "question": "unique-key-4",
                        "answer": "Test Answer",
                    },
                    "href": "http://www.example.com",
                },
                "unique-key-4",
            ),
            (
                BesideQuestionAnswerPairHref,
                {
                    "data": {
                        "question": "unique-key-5",
                        "answer": "Test Answer",
                    },
                    "href": "http://www.example.com",
                },
                "unique-key-5",
            ),
            (
                FormattedBesideQuestionAnswerPair,
                {
                    "data": {
                        "question": "unique-key-6",
                        "answer": "Test Address, null, Test Town Or City, null, QQ12 7QQ",
                    },
                    "formatter": format_address,
                },
                "unique-key-6",
            ),
            (
                QuestionHeading,
                {
                    "data": {
                        "question": "unique-key-7",
                    }
                },
                "unique-key-7",
            ),
        ],
    )
    def test_theme_mapping_works_based_on_meta_key(self, app, clazz, arguments, expected_unique_id):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            meta = clazz.from_dict(**arguments)

            rendered_html = render_template_string(
                "{{ theme([meta]) }}",
                theme=get_template_attribute("assess/macros/theme.html", "theme"),
                meta=meta,
            )

            assert expected_unique_id in rendered_html, "Unique ID not found"

    @pytest.mark.parametrize(
        "fund_short_name, show_funding_amount_requested, project_name_caption,show_assessment_status,"
        "is_eoi_round,display_status",
        [
            ("TFID", True, "Project name:", True, False, True),
            ("TFID", True, "Project name:", True, False, False),
            ("DPIF", False, "Project name:", True, False, True),
            ("COF-EOI", False, "Organisation name:", False, True, True),
            ("AnotherEOIRound", False, "Organisation name:", False, True, True),
            ("AnotherEOIRound", False, "Organisation name:", False, True, False),
            ("HSRA", True, "Project name:", True, False, True),
        ],
    )
    def test_banner_summary_macro(
        self,
        app,
        fund_short_name,
        show_funding_amount_requested,
        project_name_caption,
        show_assessment_status,
        is_eoi_round,
        display_status,
    ):
        fund_name = "Test Fund"
        project_reference = "TEST123"
        project_name = "Test Project"
        funding_amount_requested = 123456.78
        assessment_status = "Submitted"
        flag_status = "Flagged"
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{ banner_summary(fund_name, fund_short_name, project_reference,"
                " project_name, funding_amount_requested, assessment_status,"
                " flag_status, display_status, is_eoi_round) }}",
                banner_summary=get_template_attribute("assess/macros/banner_summary.html", "banner_summary"),
                fund_name=fund_name,
                fund_short_name=fund_short_name,
                project_reference=project_reference,
                project_name=project_name,
                funding_amount_requested=funding_amount_requested,
                assessment_status=assessment_status,
                flag_status=flag_status,
                is_eoi_round=is_eoi_round,
                display_status=display_status,
                g=default_flask_g(),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert (
                soup.find("p", class_="govuk-heading-xl fsd-banner-content").text.strip() == "Fund: Test Fund"
            ), "Fund name not found"
            assert (
                soup.find("p", class_="govuk-heading-l fsd-banner-content").text.strip() == "Project reference: TEST123"
            ), "Project reference not found"

            assert soup.find(
                "p",
                class_="govuk-body-l fsd-banner-content fsd-banner-collapse-padding",
                text=f"{project_name_caption}\xa0Test Project",
            ), "Project name not found"

            funding_amount_requested_element = soup.find(
                "p",
                class_="govuk-body-l fsd-banner-content",
                text="Total funding requested: £123,456.78",
            )
            if show_funding_amount_requested:
                assert funding_amount_requested_element, "Funding amount not found"
            else:
                assert not funding_amount_requested_element, "Funding amount found"

            assessment_status_element = soup.find(
                "strong",
                class_="govuk-tag",
                text="Submitted",
            )
            if show_assessment_status and display_status:
                assert assessment_status_element, "Assessment status not found"
            else:
                assert not assessment_status_element, "Assessment status found when not expected"

            flag_status_element = soup.find("p", class_="fsd-banner-content", text="Flagged")
            if display_status:
                assert flag_status_element, "Flag status not found"
            else:
                assert not flag_status_element

    def test_stopped_flag_macro(self, app):
        fund_name = "Test Fund"
        fund_short_name = "TFID"
        project_reference = "TEST123"
        project_name = "Test Project"
        funding_amount_requested = 123456.78
        assessment_status = "In progress"
        flag_status = "Stopped"
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{ banner_summary(fund_name, fund_short_name, project_reference,"
                " project_name, funding_amount_requested, assessment_status,"
                " flag_status) }}",
                banner_summary=get_template_attribute("assess/macros/banner_summary.html", "banner_summary"),
                fund_name=fund_name,
                fund_short_name=fund_short_name,
                project_reference=project_reference,
                project_name=project_name,
                funding_amount_requested=funding_amount_requested,
                assessment_status=assessment_status,
                flag_status=flag_status,
                g=default_flask_g(),
            )

            assert "Stopped" in rendered_html

    def test_flag_application_button(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{flag_application_button(12345)}}",
                flag_application_button=get_template_attribute(
                    "assess/macros/flag_application_button.html",
                    "flag_application_button",
                ),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            flag_container = soup.find("div", {"class": "govuk-grid-row govuk-!-text-align-right"})
            assert flag_container is not None, "Flag application button container not found"

            flag_link = flag_container.find(
                "a",
                {
                    "href": "/assess/flag/12345",
                    "class": "govuk-button primary-button",
                    "data-module": "govuk-button",
                },
            )
            assert flag_link is not None, "Flag application button not found"
            assert flag_link.text.strip() == "Flag application", "Flag application button text does not match"

    def test_mark_qa_complete_button(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{mark_qa_complete_button(12345)}}",
                mark_qa_complete_button=get_template_attribute(
                    "assess/macros/mark_qa_complete_button.html",
                    "mark_qa_complete_button",
                ),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            button_container = soup.find("div", class_="govuk-grid-row govuk-!-text-align-right")
            assert button_container is not None, "Mark QA complete button container not found"

            button_element = button_container.find("a", href="/assess/qa_complete/12345")
            assert button_element is not None, "Mark QA complete button not found"

    def test_stopped_assessment_flag(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{assessment_stopped(flag, user_info)}}",
                assessment_stopped=get_template_attribute("assess/macros/assessment_flag.html", "assessment_stopped"),
                flag={
                    "latest_status": {"name": "STOPPED"},
                    "latest_allocation": "Team A",
                    "updates": [
                        {
                            "justification": "Test justification",
                            "status": {"name": "STOPPED"},
                        }
                    ],
                    "sections_to_flag": ["Test section"],
                    "date_created": "2020-01-01 12:00:00",
                },
                user_info={
                    "full_name": "Test user",
                    "highest_role": "Test role",
                    "email_address": "test@example.com",
                },
                g=default_flask_g(),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            alert_div = soup.find("div", class_="assessment-alert")

            assert (
                alert_div.find("h1", class_="assessment-alert__heading govuk-heading-l").text.strip()
                == "Flagged for Team A - Assessment stopped"
            ), "Flag type not found"

            assert alert_div.find("h2", class_="govuk-heading-m").text == "Reason", "Reason heading not found"

            assert alert_div.find("p", class_="govuk-body").text == "Test justification", "Justification not found"

            user_paragraph = alert_div.find("p", class_="govuk-body-s")
            assert "test@example.com" in user_paragraph.text, "User email not found"

            assert "Test role" in user_paragraph.text, "User role not found"

            date_created_paragraph = alert_div.find("p", class_="govuk-body-s")
            assert date_created_paragraph is not None, "Date created paragraph not found"

    def test_assessment_flag(self, app):
        def get_section_from_sub_criteria_id(self, sub_criteria_id):
            return {
                "sub_section_name": sub_criteria_id,
                "parent_section_name": "Parent Test section",
            }

        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{assessment_flagged(state, flag, user_info, state)}}",
                assessment_flagged=get_template_attribute("assess/macros/assessment_flag.html", "assessment_flagged"),
                state=type(
                    "State",
                    (),
                    {"get_section_from_sub_criteria_id": get_section_from_sub_criteria_id},
                )(),
                flag={
                    "latest_status": {"name": "RAISED"},
                    "updates": [
                        {
                            "justification": "Test justification",
                            "status": {"name": "RAISED"},
                        }
                    ],
                    "sections_to_flag": ["Test section"],
                    "date_created": "2020-01-01 12:00:00",
                },
                user_info={
                    "full_name": "Test user",
                    "highest_role": "Test role",
                    "email_address": "test@example.com",
                },
                g=default_flask_g(),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            alert_div = soup.find("div", class_="assessment-alert--flagged")

            reason_heading = alert_div.find("h2", text="Reason")
            assert reason_heading is not None, "Reason heading not found"
            justification = reason_heading.find_next_sibling(
                "p",
            )
            assert justification is not None and justification.text == "Test justification", "Justification not found"

            section_heading = alert_div.find("h2", text="Section(s) flagged")
            assert section_heading is not None, "Section(s) flagged heading not found"
            section = section_heading.find_next_sibling("p")
            assert (
                section is not None and section.text == "Test section (Parent Test section) (Opens in new tab) "
            ), "Section not found"

            notification_heading = alert_div.find("h2", text="Notification sent")
            assert notification_heading is not None, "Notification sent heading not found"
            notification = notification_heading.find_next_sibling("p")
            assert notification is not None and notification.text == "No", "Notification not found"

            user_info = alert_div.find_all("p", class_="govuk-body-s")
            assert any("test@example.com" in info.text for info in user_info), "User info not found"

            date_created = alert_div.find("p", class_="govuk-body-s").find_next_sibling("p", class_="govuk-body-s")
            assert date_created is not None and re.match(
                r"\d{2}/\d{2}/\d{4} at \d{2}:\d{2}", date_created.text
            ), "Date created not found"

    def test_assessment_completion_state_completed(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{assessment_complete(state, csrf_token, application_id)}}",
                assessment_complete=get_template_attribute("assess/macros/assessment_completion.html", "assessment_complete"),
                state=type("State", (), {"workflow_status": "COMPLETED"})(),
                csrf_token=generate_csrf(),
                application_id=1,
                g=default_flask_g(),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert soup.find("h2", class_="assessment-alert__heading").string == "Assessment complete"

            assert soup.find("p", class_="govuk-body").string == "You have marked this assessment as complete."

    def test_assessment_completion_flagged(self, app):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{assessment_complete(state, srf_token, application_id)}}",
                assessment_complete=get_template_attribute("assess/macros/assessment_completion.html", "assessment_complete"),
                state=type("State", (), {"workflow_status": "IN_PROGRESS"})(),
                csrf_token=generate_csrf(),
                application_id=1,
                g=default_flask_g(),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert soup.find("h2", class_="assessment-alert__heading").string == "All sections assessed"

    @pytest.mark.parametrize(
        "sub_criteria, expected_heading, has_forms",
        [
            ({"name": "Engagement"}, "Score engagement", True),
            ({"name": "Engagement"}, "Engagement", False),
            # Add more test cases as needed
        ],
    )
    def test_sub_criteria_heading(self, app, sub_criteria, expected_heading, has_forms):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{sub_criteria_heading(sub_criteria, score_form, rescore_form)}}",
                sub_criteria_heading=get_template_attribute("assess/macros/sub_criteria_heading.html", "sub_criteria_heading"),
                score_form=OneToFiveScoreForm() if has_forms else None,
                rescore_form=RescoreForm() if has_forms else None,
                sub_criteria=sub_criteria,
            )

            soup = BeautifulSoup(rendered_html, "html.parser")

            assert soup.find("h2", class_="govuk-heading-l scoring-heading").string == expected_heading

    @pytest.mark.parametrize(
        "application_not_yet_open, application_open, is_assessment_active, has_assessment_closed, exp_colour_class,"
        " exp_text",
        [
            (True, False, False, False, " govuk-tag--grey", "APPLICATION NOT YET OPEN"),
            (False, True, False, False, None, "APPLICATION LIVE"),
            (False, False, True, False, None, "ASSESSMENT ACTIVE"),
            (False, True, True, False, None, "ASSESSMENT ACTIVE"),
            (False, False, False, True, " govuk-tag--grey", "ASSESSMENT CLOSED"),
        ],
    )
    def test_dashboard_summary_assessment_status(
        self,
        app,
        application_not_yet_open,
        application_open,
        is_assessment_active,
        has_assessment_closed,
        exp_colour_class,
        exp_text,
    ):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            rendered_html = render_template_string(
                "{{assessment_status(round_status)}}",
                assessment_status=get_template_attribute("assess/macros/fund_dashboard_summary.html", "assessment_status"),
                round_status=RoundStatus(
                    application_not_yet_open,
                    application_open,
                    False,
                    is_assessment_active,
                    False,
                    has_assessment_closed,
                ),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")
            assert (
                soup.find(
                    "div",
                    class_=f"govuk-tag govuk-!-margin-bottom-2 govuk-summary-card__title{exp_colour_class or ''}",
                ).text.strip()
                == exp_text
            )

    @pytest.mark.parametrize(
        "is_lead_assessor, download_available, export_href, feedback_export_href,assessment_tracker_href,"
        " is_assessment_active, has_assessment_opened, has_application_closed, exp_links_text",
        [
            (
                True,
                True,
                "export",
                "feedback",
                "tracker",
                True,
                True,
                True,
                [
                    "View all active assessments",
                    "Export applicant information",
                    "Export feedback survey responses",
                    "Assessment Tracker Export",
                ],
            ),
            (
                True,
                True,
                "export",
                "feedback",
                "tracker",
                False,
                False,
                False,
                [
                    "Export feedback survey responses",
                ],
            ),
            (
                True,
                True,
                "export",
                "feedback",
                "tracker",
                True,
                True,
                False,
                [
                    "View all active assessments",
                    "Export applicant information",
                    "Export feedback survey responses",
                    "Assessment Tracker Export",
                ],
            ),
            (
                False,
                True,
                "export",
                "feedback",
                "tracker",
                True,
                True,
                True,
                [
                    "View all active assessments",
                ],
            ),
            (
                True,
                True,
                "export",
                "feedback",
                "tracker",
                False,
                True,
                True,
                [
                    "View all closed assessments",
                    "Export applicant information",
                    "Export feedback survey responses",
                    "Assessment Tracker Export",
                ],
            ),
            (
                True,
                True,
                "export",
                None,
                "tracker",
                False,
                True,
                True,
                [
                    "View all closed assessments",
                    "Export applicant information",
                    "Assessment Tracker Export",
                ],
            ),
            (
                True,
                True,
                "",
                "feedback",
                "",
                False,
                True,
                True,
                [
                    "View all closed assessments",
                    "Export feedback survey responses",
                ],
            ),
            (
                True,
                False,
                "export",
                "feedback",
                "tracker",
                True,
                True,
                True,
                [
                    "View all active assessments",
                    "Assessment Tracker Export",
                ],
            ),
        ],
    )
    def test_dashboard_summary_round_links(
        self,
        app,
        is_lead_assessor,
        download_available,
        export_href,
        feedback_export_href,
        assessment_tracker_href,
        is_assessment_active,
        has_assessment_opened,
        has_application_closed,
        exp_links_text,
    ):
        with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
            mock_access_controller = MagicMock()
            mock_access_controller.is_lead_assessor = is_lead_assessor
            rendered_html = render_template_string(
                "{{round_links(access_controller, assessments_href, download_available, export_href,"
                " feedback_export_href,assessment_tracker_href, round_status)}}",
                round_links=get_template_attribute("assess/macros/fund_dashboard_summary.html", "round_links"),
                access_controller=mock_access_controller,
                assessments_href="assessments_href",
                download_available=download_available,
                export_href=export_href,
                feedback_export_href=feedback_export_href,
                assessment_tracker_href=assessment_tracker_href,
                round_status=RoundStatus(
                    False,
                    False,
                    has_application_closed,
                    is_assessment_active,
                    has_assessment_opened,
                    False,
                ),
            )

            soup = BeautifulSoup(rendered_html, "html.parser")
            found_links = soup.find_all("a", class_="govuk-link")
            assert len(found_links) == len(exp_links_text)
            for text in exp_links_text:
                assert soup.find("a", class_="govuk-link", string=lambda str: text in str)  # noqa: B023
