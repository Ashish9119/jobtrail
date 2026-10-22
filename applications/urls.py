from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("applications/", views.ApplicationListView.as_view(), name="list"),
    path("applications/new/", views.ApplicationCreateView.as_view(), name="create"),
    path("applications/<int:pk>/", views.ApplicationDetailView.as_view(), name="detail"),
    path("applications/<int:pk>/edit/", views.ApplicationUpdateView.as_view(), name="update"),
    path("applications/<int:pk>/delete/", views.ApplicationDeleteView.as_view(), name="delete"),
]
