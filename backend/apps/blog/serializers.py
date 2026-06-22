from django.utils.text import slugify
from rest_framework import serializers
from .models import Blogs


class BlogsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blogs
        fields = ("BlogId", "Title", "Slug", "BlogStatus", "PublishedAt",
                  "SeoTitle", "AuthorId", "CreatedAt")


class BlogsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blogs
        fields = "__all__"
        read_only_fields = ("BlogId", "EntityId", "PublishedAt",
                            "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy")

    def validate(self, data):
        # Auto-generate slug from title if not provided on create
        if not data.get("Slug") and data.get("Title"):
            data["Slug"] = slugify(data["Title"])[:220]
        return data


class PublicBlogSerializer(serializers.ModelSerializer):
    """Stripped-down read-only serializer for the public endpoint."""
    class Meta:
        model = Blogs
        fields = ("BlogId", "Title", "Slug", "PostBody", "PublishedAt",
                  "SeoTitle", "SeoDescription", "EmbedUrls", "FeaturedImageId")
