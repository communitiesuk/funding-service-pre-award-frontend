from io import BytesIO
from unittest.mock import patch

import pytest

from assess.assessments.pdf_generator import PDFCreationException, generate_pdf


@pytest.fixture
def mock_render_template():
    with patch("assess.assessments.pdf_generator._render_template") as mock:
        mock.return_value = "<html><body>Test PDF</body></html>"
        yield mock


@pytest.fixture
def mock_convert_html_to_pdf_error():
    with patch("assess.assessments.pdf_generator._convert_html_to_pdf") as mock:
        mock.side_effect = PDFCreationException("Mocked Error")
        yield mock


@pytest.fixture
def mock_convert_html_to_pdf_success():
    with patch("assess.assessments.pdf_generator._convert_html_to_pdf") as mock:
        yield mock


def test_generate_pdf_successful(mock_render_template, mock_convert_html_to_pdf_success):
    template_path = "path/to/valid/template.html"
    context = {"key": "value"}

    pdf_file = generate_pdf(template_path, context)

    mock_render_template.assert_called_once_with(template_path, context)
    mock_convert_html_to_pdf_success.assert_called_once()
    assert isinstance(pdf_file, BytesIO)


def test_generate_pdf_with_error(mock_render_template, mock_convert_html_to_pdf_error):
    template_path = "path/to/invalid/template.html"
    context = {"key": "value"}

    with pytest.raises(PDFCreationException, match="Mocked Error"):
        generate_pdf(template_path, context)

    mock_render_template.assert_called_once_with(template_path, context)
    mock_convert_html_to_pdf_error.assert_called_once()
