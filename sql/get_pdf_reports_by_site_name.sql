SELECT
    drupal_pdf_files.pdf_uri,
    drupal_pdf_files.parent_uri,
    drupal_pdf_files.scanned_date,
    drupal_pdf_files.file_hash,
    drupal_site.domain_name,
    drupal_site.security_group_name,
    drupal_pdf_files.drupal_site_id,
    pdf_report.violations,
    pdf_report.failed_checks,
    pdf_report.tagged,
    pdf_report.pdf_text_type,
    pdf_report.title_set,
    pdf_report.language_set,
    pdf_report.page_count,
    pdf_report.has_form,
    pdf_report.approved_pdf_exporter,
    drupal_site.box_folder,
    drupal_pdf_files.parent_returns_404,
    drupal_pdf_files.pdf_returns_404

FROM
    drupal_pdf_files
        JOIN
    drupal_site ON drupal_pdf_files.drupal_site_id = drupal_site.id
        JOIN
    pdf_report ON drupal_pdf_files.file_hash = pdf_report.pdf_hash

WHERE parent_uri NOT LIKE '%/node/%' AND parent_uri NOT LIKE '%/index.php/%'
  AND parent_returns_404 is FALSE
  AND pdf_returns_404 is FALSE
  AND drupal_site.domain_name = '{site_name}';
