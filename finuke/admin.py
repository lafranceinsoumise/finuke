from django.contrib.admin import AdminSite


class FinukeAdmin(AdminSite):
    site_header = 'Finuke'


admin_site = FinukeAdmin(name='finuke_admin')
