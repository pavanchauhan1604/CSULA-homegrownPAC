WITH ranked AS (
    SELECT
        d.id,
        d.pdf_uri,
        d.parent_uri,
        d.file_hash,
        d.scanned_date,
        d.removed,
        ROW_NUMBER() OVER (
            PARTITION BY d.pdf_uri, d.parent_uri
            ORDER BY COALESCE(d.scanned_date, '0000-01-01T00:00:00') DESC, d.id DESC
            ) AS rn,
        COUNT(*) OVER (PARTITION BY d.pdf_uri, d.parent_uri) AS dup_count
    FROM drupal_pdf_files d
             JOIN drupal_site s ON d.drupal_site_id = s.id
    WHERE s.domain_name = 'socwork.sfsu.edu'
)
SELECT id, pdf_uri, parent_uri, file_hash, scanned_date, removed
FROM ranked
WHERE dup_count > 1
  AND rn > 1                     -- exclude the single most-recent per pair
ORDER BY pdf_uri, parent_uri, scanned_date;