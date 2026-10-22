from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        INTERVIEW = "interview", "Interviewing"
        OFFER = "offer", "Offer"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    # Statuses that imply the application got past the screening stage.
    INTERVIEW_STAGES = (Status.INTERVIEW, Status.OFFER)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    company = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    applied_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    salary = models.PositiveIntegerField(null=True, blank=True, help_text="Annual salary, if listed or offered.")
    job_url = models.URLField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    # Status only records where an application is now. This records whether it ever
    # reached an interview, so a later rejection still counts toward the interview rate.
    interviewed = models.BooleanField(
        default=False,
        help_text="Set automatically when the status is Interviewing or Offer.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="app_user_status_idx"),
            models.Index(fields=["user", "applied_date"], name="app_user_applied_idx"),
        ]

    def __str__(self):
        return f"{self.job_title} at {self.company}"

    def get_absolute_url(self):
        return reverse("applications:detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if self.status in self.INTERVIEW_STAGES:
            self.interviewed = True
        super().save(*args, **kwargs)
