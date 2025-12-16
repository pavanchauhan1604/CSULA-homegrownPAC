import re

node_check = re.compile(r".*./node/.*")
index_check = re.compile(r".*./index.php/.*")

def check_for_node(parent_uri):
    return True if (node_check.match(parent_uri) or index_check.match(parent_uri)) is not None else False



def is_high_priority(data):
    """Determine if a PDF requires review based on accessibility flags."""
    if not isinstance(data, dict):
        data = dict(data._asdict())

    if data['tagged'] == 0:
        return True
    if data['pdf_text_type'] == 'Image Only':
        return True
    if data['approved_pdf_exporter']:
        return False
    if int(data['page_count']) > 0 and round(int(data['failed_checks']) / int(data['page_count'])) > 20:
        return True
    if data['has_form'] == 1 and int(data['page_count']) > 0 and round(int(data['failed_checks']) / int(data['page_count'])) > 3:
        return True
    return False


def get_priority_level(data):
    """
    Categorize PDFs into priority levels: 'high', 'medium', or 'low'.
    Returns tuple of (priority_level, color_code, color_name)
    """
    if not isinstance(data, dict):
        data = dict(data._asdict())
    
    # High priority criteria
    if data['tagged'] == 0:
        return ('high', '#8B0000', 'High')  # Dark red - untagged
    if data['pdf_text_type'] == 'Image Only':
        return ('high', '#8B0000', 'High')  # Dark red - image only
    if int(data['page_count']) > 0 and round(int(data['failed_checks']) / int(data['page_count'])) > 20:
        return ('high', '#8B0000', 'High')  # Dark red - very high violations per page
    if data['has_form'] == 1 and int(data['page_count']) > 0 and round(int(data['failed_checks']) / int(data['page_count'])) > 3:
        return ('high', '#8B0000', 'High')  # Dark red - form with high violations
    
    # If approved exporter, it's low priority
    if data['approved_pdf_exporter']:
        return ('low', '#006400', 'Low')  # Dark green - approved exporter
    
    # Medium priority criteria - has violations but not critical
    violations_per_page = 0
    if int(data['page_count']) > 0:
        violations_per_page = round(int(data['failed_checks']) / int(data['page_count']))
    
    if violations_per_page >= 5:
        return ('medium', '#FF8C00', 'Medium')  # Dark orange - moderate violations
    elif violations_per_page > 0:
        return ('low', '#006400', 'Low')  # Dark green - low violations
    
    return ('low', '#006400', 'Low')  # Dark green - default