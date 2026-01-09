# Blog URLs
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogViewSet, CommentModerationViewSet

app_name = 'blog'

router = DefaultRouter()
router.register(r'posts', BlogViewSet, basename='post')
router.register(r'comments', CommentModerationViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
]