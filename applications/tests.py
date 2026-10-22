from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import analytics
from .forms import JobApplicationForm
from .models import JobApplication

User = get_user_model()


def make_app(user, **overrides):
    fields = {"company": "Acme", "job_title": "Engineer", "applied_date": timezone.localdate()}
    fields.update(overrides)
    return JobApplication.objects.create(user=user, **fields)


def valid_payload(**overrides):
    data = {
        "company": "Globex",
        "job_title": "Analyst",
        "location": "Remote",
        "applied_date": timezone.localdate().isoformat(),
        "status": "applied",
        "salary": "70000",
        "job_url": "https://example.com/job",
        "notes": "Referred by a friend",
    }
    data.update(overrides)
    return data


class OwnershipTests(TestCase):
    """Phase 4: one user must never see or change another user's applications."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user("alice", password="alice-pass-123")
        cls.bob = User.objects.create_user("bob", password="bob-pass-123")
        cls.alice_app = make_app(cls.alice, company="Alice Co", notes="alice note")
        cls.bob_app = make_app(cls.bob, company="Bob Co", notes="secret bob note", status="interview")

    def setUp(self):
        self.client.force_login(self.alice)

    # --- anonymous access ---
    def test_anonymous_users_are_sent_to_login(self):
        self.client.logout()
        urls = [
            reverse("applications:dashboard"),
            reverse("applications:list"),
            reverse("applications:create"),
            reverse("applications:detail", args=[self.alice_app.pk]),
            reverse("applications:update", args=[self.alice_app.pk]),
            reverse("applications:delete", args=[self.alice_app.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}", fetch_redirect_response=False)

    def test_anonymous_post_changes_nothing(self):
        self.client.logout()
        self.client.post(reverse("applications:delete", args=[self.alice_app.pk]))
        self.client.post(reverse("applications:update", args=[self.alice_app.pk]), valid_payload())
        self.client.post(reverse("applications:create"), valid_payload())
        self.assertEqual(JobApplication.objects.count(), 2)
        self.alice_app.refresh_from_db()
        self.assertEqual(self.alice_app.company, "Alice Co")

    # --- reading ---
    def test_list_only_shows_own_applications(self):
        response = self.client.get(reverse("applications:list"))
        self.assertContains(response, "Alice Co")
        self.assertNotContains(response, "Bob Co")

    def test_detail_of_another_users_application_is_404(self):
        response = self.client.get(reverse("applications:detail", args=[self.bob_app.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_view_their_own_detail(self):
        self.client.force_login(self.bob)
        response = self.client.get(reverse("applications:detail", args=[self.bob_app.pk]))
        self.assertEqual(response.status_code, 200)

    # --- modifying ---
    def test_cannot_open_or_submit_edit_form_for_another_users_application(self):
        url = reverse("applications:update", args=[self.bob_app.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, valid_payload(company="Hijacked")).status_code, 404)
        self.bob_app.refresh_from_db()
        self.assertEqual(self.bob_app.company, "Bob Co")

    def test_cannot_delete_another_users_application(self):
        url = reverse("applications:delete", args=[self.bob_app.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(JobApplication.objects.filter(pk=self.bob_app.pk).exists())

    def test_missing_and_foreign_records_look_identical(self):
        missing = self.client.get(reverse("applications:detail", args=[999999]))
        foreign = self.client.get(reverse("applications:detail", args=[self.bob_app.pk]))
        self.assertEqual(missing.status_code, foreign.status_code)

    def test_create_ignores_a_user_field_in_the_post(self):
        self.client.post(reverse("applications:create"), valid_payload(user=self.bob.pk))
        created = JobApplication.objects.get(company="Globex")
        self.assertEqual(created.user, self.alice)

    # --- search, filters, pagination, dashboard must not leak either ---
    def test_search_does_not_leak_other_users_data(self):
        response = self.client.get(reverse("applications:list"), {"q": "secret"})
        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        response = self.client.get(reverse("applications:list"), {"q": "Bob"})
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_status_filter_does_not_leak_other_users_data(self):
        response = self.client.get(reverse("applications:list"), {"status": "interview"})
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_pagination_never_includes_other_users_rows(self):
        for i in range(25):
            make_app(self.alice, company=f"Alice Extra {i}")
        seen = []
        for page in (1, 2, 3):
            response = self.client.get(reverse("applications:list"), {"page": page})
            self.assertEqual(response.status_code, 200)
            seen.extend(response.context["applications"])
        self.assertEqual(len(seen), 26)
        self.assertTrue(all(app.user_id == self.alice.pk for app in seen))
        self.assertEqual(len({app.pk for app in seen}), 26)

    def test_dashboard_only_counts_own_applications(self):
        for _ in range(4):
            make_app(self.bob, status="offer")
        response = self.client.get(reverse("applications:dashboard"))
        self.assertEqual(response.context["metrics"]["total"], 1)
        self.assertEqual(response.context["metrics"]["offers"], 0)
        self.assertEqual(sum(row["applications"] for row in response.context["trend"]), 1)


class CrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("sam", password="sam-pass-123")
        self.client.force_login(self.user)

    def test_create_read_update_delete(self):
        response = self.client.post(reverse("applications:create"), valid_payload())
        application = JobApplication.objects.get(company="Globex")
        self.assertRedirects(response, application.get_absolute_url())

        self.assertContains(self.client.get(application.get_absolute_url()), "Analyst")

        self.client.post(reverse("applications:update", args=[application.pk]), valid_payload(status="offer"))
        application.refresh_from_db()
        self.assertEqual(application.status, "offer")

        response = self.client.post(reverse("applications:delete", args=[application.pk]))
        self.assertRedirects(response, reverse("applications:list"))
        self.assertFalse(JobApplication.objects.filter(pk=application.pk).exists())

    def test_search_status_filter_and_sort(self):
        make_app(self.user, company="Initech", job_title="Designer", status="rejected", salary=50000)
        make_app(self.user, company="Hooli", job_title="Engineer", status="applied", salary=90000)
        url = reverse("applications:list")

        names = [a.company for a in self.client.get(url, {"q": "design"}).context["applications"]]
        self.assertEqual(names, ["Initech"])

        names = [a.company for a in self.client.get(url, {"status": "applied"}).context["applications"]]
        self.assertEqual(names, ["Hooli"])

        names = [a.company for a in self.client.get(url, {"sort": "-salary"}).context["applications"]]
        self.assertEqual(names, ["Hooli", "Initech"])

    def test_invalid_filter_values_are_ignored(self):
        make_app(self.user)
        response = self.client.get(reverse("applications:list"), {"status": "nonsense", "sort": "drop table"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_pagination_keeps_filters_in_links(self):
        for i in range(12):
            make_app(self.user, company=f"Match {i}")
        response = self.client.get(reverse("applications:list"), {"q": "Match"})
        self.assertContains(response, "q=Match&amp;page=2")

    def test_future_application_date_is_rejected(self):
        future = (timezone.localdate() + timedelta(days=3)).isoformat()
        form = JobApplicationForm(valid_payload(applied_date=future))
        self.assertFalse(form.is_valid())
        self.assertIn("applied_date", form.errors)


class ModelTests(TestCase):
    def test_interview_and_offer_statuses_mark_interviewed(self):
        user = User.objects.create_user("mo", password="mo-pass-123")
        self.assertFalse(make_app(user, status="applied").interviewed)
        self.assertTrue(make_app(user, status="interview").interviewed)
        self.assertTrue(make_app(user, status="offer").interviewed)

    def test_interviewed_survives_a_later_rejection(self):
        user = User.objects.create_user("mo", password="mo-pass-123")
        application = make_app(user, status="interview")
        application.status = "rejected"
        application.save()
        application.refresh_from_db()
        self.assertTrue(application.interviewed)


class AnalyticsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana", password="ana-pass-123")

    def test_status_totals_include_empty_statuses(self):
        make_app(self.user, status="applied")
        make_app(self.user, status="applied")
        make_app(self.user, status="offer")
        totals = {row["value"]: row["count"] for row in analytics.status_totals(JobApplication.objects.all())}
        self.assertEqual(totals["applied"], 2)
        self.assertEqual(totals["offer"], 1)
        self.assertEqual(totals["withdrawn"], 0)
        self.assertEqual(len(totals), len(JobApplication.Status.choices))

    def test_conversion_metrics(self):
        make_app(self.user, status="applied")
        make_app(self.user, status="interview")
        make_app(self.user, status="rejected", interviewed=True)
        make_app(self.user, status="offer")
        metrics = analytics.conversion_metrics(JobApplication.objects.all())
        self.assertEqual(metrics["total"], 4)
        self.assertEqual(metrics["interviewed"], 3)
        self.assertEqual(metrics["offers"], 1)
        self.assertEqual(metrics["interview_rate"], 75.0)
        self.assertEqual(metrics["offer_rate"], 25.0)
        self.assertEqual(metrics["interview_to_offer_rate"], 33.3)

    def test_conversion_metrics_with_no_data_avoid_division_by_zero(self):
        metrics = analytics.conversion_metrics(JobApplication.objects.all())
        self.assertEqual(metrics["total"], 0)
        self.assertIsNone(metrics["interview_rate"])
        self.assertIsNone(metrics["interview_to_offer_rate"])

    def test_add_months_crosses_year_boundaries(self):
        self.assertEqual(analytics.add_months(date(2026, 1, 15), -1), date(2025, 12, 1))
        self.assertEqual(analytics.add_months(date(2026, 11, 30), 3), date(2027, 2, 1))
        self.assertEqual(analytics.add_months(date(2026, 3, 9), 0), date(2026, 3, 1))

    def test_monthly_trend_is_zero_filled_and_windowed(self):
        today = date(2026, 3, 15)
        make_app(self.user, applied_date=date(2026, 3, 2))
        make_app(self.user, applied_date=date(2026, 1, 20), interviewed=True)
        make_app(self.user, applied_date=date(2025, 3, 31))  # 13 months back: outside the window
        trend = analytics.monthly_trend(JobApplication.objects.all(), months=12, today=today)
        self.assertEqual(len(trend), 12)
        self.assertEqual(trend[0]["label"], "Apr 2025")
        self.assertEqual(trend[-1]["label"], "Mar 2026")
        by_label = {row["label"]: row for row in trend}
        self.assertEqual(by_label["Mar 2026"]["applications"], 1)
        self.assertEqual(by_label["Jan 2026"]["applications"], 1)
        self.assertEqual(by_label["Jan 2026"]["interviews"], 1)
        self.assertEqual(by_label["Feb 2026"]["applications"], 0)
        self.assertEqual(sum(row["applications"] for row in trend), 2)
