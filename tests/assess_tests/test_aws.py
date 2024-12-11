import assess
from assess.services.aws import FileData, generate_url, list_files_in_folder


def test_generate_url_short_id(app):
    file_data = FileData("app1", "form1", "path1", "comp1", "file1.txt")
    assert (
        generate_url(file_data, "short-id")
        == "http://assessment.levellingup.gov.localhost:3010/assess/application/app1/export/form1%252Fpath1%252Fcomp1%252Ffile1.txt?short_id=short-id&quoted=True"
    )


def test_generate_url(app):
    file_data = FileData("app1", "form1", "path1", "comp1", "file1.txt")
    assert (
        generate_url(file_data) == "http://assessment.levellingup.gov.localhost:3010/assess/application/app1/export/form1%252Fpath1%252Fcomp1%252Ffile1.txt?quoted=True"
    )


def test_list_files_in_folder(monkeypatch):
    def mock_list_objects_v2(Bucket, Prefix):  # noqa
        return {
            "Contents": [
                {"Key": "app_id/form_name/path/name/filename1.png"},
                {"Key": "app_id/form_name/path/name/filename2.docx"},
                {"Key": "app_id/form_name/path/name/filename3.jpeg"},
                {"Key": "app_id/form_name/path/name/filename4.png"},
                {"Key": "app_id/form_name/path/name/filename5.pdf"},
                {"Key": "app_id/form_name/path/name/filename6.txt"},
                {"Key": "app_id/form_name/path/name/filename7.doc"},
                {"Key": "app_id/form_name/path/name/filename8.docx"},
                {"Key": "app_id/form_name/path/name/filename9.odt"},
                {"Key": "app_id/form_name/path/name/filename10.csv"},
                {"Key": "app_id/form_name/path/name/filename11.xls"},
                {"Key": "app_id/form_name/path/name/filename12.xlsx"},
                {"Key": "app_id/form_name/path/name/filename13.ods"},
            ]
        }

    monkeypatch.setattr(
        assess.services.aws._S3_CLIENT,
        "list_objects_v2",
        mock_list_objects_v2,
    )

    prefix = "app_id/form_name/path/name/"
    files = list_files_in_folder(prefix)

    assert files == [
        "form_name/path/name/filename1.png",
        "form_name/path/name/filename2.docx",
        "form_name/path/name/filename3.jpeg",
        "form_name/path/name/filename4.png",
        "form_name/path/name/filename5.pdf",
        "form_name/path/name/filename6.txt",
        "form_name/path/name/filename7.doc",
        "form_name/path/name/filename8.docx",
        "form_name/path/name/filename9.odt",
        "form_name/path/name/filename10.csv",
        "form_name/path/name/filename11.xls",
        "form_name/path/name/filename12.xlsx",
        "form_name/path/name/filename13.ods",
    ]
