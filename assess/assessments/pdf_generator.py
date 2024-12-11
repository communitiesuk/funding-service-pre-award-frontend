from io import BytesIO

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa


def _render_template(template_path: str, context) -> str:
    env = Environment(loader=FileSystemLoader("."), autoescape=True)
    template = env.get_template(template_path)
    return template.render(context)


class PDFCreationException(Exception):
    pass


def _convert_html_to_pdf(html_content: str, pdf_file: BytesIO) -> bool:
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
    if pisa_status.err:
        raise PDFCreationException(f"Error while converting HTML to PDF: {str(pisa_status.err)}")


def generate_pdf(template_path: str, context) -> BytesIO:
    """
    Generates a PDF from a given Jinja2 HTML template and its context.

    Args:
        template_path (str): The path to the Jinja2 HTML template to be rendered.
        context (dict): A dictionary containing the context variables for the template.

    Returns:
        BytesIO: A binary stream containing the generated PDF content.

    Raises:
        PDFCreationException: If there's an error during the conversion of HTML to PDF.

    Example:
        To use this function with a specific template, you can use `functools.partial`:

        ```python
        from functools import partial

        generate_full_application_pdf = partial(
            generate_pdf, "app/pdf/templates/full_application.html"
        )
        ```

        Calling `generate_full_application_pdf` with the context will now render
        the "full_application.html" template and convert it to a PDF.
    """
    pdf_file = BytesIO()
    html_content = _render_template(template_path, context)
    _convert_html_to_pdf(html_content, pdf_file)
    return pdf_file
