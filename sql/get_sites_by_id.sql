SELECT
    site_user.employee_id,
    site_user.first_name,
    site_user.last_name,
    site_user.email,
    site_user.is_manager,
    drupal_site.domain_name,
    drupal_site.page_title,
    drupal_site.security_group_name,
    drupal_site.box_folder,
    site_assignment.id AS assignment_id
FROM
    site_user
        JOIN
    site_assignment ON site_user.employee_id = site_assignment.user_id
        JOIN
    drupal_site ON site_assignment.site_id = drupal_site.id
WHERE
    site_user.employee_id = '912793588';