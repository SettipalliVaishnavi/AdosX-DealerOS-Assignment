from django.urls import path
from reconcile import views, page_views

urlpatterns = [
    path("", page_views.dashboard, name="dashboard"),
    path("organizations/", views.organizations, name="organizations"),
    path("disagreements/", views.disagreements, name="disagreements"),
]
