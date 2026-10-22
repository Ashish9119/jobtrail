from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from . import analytics
from .forms import ApplicationFilterForm, JobApplicationForm
from .models import JobApplication

# "-pk" is a final tie-breaker so pagination never repeats or skips rows.
SORTS = {
    "-applied_date": ("-applied_date", "-created_at", "-pk"),
    "applied_date": ("applied_date", "created_at", "pk"),
    "company": (Lower("company"), "-pk"),
    "-salary": (F("salary").desc(nulls_last=True), "-pk"),
}


class OwnedApplicationMixin(LoginRequiredMixin):
    """Scope every lookup to the signed-in user.

    Other people's records simply don't exist as far as these views are concerned,
    so they get a 404 rather than a 403 that would confirm the record exists.
    """

    model = JobApplication

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "applications/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = JobApplication.objects.filter(user=self.request.user)
        trend = analytics.monthly_trend(queryset)
        context.update(
            totals=analytics.status_totals(queryset),
            metrics=analytics.conversion_metrics(queryset),
            trend=trend,
            chart_data={
                "labels": [row["label"] for row in trend],
                "applications": [row["applications"] for row in trend],
                "interviews": [row["interviews"] for row in trend],
            },
            recent=queryset[:5],
        )
        return context


class ApplicationListView(OwnedApplicationMixin, ListView):
    template_name = "applications/list.html"
    context_object_name = "applications"
    paginate_by = 10

    def get_filter_data(self):
        if not hasattr(self, "_filter_form"):
            self._filter_form = ApplicationFilterForm(self.request.GET)
        form = self._filter_form
        return form, (form.cleaned_data if form.is_valid() else {})

    def get_queryset(self):
        queryset = super().get_queryset()
        _, data = self.get_filter_data()

        term = data.get("q", "").strip()
        if term:
            queryset = queryset.filter(
                Q(company__icontains=term)
                | Q(job_title__icontains=term)
                | Q(location__icontains=term)
                | Q(notes__icontains=term)
            )
        if data.get("status"):
            queryset = queryset.filter(status=data["status"])

        return queryset.order_by(*SORTS[data.get("sort") or "-applied_date"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form, data = self.get_filter_data()
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update(
            filter_form=form,
            querystring=params.urlencode(),
            is_filtered=bool(data.get("q") or data.get("status")),
        )
        return context


class ApplicationDetailView(OwnedApplicationMixin, DetailView):
    template_name = "applications/detail.html"


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = "applications/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add application"
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Application added.")
        return response


class ApplicationUpdateView(OwnedApplicationMixin, UpdateView):
    form_class = JobApplicationForm
    template_name = "applications/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit application"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Changes saved.")
        return response


class ApplicationDeleteView(OwnedApplicationMixin, DeleteView):
    template_name = "applications/confirm_delete.html"
    success_url = reverse_lazy("applications:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Application deleted.")
        return response
