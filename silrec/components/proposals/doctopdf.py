import io
import os
import logging
import tempfile

from django.conf import settings

from docxtpl import DocxTemplate

logger = logging.getLogger(__name__)


def render_report_pdf(report, df, parameters):
    """
    Render a SQL report as PDF using the current docx template for the report.

    Args:
        report: SQLReport instance
        df: pandas DataFrame with query results
        parameters: dict of filter parameters used in the query

    Returns:
        bytes of the generated PDF file, or None if no template is available
    """
    template = report.templates.filter(is_current=True).first()
    if not template:
        logger.warning(f"No current template found for report {report.id} ({report.name})")
        return None

    template_path = template.template_file.path
    if not os.path.isfile(template_path):
        logger.error(f"Template file not found on disk: {template_path}")
        return None

    try:
        doc = DocxTemplate(template_path)

        # Build context from DataFrame columns + parameters
        context = {
            'report_name': report.name,
            'report_type': report.get_report_type_display(),
            'parameters': parameters,
            'rows': df.to_dict('records'),
            'columns': list(df.columns),
            'row_count': len(df),
        }
        # Add each column as a top-level list for direct iteration in templates
        for col in df.columns:
            context[col] = df[col].tolist()

        doc.render(context)

        # Save to temp docx then convert to PDF
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
            tmp_docx_path = tmp_docx.name
            doc.save(tmp_docx_path)

        try:
            pdf_bytes = _convert_docx_to_pdf(tmp_docx_path)
            return pdf_bytes
        finally:
            try:
                os.unlink(tmp_docx_path)
            except OSError:
                pass

    except Exception as e:
        logger.error(f"Error rendering report PDF for {report.name}: {e}", exc_info=True)
        return None


def _convert_docx_to_pdf(docx_path):
    """
    Convert a .docx file to PDF bytes.

    Uses libreoffice headless conversion. Falls back to a HTML-based PDF
    if libreoffice is not available.
    """
    import subprocess

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', tmpdir, docx_path,
                ],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                base = os.path.splitext(os.path.basename(docx_path))[0]
                pdf_path = os.path.join(tmpdir, f'{base}.pdf')
                if os.path.isfile(pdf_path):
                    with open(pdf_path, 'rb') as f:
                        return f.read()

        logger.warning("libreoffice PDF conversion failed or unavailable; falling back to simple PDF")
        return _fallback_pdf_from_docx(docx_path)

    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning(f"libreoffice not available or timed out ({e}); falling back to simple PDF")
        return _fallback_pdf_from_docx(docx_path)


def _fallback_pdf_from_docx(docx_path):
    """
    Fallback: convert the docx to a simple PDF by reading text content
    and placing it on PDF pages. This loses formatting but guarantees output.
    """
    from docx import Document as DocxReader
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    doc = DocxReader(docx_path)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    p.setFont("Helvetica", 10)
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 50
        p.drawString(50, y, text[:120])
        y -= 15

    p.save()
    buffer.seek(0)
    return buffer.getvalue()
