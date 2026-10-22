import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="JobApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company", models.CharField(max_length=200)),
                ("job_title", models.CharField(max_length=200)),
                ("location", models.CharField(blank=True, max_length=200)),
                ("applied_date", models.DateField(default=django.utils.timezone.localdate)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("applied", "Applied"),
                            ("screening", "Screening"),
                            ("interview", "Interviewing"),
                            ("offer", "Offer"),
                            ("rejected", "Rejected"),
                            ("withdrawn", "Withdrawn"),
                        ],
                        default="applied",
                        max_length=20,
                    ),
                ),
                (
                    "salary",
                    models.PositiveIntegerField(blank=True, help_text="Annual salary, if listed or offered.", null=True),
                ),
                ("job_url", models.URLField(blank=True, max_length=500)),
                ("notes", models.TextField(blank=True)),
                (
                    "interviewed",
                    models.BooleanField(
                        default=False,
                        help_text="Set automatically when the status is Interviewing or Offer.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-applied_date", "-created_at"]},
        ),
        migrations.AddIndex(
            model_name="jobapplication",
            index=models.Index(fields=["user", "status"], name="app_user_status_idx"),
        ),
        migrations.AddIndex(
            model_name="jobapplication",
            index=models.Index(fields=["user", "applied_date"], name="app_user_applied_idx"),
        ),
    ]
