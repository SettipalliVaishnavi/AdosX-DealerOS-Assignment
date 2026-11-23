from django.contrib import admin
from django.urls import path, include
from reconcile.page_views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("reconcile.urls")),
    path("", dashboard, name="dashboard"),
]
