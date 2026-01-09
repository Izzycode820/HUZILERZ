from django.urls import path, include
from workspace.core.views import workspace_views, member_views

app_name = 'workspace'

urlpatterns = [
    # Core workspace management endpoints
    path('', workspace_views.list_workspaces, name='list-workspaces'),
    path('create/', workspace_views.create_workspace, name='create-workspace'),
    path('<uuid:workspace_id>/', workspace_views.get_workspace, name='get-workspace'),
    path('<uuid:workspace_id>/update/', workspace_views.update_workspace, name='update-workspace'),
    path('<uuid:workspace_id>/delete/', workspace_views.delete_workspace, name='delete-workspace'),
    path('<uuid:workspace_id>/restore/', workspace_views.restore_workspace, name='restore-workspace'),

    # Member management endpoints
    path('<uuid:workspace_id>/members/', member_views.list_members, name='list-members'),
    path('<uuid:workspace_id>/members/invite/', member_views.invite_member, name='invite-member'),
    path('<uuid:workspace_id>/members/<int:user_id>/', member_views.remove_member, name='remove-member'),
    path('<uuid:workspace_id>/members/<int:user_id>/role/', member_views.change_member_role, name='change-member-role'),

    # Sync endpoints
    path('<uuid:workspace_id>/sync/', include('workspace.sync.urls')),

    # Store workspace endpoints
    path('store/', include('workspace.store.urls')),

    # Storefront endpoints (customer-facing)
    path('storefront/', include('workspace.storefront.urls')),


    # Hosting endpoints (workspace-scoped)
    path('hosting/', include('workspace.hosting.urls')),

    # Other workspace type endpoints can be added here
    # path('<str:workspace_id>/blog/', include('workspace.blog.urls')),
    # path('<str:workspace_id>/services/', include('workspace.services.urls')),
]