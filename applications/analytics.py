"""Dashboard calculations. Every function takes an already user-scoped queryset."""
from datetime import date, datetime

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import JobApplication


def add_months(d, n):
    """Return the first day of the month n months after d's month (n may be negative)."""
    index = d.year * 12 + (d.month - 1) + n
    return date(index // 12, index % 12 + 1, 1)


def _percent(part, whole):
    if not whole:
        return None
    return round(100 * part / whole, 1)


def status_totals(queryset):
    """One row per status, in display order, including statuses with zero applications."""
    counts = dict(queryset.order_by().values_list("status").annotate(n=Count("id")))
    return [
        {"value": value, "label": label, "count": counts.get(value, 0)}
        for value, label in JobApplication.Status.choices
    ]


def conversion_metrics(queryset):
    agg = queryset.order_by().aggregate(
        total=Count("id"),
        interviewed=Count("id", filter=Q(interviewed=True)),
        offers=Count("id", filter=Q(status=JobApplication.Status.OFFER)),
    )
    total, interviewed, offers = agg["total"], agg["interviewed"], agg["offers"]
    return {
        "total": total,
        "interviewed": interviewed,
        "offers": offers,
        "interview_rate": _percent(interviewed, total),
        "offer_rate": _percent(offers, total),
        "interview_to_offer_rate": _percent(offers, interviewed),
    }


def monthly_trend(queryset, months=12, today=None):
    """Applications and interviews per month for the last `months` months, zero-filled."""
    today = today or timezone.localdate()
    first = add_months(today.replace(day=1), -(months - 1))
    rows = (
        queryset.filter(applied_date__gte=first)
        .annotate(month=TruncMonth("applied_date"))
        .values("month")
        .annotate(applications=Count("id"), interviews=Count("id", filter=Q(interviewed=True)))
        .order_by("month")
    )
    by_month = {}
    for row in rows:
        month = row["month"]
        if isinstance(month, datetime):
            month = month.date()
        by_month[month] = row

    trend = []
    for offset in range(months):
        month = add_months(first, offset)
        row = by_month.get(month, {})
        trend.append(
            {
                "month": month,
                "label": month.strftime("%b %Y"),
                "applications": row.get("applications", 0),
                "interviews": row.get("interviews", 0),
            }
        )
    return trend
