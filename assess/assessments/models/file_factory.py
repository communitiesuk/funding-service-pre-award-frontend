from dataclasses import asdict
from typing import NamedTuple

from flask import abort, send_file
from fsd_utils import generate_text_of_application

from assess.assessments.helpers import download_file, generate_csv_of_application
from assess.assessments.models.full_application import (
    FullApplicationPdfContext,
    generate_full_application_pdf,
)
from assess.services.models.fund import Fund
from assess.services.models.round import Round


class ApplicationFileRepresentationArgs(NamedTuple):
    fund: Fund
    round: Round
    short_id: str
    form_name_to_title_map: dict
    question_to_answer: dict
    application_json: dict
    all_uploaded_documents: list[dict]


def _generate_text_of_application(args: ApplicationFileRepresentationArgs):
    fund_round_name = f"{args.fund.name} {args.round.title}"
    text = generate_text_of_application(args.question_to_answer, fund_round_name)
    return download_file(text, "text/plain", f"{args.short_id}_answers.txt")


def _generate_csv_of_application(args: ApplicationFileRepresentationArgs):
    fund_round_name = f"{args.fund.name} {args.round.title}"
    csv = generate_csv_of_application(args.question_to_answer, args.fund, args.application_json, fund_round_name)
    return download_file(csv, "text/csv", f"{args.short_id}_answers.csv")


def _generate_pdf_of_application(args: ApplicationFileRepresentationArgs):
    context = FullApplicationPdfContext.from_data(args)
    if pdf_file := generate_full_application_pdf(asdict(context)):
        pdf_file.seek(0)
        return send_file(
            pdf_file,
            download_name=f"{args.short_id}_answers.pdf",
            as_attachment=True,
        )


FILE_GENERATORS = {
    "txt": _generate_text_of_application,
    "csv": _generate_csv_of_application,
    "pdf": _generate_pdf_of_application,
}


def generate_file_content(args: ApplicationFileRepresentationArgs, file_type: str):
    """
    Generate the content of an application file based on the provided file type.

    This function will create either a file representation of an application,
    depending on the `file_type` provided.

    Args:
        args (ApplicationFileRepresentationArgs): Arguments containing application details like
                                                  fund details, round, short id, form name to title map,
                                                  question to answer mappings, application JSON data,
                                                  and all uploaded documents.
        file_type (str): The type of file to generate. Valid values are 'txt', 'csv', and 'pdf'.

    Returns:
        A file content in the specified format, response for a flask request.

    Raises:
        404: If the provided `file_type` is not supported.

    Example:
        >>> args = ApplicationFileRepresentationArgs(...)
        >>> generate_file_content(args, 'txt')
        [Generates and returns the text representation of the application]
    """
    if file_generator := FILE_GENERATORS.get(file_type):
        return file_generator(args)

    abort(404)
