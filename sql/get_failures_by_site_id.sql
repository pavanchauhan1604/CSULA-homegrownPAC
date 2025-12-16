SELECT
    failure.site_id,
    failure.error_date,
    failure.error_message,
    COALESCE(drupal_pdf_files.pdf_uri, failure.pdf_id) as pdf_uri,
    drupal_pdf_files.parent_uri
FROM failure
LEFT JOIN drupal_pdf_files ON failure.pdf_id = drupal_pdf_files.id
WHERE failure.site_id = '{site_id}'




