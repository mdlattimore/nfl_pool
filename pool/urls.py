from django.urls import path
from .views import PickView


urlpatterns = [
    path('picks/week/<int:week>/', PickView.as_view(), name="make_picks"),
]