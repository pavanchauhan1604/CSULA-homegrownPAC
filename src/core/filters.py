import re

node_check = re.compile(r".*./node/.*")
index_check = re.compile(r".*./index.php/.*")

def check_for_node(parent_uri):
    return True if (node_check.match(parent_uri) or index_check.match(parent_uri)) is not None else False



def is_high_priority(data):
    """Return True if the PDF requires urgent attention for ADA Title II compliance.

    High priority means the document is meaningfully inaccessible — a screen reader
    user would be unable to use it or would have a severely degraded experience.

    Criteria (any one is sufficient):
      - Untagged: screen readers cannot navigate content or reading order at all.
      - Image Only: no text layer; content is completely inaccessible without OCR.
      - >9 failed checks/page: systematic accessibility breakdowns across most content
        (missing alt text, broken structure, unlabelled fields etc.). Data-calibrated
        against 5,573 CSULA PDFs — the distribution peaks at 4-9/page; 10+ indicates
        a document with pervasive structural problems.
      - Form with >3 failed checks/page: interactive forms must be fully accessible
        under ADA; any significant violation blocks assistive-technology users.

    Auto-pass: approved_pdf_exporter bypasses the violation thresholds (the tool
    guarantees PDF/UA output so minor residual counts are false positives).
    """
    if not isinstance(data, dict):
        data = dict(data._asdict())

    if data['tagged'] == 0:
        return True
    if data['pdf_text_type'] == 'Image Only':
        return True
    if data['approved_pdf_exporter']:
        return False

    epp = round(int(data['failed_checks']) / int(data['page_count'])) if int(data['page_count']) > 0 else 0
    if epp > 9:
        return True
    if data['has_form'] == 1 and epp > 3:
        return True
    return False


def get_priority_level(data):
    """Categorise a PDF as 'high', 'medium', or 'low' priority.

    Returns (priority_level, hex_color, label).

    High   (#8B0000) — same criteria as is_high_priority(): untagged, Image Only,
                       >9 failed checks/page, or form with >3 failed checks/page.
    Medium (#FF8C00) — tagged, no form issues, but 4–9 failed checks/page.
                       Real WCAG violations (missing alt text, heading gaps) but
                       the document is still screen-reader-navigable.
    Low    (#006400) — tagged, 0–3 failed checks/page, or approved exporter.
    """
    if not isinstance(data, dict):
        data = dict(data._asdict())

    epp = round(int(data['failed_checks']) / int(data['page_count'])) if int(data['page_count']) > 0 else 0

    # High priority
    if data['tagged'] == 0:
        return ('high', '#8B0000', 'High')
    if data['pdf_text_type'] == 'Image Only':
        return ('high', '#8B0000', 'High')
    if epp > 9:
        return ('high', '#8B0000', 'High')
    if data['has_form'] == 1 and epp > 3:
        return ('high', '#8B0000', 'High')

    # Approved exporter → low regardless of residual violation count
    if data['approved_pdf_exporter']:
        return ('low', '#006400', 'Low')

    # Medium priority — tagged but meaningful violations
    if epp >= 4:
        return ('medium', '#FF8C00', 'Medium')

    return ('low', '#006400', 'Low')