from django.urls import path
from . import views

app_name = "tournaments"

urlpatterns = [
    path("", views.LobbyView.as_view(), name="lobby"),
]
