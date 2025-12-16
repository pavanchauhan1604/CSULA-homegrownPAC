SELECT


    site_user.first_name,
    site_user.last_name,
    site_user.email,

    count(pdf_report.pdf_hash) AS total_files,
    SUM(pdf_report.failed_checks / NULLIF(pdf_report.page_count, 0)) AS total_rank
FROM
    drupal_pdf_files
        JOIN
    drupal_site ON drupal_pdf_files.drupal_site_id = drupal_site.id
        JOIN
    pdf_report ON drupal_pdf_files.file_hash = pdf_report.pdf_hash
        JOIN
    site_assignment ON site_assignment.site_id = drupal_site.id
        JOIN
    site_user ON site_assignment.user_id = site_user.employee_id
WHERE parent_uri NOT LIKE '%/node/%' AND parent_uri NOT LIKE '%/index.php/%'

GROUP BY
    site_user.email
ORDER BY
    total_rank DESC
