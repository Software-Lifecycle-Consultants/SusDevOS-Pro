from django.urls import path
from .views import PublicBlogDetailView, PublicBlogListView

urlpatterns = [
    path("blog/",          PublicBlogListView.as_view(),        name="public-blog-list"),
    path("blog/<slug:slug>/", PublicBlogDetailView.as_view(),   name="public-blog-detail"),
]
