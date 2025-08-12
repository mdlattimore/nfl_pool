from django.urls import path
from .views import PickView, DashboardView


urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path('picks/week/<int:week>/', PickView.as_view(), name="make_picks"),
]