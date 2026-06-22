"""
Migration: Blogs
App: apps.blog
Depends on: apps.entities, apps.users

Blog posts are created by Super Admins or Entity Admins via the authenticated
CMS endpoint (/api/v1/blog/). Published posts are publicly accessible without
authentication at /api/public/blog/{slug}/.

Status transitions:
  Draft (1) → Published (2)   — irreversible; use Archive to retire
  Published (2) → Archived (3) — soft-retire without deletion

Slug: URL-safe, lowercase, hyphenated, auto-generated from Title on create
      but editable before publishing. Must be unique across all blog posts.

SEO fields are optional but recommended — shown with character-count hints
in the CMS (60 chars for SeoTitle, 160 for SeoDescription).
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_entities'),
        ('users', '0001_users_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blogs',
            fields=[
                ('BlogId', models.AutoField(primary_key=True)),
                ('EntityId', models.ForeignKey(
                    to='entities.Entities',
                    on_delete=models.PROTECT,
                    related_name='blog_posts',
                    help_text="Entity that owns this blog post"
                )),
                ('AuthorId', models.ForeignKey(
                    to='users.Users',
                    on_delete=models.SET_NULL,
                    null=True,
                    related_name='authored_posts',
                )),
                ('Title', models.CharField(max_length=200)),
                ('Slug', models.SlugField(
                    max_length=220,
                    unique=True,
                    help_text="URL-safe identifier: auto-generated from Title, editable before publish"
                )),
                ('PostBody', models.TextField()),
                ('BlogStatus', models.PositiveSmallIntegerField(
                    default=1,
                    help_text="1: Draft, 2: Published, 3: Archived"
                )),
                ('PublishedAt', models.DateTimeField(
                    null=True,
                    blank=True,
                    help_text="Set when BlogStatus transitions to Published"
                )),
                # SEO fields
                ('SeoTitle', models.CharField(
                    max_length=60,
                    blank=True,
                    null=True,
                    help_text="SEO title — max 60 chars recommended"
                )),
                ('SeoDescription', models.CharField(
                    max_length=160,
                    blank=True,
                    null=True,
                    help_text="SEO meta description — max 160 chars recommended"
                )),
                # Embed URLs for public GHG chart/table widgets
                ('EmbedUrls', models.JSONField(
                    default=list,
                    help_text="List of public chart/table URLs rendered as iframes on the public blog page"
                )),
                # FeaturedImageId: optional cover image
                ('FeaturedImageId', models.IntegerField(
                    null=True,
                    blank=True,
                    help_text="FK to shared.Images (IntegerField to avoid cross-app circular import)"
                )),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'blogs'},
        ),
        migrations.AddIndex(
            model_name='Blogs',
            index=models.Index(fields=['Slug'], name='idx_blog_slug'),
        ),
        migrations.AddIndex(
            model_name='Blogs',
            index=models.Index(
                fields=['BlogStatus', 'PublishedAt'],
                name='idx_blog_status_published',
            ),
        ),
    ]
