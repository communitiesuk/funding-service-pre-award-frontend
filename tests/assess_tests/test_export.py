from unittest import mock

from fsd_utils import extract_questions_and_answers, generate_text_of_application

import assess
from assess.assessments.helpers import get_files_for_application_upload_fields
from tests.assess_tests.api_data.example_application_answers import test_application_answers
from tests.assess_tests.api_data.example_application_json_blob import single_application_json_blob


class TestExport:
    def test_extract_q_and_a(self, app):
        result = extract_questions_and_answers(single_application_json_blob["forms"])
        assert "sample1.doc" == result["upload-business-plan"]["Upload business plan"]
        assert (
            "lots of surveys"
            == result["feasibility"]["Tell us about the feasibility studies you have carried out for your project"]
        )
        assert "No" == result["feasibility"]["Do you need to do any further feasibility work?"]
        assert (
            "Yes"
            == result["declarations"][
                "Confirm you have considered subsidy control"
                " and state aid implications for your project,"
                " and the information you have given us is"
                " correct"
            ]
        )

    def test_generate_text(self, app):
        result = generate_text_of_application(test_application_answers, "TEST FUND")
        assert "********* TEST FUND" in result
        assert "Q) Capital funding" in result
        assert "A) 2300" in result

    def test_get_files_for_application_upload_fields(self, monkeypatch, app):
        application_id = "dummy_id"
        short_id = "d_id"

        def mock_list_objects_v2(Bucket, Prefix):  # noqa
            return {
                "Contents": [
                    {"Key": "app_id/form_name/path/name/filename1.png"},
                ]
            }

        monkeypatch.setattr(
            assess.services.aws._S3_CLIENT,
            "list_objects_v2",
            mock_list_objects_v2,
        )

        with mock.patch(
            "assess.assessments.helpers.url_for",
            return_value="dummy/path/to/file.dmp",
        ):
            ans = get_files_for_application_upload_fields(
                application_id,
                short_id,
                {"jsonb_blob": single_application_json_blob},
            )

        assert ans == [
            ("sample1.doc", "dummy/path/to/file.dmp"),
            ("awskey123123123123123/sample1.doc", "dummy/path/to/file.dmp"),
            (
                "filename1.png",
                "http://assessment.levellingup.gov.localhost:3010/assess/application/app_id/export/"
                "form_name%252Fpath%252Fname%252Ffilename1.png?short_id=d_id&quoted=True",
            ),
        ]
