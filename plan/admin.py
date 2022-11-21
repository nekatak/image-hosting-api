from django.contrib import admin

from . import models


class PlanToImageSpecificationsInline(admin.TabularInline):
    model = models.Plan.includes.through
    extra = 0


class PlanAdmin(admin.ModelAdmin):
    inlines = [
        PlanToImageSpecificationsInline,
    ]


admin.site.register(models.Plan, PlanAdmin)
admin.site.register(models.ImageSpecifications)
