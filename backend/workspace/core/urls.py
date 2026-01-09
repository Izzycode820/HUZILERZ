from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkspaceViewSet, MembershipViewSet, RoleViewSet


app_name = 'core'

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'memberships', MembershipViewSet, basename='membership')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    path('', include(router.urls)),

]