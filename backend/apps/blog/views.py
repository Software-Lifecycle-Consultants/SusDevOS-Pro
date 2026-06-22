from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Blogs
from .serializers import BlogsDetailSerializer, BlogsListSerializer, PublicBlogSerializer


class BlogsViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Blogs.objects.all()

    def get_queryset(self):
        user = self.request.user
        qs = Blogs.objects.filter(Status__lt=4)
        if not getattr(user, "IsSuperAdmin", False):
            entity_id = getattr(self.request, "entity_id", None)
            if entity_id:
                qs = qs.filter(EntityId_id=entity_id)
            else:
                return qs.none()
        return qs.order_by("-CreatedAt")

    def get_serializer_class(self):
        return BlogsListSerializer if self.action == "list" else BlogsDetailSerializer

    def perform_create(self, serializer):
        serializer.save(
            EntityId_id=self.request.entity_id,
            AuthorId=self.request.user,
            CreatedBy=self.request.user.UserId,
        )

    def perform_destroy(self, instance):
        instance.Status = 4
        instance.save()

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        post = self.get_object()
        if post.BlogStatus == 2:
            return Response({"code": "already_published", "detail": "Already published."},
                            status=status.HTTP_400_BAD_REQUEST)
        post.BlogStatus = 2
        post.PublishedAt = timezone.now()
        post.save()
        return Response(BlogsDetailSerializer(post).data)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        post = self.get_object()
        post.BlogStatus = 3
        post.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Public (no auth) ───────────────────────────────────────────────────────────

class PublicBlogListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        posts = Blogs.objects.filter(BlogStatus=2, Status__lt=4).order_by("-PublishedAt")
        return Response(PublicBlogSerializer(posts, many=True).data)


class PublicBlogDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            post = Blogs.objects.get(Slug=slug, BlogStatus=2, Status__lt=4)
        except Blogs.DoesNotExist:
            return Response({"code": "not_found", "detail": "Post not found."},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(PublicBlogSerializer(post).data)
