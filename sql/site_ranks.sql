SELECT
    drupal_site.domain_name,
    count(drupal_pdf_files.pdf_uri) as pdfs_on_site,
    SUM(pdf_report.failed_checks / NULLIF(pdf_report.page_count, 0)) AS total_rank,
    GROUP_CONCAT(DISTINCT site_user.email) AS site_users
FROM
    drupal_pdf_files
        JOIN
    drupal_site ON drupal_pdf_files.drupal_site_id = drupal_site.id
        JOIN
    pdf_report ON drupal_pdf_files.file_hash = pdf_report.pdf_hash
        JOIN
    site_assignment ON drupal_site.id = site_assignment.site_id
        join site_user on site_assignment.user_id = site_user.employee_id
WHERE parent_uri NOT LIKE '%/node/%' AND parent_uri NOT LIKE '%/index.php/%'

GROUP BY
    drupal_site.domain_name
ORDER BY
    total_rank DESC
