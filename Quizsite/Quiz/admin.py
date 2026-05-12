from django.contrib import admin

from .models import UploadedMaterial

admin.site.site_header = "Администрирование тестов"
admin.site.site_title = "Администрирование тестов"
admin.site.index_title = "Панель управления"


@admin.register(UploadedMaterial)
class UploadedMaterialAdmin(admin.ModelAdmin):
    list_display = ("material", "uploaded_at")
    readonly_fields = ("uploaded_at",)
