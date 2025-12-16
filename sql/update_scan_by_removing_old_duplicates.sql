WITH ranked AS (
    SELECT
        d.id,
        ROW_NUMBER() OVER (
            PARTITION BY d.pdf_uri, d.parent_uri
            ORDER BY COALESCE(d.scanned_date, '0000-01-01T00:00:00') DESC, d.id DESC
            ) AS rn,
        COUNT(*) OVER (PARTITION BY d.pdf_uri, d.parent_uri) AS dup_count
    FROM drupal_pdf_files d
             JOIN drupal_site s ON d.drupal_site_id = s.id
    WHERE s.domain_name = '{site_name}'
)
UPDATE drupal_pdf_files
SET removed = 1
WHERE id IN (
    SELECT id
    FROM ranked
    WHERE dup_count > 1
      AND rn > 1   -- all but the most recent per (pdf_uri, parent_uri)
);