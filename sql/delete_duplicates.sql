DELETE FROM drupal_pdf_files
WHERE id IN (
    SELECT id FROM (
                       SELECT d.id,
                              ROW_NUMBER() OVER (
                                  PARTITION BY d.pdf_uri, d.parent_uri, d.file_hash
                                  ORDER BY d.scanned_date ASC
                                  ) AS rn
                       FROM drupal_pdf_files d
                                JOIN drupal_site s ON d.drupal_site_id = s.id
                       WHERE s.domain_name = '{site_name}'
                   ) sub
    WHERE rn > 1
);
