SELECT domain_name, COUNT(drupal_pdf_files.drupal_site_id) AS pdf_count
FROM drupal_site
         JOIN drupal_pdf_files ON drupal_site.id = drupal_pdf_files.drupal_site_id
WHERE drupal_pdf_files.parent_uri NOT LIKE '%/node/%'
  AND drupal_pdf_files.parent_uri NOT LIKE '%/index.php/%'
  AND drupal_pdf_files.pdf_returns_404 = 0
  AND drupal_pdf_files.parent_returns_404 = 0
  AND removed is FALSE
GROUP BY domain_name;