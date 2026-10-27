from django.urls import path

from .views import MarkReadView, NotificationListView, ReadAllView, UnreadCountView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("unread-count/", UnreadCountView.as_view(), name="notification-unread"),
    path("read-all/", ReadAllView.as_view(), name="notification-read-all"),
    path("<int:pk>/read/", MarkReadView.as_view(), name="notification-read"),
]
