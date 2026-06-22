from django.urls import path
from apps.users.views import (
    LoginView, RefreshView, LogoutView,
    ForgotPasswordView, ResetPasswordView,
    OnboardView, MeView,
)

urlpatterns = [
    path("login",           LoginView.as_view(),          name="auth-login"),
    path("refresh",         RefreshView.as_view(),         name="auth-refresh"),
    path("logout",          LogoutView.as_view(),          name="auth-logout"),
    path("forgot-password", ForgotPasswordView.as_view(),  name="auth-forgot-password"),
    path("reset-password",  ResetPasswordView.as_view(),   name="auth-reset-password"),
    path("onboard",         OnboardView.as_view(),         name="auth-onboard"),
    path("me",              MeView.as_view(),              name="auth-me"),
]
