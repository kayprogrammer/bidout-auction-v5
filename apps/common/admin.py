from django.contrib import admin
from django.utils.safestring import mark_safe

from apps.common.models import File, GuestUser

admin.site.site_header = mark_safe(
    '<strong style="font-weight:bold;">B.A V5 ADMIN</strong>'
)


class FileAdmin(admin.ModelAdmin):
    list_display = ("id", "resource_type")
    list_filter = ("id", "resource_type")


class GuestUserAdmin(admin.ModelAdmin):
    list_display = ("id",)
    list_filter = ("id",)


admin.site.register(File, FileAdmin)
admin.site.register(GuestUser, GuestUserAdmin)
