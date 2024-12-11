import pytest

from assess.assessments.models.full_application import FullApplicationPdfContext


@pytest.fixture
def mock_args():
    class Args:
        form_name_to_title_map = {"section1": "Section One"}
        question_to_answer = {"section1": {"q1": "answer1"}}
        all_uploaded_documents = [{"question": "uploaded1", "answer": "doc1"}]
        short_id = "12345"

        class Fund:
            name = "Fund Name"
            owner_organisation_name = "Organisation Name"
            owner_organisation_shortname = "Short Name"
            owner_organisation_logo_uri = "http://logo.url"

        fund = Fund()

        class Round:
            title = "Round Title"
            display_logo_on_pdf_exports = True
            all_uploaded_documents_section_available = True

        round = Round()

        application_json = {
            "short_id": "1234",
            "date_submitted": "2023-06-06T13:38:51.467199",
        }

    return Args()


@pytest.mark.parametrize(
    "all_docs_available,display_logo,expected_len_sections,expected_logo_uri",
    [
        (True, True, 2, "http://logo.url"),
        (True, False, 2, None),
        (False, True, 1, "http://logo.url"),
        (False, False, 1, None),
    ],
)
def test_from_data(
    mock_args,
    all_docs_available,
    display_logo,
    expected_len_sections,
    expected_logo_uri,
    app,
):
    mock_args.round.all_uploaded_documents_section_available = all_docs_available
    mock_args.round.display_logo_on_pdf_exports = display_logo
    with app.test_request_context(headers={"Host": app.config["ASSESS_HOST"]}):
        context = FullApplicationPdfContext.from_data(mock_args)

        assert context.title == "Fund Name"
        assert context.response_id == "12345"
        assert context.submission_to == "Fund Name Round Title"
        assert context.submitted_on == "06/06/2023 at 14:38"  # Timestamp is converted to bst
        assert context.organisation_name == "Organisation Name"
        assert context.organisation_shortname == "Short Name"
        assert context.organisation_logo_uri == expected_logo_uri
        assert len(context.sections) == expected_len_sections
