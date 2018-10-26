from django.contrib.admin import AdminSite
from django.contrib.auth import admin as auth_admin
from django.urls import path


class FinukeAdmin(AdminSite):
    site_header = 'Finuke'
    index_template = "admin/custom_index.html"

    def get_urls(self):
        urls = super().get_urls()

        from votes.admin import ResultsAdminView
        myurls = [
            path('results/', self.admin_view(ResultsAdminView.as_view()), name='results')
        ]

        return myurls + urls


admin_site = FinukeAdmin(name='finuke_admin')


# register auth model admins
admin_site.register(auth_admin.Group, auth_admin.GroupAdmin)
admin_site.register(auth_admin.User, auth_admin.UserAdmin)
