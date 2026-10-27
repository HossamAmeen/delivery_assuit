from django.urls import path

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshView,
    RegisterClientView,
    RegisterDriverView,
    RegisterTraderView,
)

urlpatterns = [
    path("token/", LoginView.as_view(), name="token"),
    path("token/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/driver/", RegisterDriverView.as_view(), name="register-driver"),
    path("register/trader/", RegisterTraderView.as_view(), name="register-trader"),
    path("register/client/", RegisterClientView.as_view(), name="register-client"),
    path("me/", MeView.as_view(), name="me"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),
]
