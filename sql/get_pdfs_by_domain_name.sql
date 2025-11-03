SELECT
    drupal_pdf_files.id,
    drupal_pdf_files.pdf_uri,
    drupal_pdf_files.parent_uri

FROM
    drupal_pdf_files
        JOIN
    drupal_site ON drupal_pdf_files.drupal_site_id = drupal_site.id
WHERE parent_uri NOT LIKE '%/node/%' AND parent_uri NOT LIKE '%/index.php/%' AND
    drupal_site.domain_name = 'procurement.sfsu.edu';