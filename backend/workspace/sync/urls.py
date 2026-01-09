"""
URL Configuration for Workspace Sync API
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
from django.urls import path, include
from . import views

app_name = 'workspace_sync'

# Workspace-specific sync endpoints
workspace_sync_patterns = [
    # Sync triggering
    path('trigger/', views.trigger_workspace_sync, name='trigger_sync'),

    # Sync events management
    path('events/', views.sync_events_list, name='sync_events_list'),
    path('events/<uuid:event_id>/', views.sync_event_detail, name='sync_event_detail'),
    path('events/<uuid:event_id>/retry/', views.retry_sync_event, name='retry_sync_event'),

    # Workspace sync status
    path('status/', views.workspace_sync_status, name='workspace_sync_status'),

    # Polling management
    path('polling/start/', views.start_workspace_polling, name='start_workspace_polling'),
    path('polling/stop/', views.stop_workspace_polling, name='stop_workspace_polling'),

    # Metrics
    path('metrics/', views.sync_metrics, name='sync_metrics'),
]

# Global sync endpoints
global_sync_patterns = [
    # Template validation
    path('validate-template/', views.validate_template_config, name='validate_template_config'),

    # System health
    path('health/', views.system_health, name='system_health'),
]

# Main URL patterns
urlpatterns = [
    # Workspace-specific endpoints (workspace_id provided by parent URL)
    path('', include(workspace_sync_patterns)),

    # Global sync endpoints
    path('sync/', include(global_sync_patterns)),
]