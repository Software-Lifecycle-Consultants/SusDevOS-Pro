from django.urls import path

from .views import PlansListView, SubscriptionView

urlpatterns = [
    path("plans/",        PlansListView.as_view(),   name="billing-plans"),
    path("subscription/", SubscriptionView.as_view(), name="billing-subscription"),
]
