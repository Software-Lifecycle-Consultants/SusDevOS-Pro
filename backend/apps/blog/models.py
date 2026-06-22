"""Blog app models. Ref: reference migration 0015_blogs."""
from django.db import models
from apps.shared.models import BaseAuditMixin


class Blogs(BaseAuditMixin):
    BlogId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="blog_posts")
    AuthorId = models.ForeignKey(
        "users.Users", on_delete=models.SET_NULL, null=True, related_name="authored_posts"
    )
    Title = models.CharField(max_length=200)
    Slug = models.SlugField(max_length=220, unique=True)
    PostBody = models.TextField()
    BlogStatus = models.PositiveSmallIntegerField(default=1, help_text="1: Draft, 2: Published, 3: Archived")
    PublishedAt = models.DateTimeField(null=True, blank=True)
    SeoTitle = models.CharField(max_length=60, blank=True, null=True)
    SeoDescription = models.CharField(max_length=160, blank=True, null=True)
    EmbedUrls = models.JSONField(default=list)
    FeaturedImageId = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "blogs"
        ordering = ["-CreatedAt"]
        indexes = [
            models.Index(fields=["Slug"], name="idx_blog_slug"),
            models.Index(fields=["BlogStatus", "PublishedAt"], name="idx_blog_status_published"),
        ]

    def __str__(self):
        return self.Title
