"""
Blog Workspace Data Export Service
Implements workspace data export for blog content management
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
from typing import Dict, Any, Optional, List
from django.db import transaction, models
from django.core.exceptions import PermissionDenied
from django.apps import apps
from workspace.core.services.base_data_export_service import BaseWorkspaceDataExporter
from workspace.core.models.base_models import BaseWorkspaceContentModel
import logging

logger = logging.getLogger('workspace.blog.data_export')


class BlogDataExporter(BaseWorkspaceDataExporter):
    """
    Blog-specific implementation of workspace data exporter
    Handles blog content with admin/public separation
    """

    # Fields that trigger site sync when changed
    SYNC_TRIGGER_FIELDS = [
        'title', 'content', 'excerpt', 'featured_image',
        'is_active', 'status', 'tags', 'category'
    ]

    # Admin-only fields (never exposed to public)
    ADMIN_ONLY_FIELDS = [
        'views', 'edit_count', 'draft_content', 'seo_score'
    ]

    def export_data(self, workspace_id: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export complete blog data with optional filtering

        Args:
            workspace_id: UUID of the blog workspace
            filters: Optional filters for data export

        Returns:
            Dict containing complete blog data
        """
        try:
            with transaction.atomic():
                # Base filters
                base_filters = {'workspace_id': workspace_id, 'is_active': True}
                if filters:
                    base_filters.update(filters)

                # Export posts (using base content model)
                posts = self._export_posts(base_filters)

                # Export categories
                categories = self._export_categories(workspace_id)

                # Export tags
                tags = self._export_tags(workspace_id)

                # Export blog settings
                blog_settings = self._export_blog_settings(workspace_id)

                return {
                    'posts': posts,
                    'categories': categories,
                    'tags': tags,
                    'blog_settings': blog_settings,
                    'export_metadata': {
                        'workspace_id': workspace_id,
                        'export_type': 'full_data',
                        'post_count': len(posts),
                        'category_count': len(categories),
                        'tag_count': len(tags)
                    }
                }

        except Exception as e:
            logger.error(f"Failed to export blog data for workspace {workspace_id}: {str(e)}")
            raise

    def get_storefront_data(self, workspace_id: str) -> Dict[str, Any]:
        """
        Export public blog data only
        Excludes admin-only information like drafts and analytics

        Args:
            workspace_id: UUID of the blog workspace

        Returns:
            Dict containing public blog content
        """
        try:
            # Only published posts
            posts = BaseWorkspaceContentModel.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                status='published'
            ).values(
                'id', 'title', 'content', 'excerpt', 'featured_image',
                'tags', 'created_at', 'updated_at', 'slug'
                # Excludes: views, edit_count, draft_content, etc.
            ).order_by('-created_at')

            # Public blog settings
            blog_settings = self._get_public_blog_settings(workspace_id)

            # Available categories and tags
            categories = self._get_public_categories(workspace_id)
            tags = self._get_public_tags(workspace_id)

            return {
                'posts': list(posts),
                'categories': categories,
                'tags': tags,
                'blog_info': blog_settings,
                'storefront_metadata': {
                    'total_posts': len(posts),
                    'categories_count': len(categories),
                    'tags_count': len(tags),
                    'data_type': 'public_blog'
                }
            }

        except Exception as e:
            logger.error(f"Failed to export blog storefront data for workspace {workspace_id}: {str(e)}")
            raise

    def get_admin_data(self, workspace_id: str, user) -> Dict[str, Any]:
        """
        Export full blog admin data
        Includes drafts, analytics, and editing history

        Args:
            workspace_id: UUID of the blog workspace
            user: User requesting the data

        Returns:
            Dict containing complete admin data
        """
        try:
            # Validate admin permissions
            if not self.validate_export_permissions(workspace_id, user, 'admin'):
                raise PermissionDenied("Insufficient permissions for blog admin data export")

            # All posts including drafts
            posts = BaseWorkspaceContentModel.objects.filter(
                workspace_id=workspace_id
            ).values(
                'id', 'title', 'content', 'excerpt', 'featured_image',
                'tags', 'status', 'is_active', 'created_at', 'updated_at',
                'created_by__username', 'slug'
            ).order_by('-updated_at')

            # Content analytics
            content_analytics = self._get_content_analytics(workspace_id)

            # Author analytics
            author_analytics = self._get_author_analytics(workspace_id)

            # Performance metrics
            performance_metrics = self._get_blog_performance_metrics(workspace_id)

            return {
                'posts': list(posts),
                'content_analytics': content_analytics,
                'author_analytics': author_analytics,
                'performance_metrics': performance_metrics,
                'admin_metadata': {
                    'export_type': 'admin_api',
                    'includes_drafts': True,
                    'includes_analytics': True
                }
            }

        except Exception as e:
            logger.error(f"Failed to export blog admin data for workspace {workspace_id}: {str(e)}")
            raise

    def get_template_variables(self, workspace_id: str) -> Dict[str, Any]:
        """
        Export blog data formatted for template variable replacement

        Args:
            workspace_id: UUID of the blog workspace

        Returns:
            Dict with template variable mappings
        """
        try:
            # Get workspace info
            Workspace = apps.get_model('core', 'Workspace')
            workspace = Workspace.objects.get(id=workspace_id)

            # Recent posts for homepage
            recent_posts = BaseWorkspaceContentModel.objects.filter(
                workspace_id=workspace_id,
                is_active=True,
                status='published'
            ).order_by('-created_at')[:6]  # Limit for performance

            # Featured posts (can be manually selected or most viewed)
            featured_posts = recent_posts[:3]

            # Categories for navigation
            categories = self._get_active_categories(workspace_id)

            # Popular tags
            popular_tags = self._get_popular_tags(workspace_id)

            # Blog profile settings
            blog_profile = self._get_blog_profile(workspace_id)

            # Author information
            author_info = self._get_author_info(workspace_id)

            return {
                # Blog information
                'blog_title': blog_profile.get('blog_title', workspace.name),
                'blog_tagline': blog_profile.get('tagline', ''),
                'blog_description': workspace.description or '',
                'blog_logo': blog_profile.get('logo_url', ''),
                'brand_color': blog_profile.get('primary_color', '#333333'),
                'accent_color': blog_profile.get('accent_color', '#007bff'),

                # Author information
                'author_name': author_info.get('name', ''),
                'author_bio': author_info.get('bio', ''),
                'author_image': author_info.get('image', ''),
                'author_social': author_info.get('social_links', {}),

                # Content
                'recent_posts': [
                    {
                        'id': post.id,
                        'title': post.title,
                        'excerpt': post.excerpt or post.content[:200] + '...',
                        'content': post.content,
                        'featured_image': post.featured_image,
                        'url': f"/blog/{workspace.slug}/posts/{post.slug}",
                        'published_date': post.created_at.strftime('%B %d, %Y'),
                        'reading_time': self._calculate_reading_time(post.content),
                        'tags': post.tags or []
                    }
                    for post in recent_posts
                ],

                'featured_posts': [
                    {
                        'id': post.id,
                        'title': post.title,
                        'excerpt': post.excerpt or post.content[:150] + '...',
                        'featured_image': post.featured_image,
                        'url': f"/blog/{workspace.slug}/posts/{post.slug}",
                        'published_date': post.created_at.strftime('%B %d, %Y')
                    }
                    for post in featured_posts
                ],

                # Navigation
                'categories': [
                    {
                        'name': cat['category'],
                        'post_count': cat['post_count'],
                        'url': f"/blog/{workspace.slug}/category/{cat['category']}"
                    }
                    for cat in categories if cat['category']
                ],

                'popular_tags': [
                    {
                        'name': tag['tag'],
                        'post_count': tag['post_count'],
                        'url': f"/blog/{workspace.slug}/tag/{tag['tag']}"
                    }
                    for tag in popular_tags
                ],

                # Blog configuration
                'blog_settings': {
                    'posts_per_page': blog_profile.get('posts_per_page', 10),
                    'allow_comments': blog_profile.get('allow_comments', True),
                    'social_sharing': blog_profile.get('social_sharing', True),
                    'show_reading_time': True,
                    'show_author_bio': True
                },

                # Template metadata
                'template_data': {
                    'workspace_type': 'blog',
                    'total_posts': recent_posts.count(),
                    'last_updated': workspace.updated_at.isoformat() if workspace.updated_at else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to export blog template variables for workspace {workspace_id}: {str(e)}")
            raise

    def validate_export_permissions(self, workspace_id: str, user, export_type: str) -> bool:
        """
        Validate user permissions for blog data export

        Args:
            workspace_id: UUID of the blog workspace
            user: User requesting export
            export_type: Type of export (admin, storefront, template)

        Returns:
            Boolean indicating permission status
        """
        try:
            if not user or not user.is_authenticated:
                return False

            # Public and template data are generally accessible
            if export_type in ['storefront', 'template']:
                return True

            # Admin data requires workspace membership
            if export_type == 'admin':
                WorkspaceMembership = apps.get_model('core', 'WorkspaceMembership')
                return WorkspaceMembership.objects.filter(
                    workspace_id=workspace_id,
                    user=user,
                    is_active=True
                ).exists()

            return False

        except Exception as e:
            logger.error(f"Blog permission validation failed for workspace {workspace_id}: {str(e)}")
            return False

    # Helper methods for blog data export

    def _export_posts(self, filters: Dict) -> List[Dict]:
        """Export posts with applied filters"""
        return list(BaseWorkspaceContentModel.objects.filter(**filters).values(
            'id', 'title', 'content', 'excerpt', 'featured_image',
            'tags', 'status', 'is_active', 'created_at', 'slug'
        ))

    def _export_categories(self, workspace_id: str) -> List[Dict]:
        """Export post categories"""
        # Categories would come from a separate category model or extracted from posts
        # For now, extracting from post tags
        return []

    def _export_tags(self, workspace_id: str) -> List[str]:
        """Export all used tags"""
        posts = BaseWorkspaceContentModel.objects.filter(
            workspace_id=workspace_id,
            is_active=True
        ).exclude(tags__isnull=True)

        all_tags = []
        for post in posts:
            if post.tags:
                all_tags.extend(post.tags)

        return list(set(all_tags))

    def _export_blog_settings(self, workspace_id: str) -> Dict:
        """Export blog-specific settings"""
        blog_profile = self._get_blog_profile(workspace_id)
        return blog_profile

    def _get_public_blog_settings(self, workspace_id: str) -> Dict:
        """Get public blog settings"""
        Workspace = apps.get_model('core', 'Workspace')
        workspace = Workspace.objects.get(id=workspace_id)
        blog_profile = self._get_blog_profile(workspace_id)

        return {
            'title': blog_profile.get('blog_title', workspace.name),
            'tagline': blog_profile.get('tagline', ''),
            'description': workspace.description or '',
            'posts_per_page': blog_profile.get('posts_per_page', 10),
            'allow_comments': blog_profile.get('allow_comments', True)
        }

    def _get_public_categories(self, workspace_id: str) -> List[Dict]:
        """Get categories from published posts"""
        # This would be implemented based on your category system
        return []

    def _get_public_tags(self, workspace_id: str) -> List[str]:
        """Get tags from published posts"""
        posts = BaseWorkspaceContentModel.objects.filter(
            workspace_id=workspace_id,
            is_active=True,
            status='published'
        ).exclude(tags__isnull=True)

        all_tags = []
        for post in posts:
            if post.tags:
                all_tags.extend(post.tags)

        return list(set(all_tags))

    def _get_content_analytics(self, workspace_id: str) -> Dict:
        """Get content analytics for admin"""
        posts = BaseWorkspaceContentModel.objects.filter(workspace_id=workspace_id)

        return {
            'total_posts': posts.count(),
            'published_posts': posts.filter(status='published').count(),
            'draft_posts': posts.filter(status='draft').count(),
            'posts_this_month': posts.filter(
                created_at__month=timezone.now().month
            ).count()
        }

    def _get_author_analytics(self, workspace_id: str) -> Dict:
        """Get author analytics"""
        posts = BaseWorkspaceContentModel.objects.filter(workspace_id=workspace_id)

        author_stats = posts.values('created_by__username').annotate(
            post_count=models.Count('id')
        ).order_by('-post_count')

        return {
            'total_authors': author_stats.count(),
            'most_prolific_authors': list(author_stats[:5])
        }

    def _get_blog_performance_metrics(self, workspace_id: str) -> Dict:
        """Get blog performance metrics"""
        # This would include view counts, engagement metrics, etc.
        # For now, return basic metrics
        posts = BaseWorkspaceContentModel.objects.filter(workspace_id=workspace_id)

        return {
            'total_content_pieces': posts.count(),
            'content_this_year': posts.filter(
                created_at__year=timezone.now().year
            ).count(),
            'average_posts_per_month': posts.count() / 12  # Rough estimate
        }

    def _get_active_categories(self, workspace_id: str) -> List[Dict]:
        """Get active categories"""
        # This would be implemented based on your category system
        return []

    def _get_popular_tags(self, workspace_id: str) -> List[Dict]:
        """Get popular tags with post counts"""
        posts = BaseWorkspaceContentModel.objects.filter(
            workspace_id=workspace_id,
            is_active=True,
            status='published'
        ).exclude(tags__isnull=True)

        tag_counts = {}
        for post in posts:
            if post.tags:
                for tag in post.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort by count and return top 10
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return [
            {'tag': tag, 'post_count': count}
            for tag, count in sorted_tags
        ]

    def _get_blog_profile(self, workspace_id: str) -> Dict:
        """Get blog profile settings"""
        try:
            BlogProfile = apps.get_model('blog', 'BlogProfile')
            profile = BlogProfile.objects.get(workspace_id=workspace_id)
            return {
                'blog_title': profile.blog_title,
                'tagline': profile.tagline,
                'posts_per_page': profile.posts_per_page,
                'allow_comments': profile.allow_comments,
                'moderate_comments': profile.moderate_comments,
                'social_sharing': profile.social_sharing,
                'meta_description': profile.meta_description,
                'meta_keywords': profile.meta_keywords
            }
        except:
            # Return defaults if no profile exists
            return {
                'blog_title': 'My Blog',
                'tagline': '',
                'posts_per_page': 10,
                'allow_comments': True,
                'moderate_comments': True,
                'social_sharing': True,
                'meta_description': '',
                'meta_keywords': ''
            }

    def _get_author_info(self, workspace_id: str) -> Dict:
        """Get primary author information"""
        # This would typically come from workspace owner or blog settings
        # For now, return empty structure
        return {
            'name': '',
            'bio': '',
            'image': '',
            'social_links': {}
        }

    def _calculate_reading_time(self, content: str) -> str:
        """Calculate estimated reading time"""
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        return f"{reading_time} min read"


# Register the blog data exporter
from workspace.core.services.base_data_export_service import workspace_data_export_service
workspace_data_export_service.register_exporter('blog', BlogDataExporter())