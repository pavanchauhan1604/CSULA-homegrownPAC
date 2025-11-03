select distinct site_user.first_name,
       site_user.last_name,
       site_user.email,
        site_user.employee_id
from site_user
join site_assignment on site_user.employee_id = site_assignment.user_id
join drupal_site on site_assignment.site_id = drupal_site.id
join drupal_pdf_files on drupal_site.id = drupal_pdf_files.drupal_site_id
order by site_user.first_name, site_user.last_name


