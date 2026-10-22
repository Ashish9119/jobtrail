from django import forms
from django.utils import timezone

from .models import JobApplication


class JobApplicationForm(forms.ModelForm):
    """The owner is never a form field; views set it from request.user."""

    class Meta:
        model = JobApplication
        fields = [
            "company",
            "job_title",
            "location",
            "applied_date",
            "status",
            "salary",
            "job_url",
            "interviewed",
            "notes",
        ]
        labels = {
            "applied_date": "Date applied",
            "job_url": "Job posting URL",
            "interviewed": "Reached an interview stage",
        }
        widgets = {
            "applied_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)

    def clean_applied_date(self):
        applied = self.cleaned_data["applied_date"]
        if applied > timezone.localdate():
            raise forms.ValidationError("The application date can't be in the future.")
        return applied


class ApplicationFilterForm(forms.Form):
    SORT_CHOICES = [
        ("-applied_date", "Newest first"),
        ("applied_date", "Oldest first"),
        ("company", "Company, A to Z"),
        ("-salary", "Highest salary"),
    ]

    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"type": "search", "placeholder": "Company, title, location or notes"}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *JobApplication.Status.choices],
    )
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES, label="Sort by")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
