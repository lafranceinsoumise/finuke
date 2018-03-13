from django.contrib.admin import AdminSite
from django.contrib.auth import admin as auth_admin

class FinukeAdmin(AdminSite):
    site_header = 'Finuke'


admin_site = FinukeAdmin(name='finuke_admin')


# register auth model admins
admin_site.register(auth_admin.Group, auth_admin.GroupAdmin)
admin_site.register(auth_admin.User, auth_admin.UserAdmin)
