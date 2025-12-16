SELECT
    drupal_pdf_files.pdf_uri,
    drupal_pdf_files.parent_uri,
    drupal_pdf_files.scanned_date,
    drupal_pdf_files.file_hash,
    drupal_site.domain_name,
    drupal_site.page_title,
    drupal_site.security_group_name,
    pdf_report.violations,
    pdf_report.failed_checks,
    pdf_report.tagged,
    pdf_report.check_for_image_only,
    pdf_report.pdf_text_type,
    pdf_report.title_set,
    pdf_report.language_set,
    pdf_report.page_count,
    site_assignment.user_id,
    site_user.employee_id
FROM
    drupal_pdf_files
        JOIN
    drupal_site ON drupal_pdf_files.drupal_site_id = drupal_site.id
        JOIN
    pdf_report ON drupal_pdf_files.file_hash = pdf_report.pdf_hash
        JOIN
    site_assignment on drupal_site.id = site_assignment.site_id
        JOIN
    site_user on site_assignment.user_id = site_user.employee_id


WHERE parent_uri NOT LIKE '%/node/%' AND parent_uri NOT LIKE '%/index.php/%' AND
      site_assignment.user_id = '{employee_id}'