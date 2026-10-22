from django.contrib import admin

from .models import JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job_title", "company", "user", "status", "applied_date")
    list_filter = ("status", "applied_date")
    search_fields = ("company", "job_title", "location", "user__username")
