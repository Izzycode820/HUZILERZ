from django.urls import path, include
from graphene_file_upload.django import FileUploadGraphQLView
from django.views.decorators.csrf import csrf_exempt
from .graphql.middleware.auth import AuthenticationMiddleware
from .graphql.schema import schema as admin_schema

app_name = 'store'

urlpatterns = [
    # GraphQL endpoint (authenticated)
    # Full path: /api/workspace/store/graphql/
    path('graphql/', csrf_exempt(FileUploadGraphQLView.as_view(
        graphiql=True,
        schema=admin_schema,
        middleware=[AuthenticationMiddleware()]
    ))),

]