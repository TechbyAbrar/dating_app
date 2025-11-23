from django.urls import path
from .views import (
    NotificationListAPI,
    NotificationMarkReadAPI,
    NotificationDeleteAPI,
)

urlpatterns = [
    path("list/", NotificationListAPI.as_view(), name="notifications"),
    path("<int:pk>/read/", NotificationMarkReadAPI.as_view(), name="notification-read"),
    path("<int:pk>/delete/", NotificationDeleteAPI.as_view(), name="notification-delete"),
]
