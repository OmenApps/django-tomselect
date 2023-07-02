from django.contrib import admin

from .models import Edition, Magazine


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    pass


@admin.register(Magazine)
class MagazineAdmin(admin.ModelAdmin):
    pass
