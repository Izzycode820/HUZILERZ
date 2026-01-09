from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Avg, Sum, F, Window
from django.db.models.functions import Rank
from django.utils import timezone
from datetime import timedelta
from ..models import Template, TemplateCategory, TemplateCustomization
import logging

logger = logging.getLogger(__name__)


class TemplateAnalyticsService:
    """Service for template analytics, categorization, ratings, and usage metrics with error handling"""

    @staticmethod
    def get_template_categories_with_stats(template_type=None, is_featured=None):
        """
        Get template categories with statistics and template counts

        Args:
            template_type: Filter by template type
            is_featured: Filter by featured status

        Returns:
            QuerySet of TemplateCategory instances with stats

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting template categories with stats: type={template_type}, featured={is_featured}")

            queryset = TemplateCategory.objects.filter(is_active=True)

            # Apply filters
            if template_type:
                queryset = queryset.filter(template_type=template_type)

            if is_featured is not None:
                queryset = queryset.filter(is_featured=is_featured)

            # Annotate with template statistics
            categories_with_stats = queryset.annotate(
                template_count=Count('template', filter=Q(template__status='published')),
                avg_rating=Avg('template__rating', filter=Q(template__status='published')),
                total_downloads=Sum('template__download_count', filter=Q(template__status='published')),
                total_views=Sum('template__view_count', filter=Q(template__status='published'))
            ).filter(
                template_count__gt=0
            ).order_by('sort_order', 'name')

            logger.info(f"Retrieved {categories_with_stats.count()} categories with statistics")
            return categories_with_stats

        except Exception as e:
            logger.error(f"Error getting template categories with stats: {e}")
            raise ValidationError("Error retrieving template categories")


    @staticmethod
    def get_template_usage_metrics(template_id, days_back=30):
        """
        Get comprehensive usage metrics for a template

        Args:
            template_id: ID of template
            days_back: Number of days to analyze

        Returns:
            Dictionary with usage metrics

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting usage metrics for template {template_id} from last {days_back} days")

            # Get template
            try:
                template = Template.objects.get(id=template_id, status='published')
            except Template.DoesNotExist:
                logger.warning(f"Template {template_id} not found or not published")
                raise ValidationError("Template not found or not available")

            # Calculate date range
            start_date = timezone.now() - timedelta(days=days_back)

            # Get active customizations count
            active_customizations = TemplateCustomization.objects.filter(
                template=template,
                is_active=True
            ).count()

            # Get recent customizations (last 30 days)
            recent_customizations = TemplateCustomization.objects.filter(
                template=template,
                created_at__gte=start_date
            ).count()

            # Get deployment statistics
            deployed_customizations = TemplateCustomization.objects.filter(
                template=template,
                status='deployed'
            ).count()

            # Calculate usage growth
            previous_period_start = start_date - timedelta(days=days_back)
            previous_customizations = TemplateCustomization.objects.filter(
                template=template,
                created_at__range=[previous_period_start, start_date]
            ).count()

            usage_growth = 0
            if previous_customizations > 0:
                usage_growth = ((recent_customizations - previous_customizations) / previous_customizations) * 100

            metrics = {
                'template': template,
                'usage_overview': {
                    'total_active_customizations': active_customizations,
                    'recent_customizations': recent_customizations,
                    'deployed_customizations': deployed_customizations,
                    'usage_growth_percentage': usage_growth
                },
                'performance_metrics': {
                    'view_count': template.view_count,
                    'download_count': template.download_count,
                    'rating': float(template.rating) if template.rating else 0.0,
                    'rating_count': template.rating_count
                },
                'time_period': {
                    'days': days_back,
                    'start_date': start_date,
                    'end_date': timezone.now()
                }
            }

            logger.info(f"Successfully retrieved usage metrics for template {template_id}")
            return metrics

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting usage metrics for template {template_id}: {e}")
            raise ValidationError("Error retrieving usage metrics")

    @staticmethod
    def get_template_preview_system_data(template_id):
        """
        Get data for template preview system

        Args:
            template_id: ID of template

        Returns:
            Dictionary with preview system data

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting preview system data for template {template_id}")

            # Get template with all related data
            template = Template.objects.filter(
                id=template_id,
                status='published'
            ).select_related(
                'created_by'
            ).prefetch_related(
                'versions',
                'assets',
                'categories'
            ).first()

            if not template:
                logger.warning(f"Template {template_id} not found or not published")
                raise ValidationError("Template not found or not available")

            # Get latest version
            latest_version = template.get_latest_version()

            # Get public assets
            public_assets = template.assets.filter(is_public=True)

            # Calculate rating statistics (using simple template fields)
            rating_stats = {
                'average': float(template.rating) if template.rating else 0.0,
                'count': template.rating_count
            }

            preview_data = {
                'template': template,
                'latest_version': latest_version,
                'public_assets': public_assets,
                'categories': template.categories.all(),
                'rating_stats': rating_stats,
                'preview_config': {
                    'demo_url': template.demo_url,
                    'cdn_path': template.cdn_path,
                    'puck_config': template.puck_config
                }
            }

            logger.info(f"Successfully retrieved preview system data for template {template_id}")
            return preview_data

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting preview system data for template {template_id}: {e}")
            raise ValidationError("Error retrieving preview system data")

    @staticmethod
    def get_category_performance_analytics(category_id=None, days_back=90):
        """
        Get performance analytics for template categories

        Args:
            category_id: Specific category ID (optional)
            days_back: Number of days to analyze

        Returns:
            Dictionary with category performance analytics

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting category performance analytics: category={category_id}, days={days_back}")

            queryset = TemplateCategory.objects.filter(is_active=True)

            if category_id:
                queryset = queryset.filter(id=category_id)

            # Calculate date range
            start_date = timezone.now() - timedelta(days=days_back)

            # Get category performance metrics
            categories_with_performance = queryset.annotate(
                template_count=Count('template', filter=Q(template__status='published')),
                total_views=Sum('template__view_count', filter=Q(template__status='published')),
                total_downloads=Sum('template__download_count', filter=Q(template__status='published')),
                total_ratings=Sum('template__rating_count', filter=Q(template__status='published')),
                avg_rating=Avg('template__rating', filter=Q(template__status='published')),
                recent_activity=Count(
                    'template__customizations',
                    filter=Q(
                        template__customizations__created_at__gte=start_date,
                        template__status='published'
                    )
                )
            ).filter(
                template_count__gt=0
            ).order_by('-total_views', '-total_downloads')

            analytics = {
                'categories': list(categories_with_performance),
                'time_period': {
                    'days': days_back,
                    'start_date': start_date,
                    'end_date': timezone.now()
                },
                'summary': {
                    'total_categories': categories_with_performance.count(),
                    'total_templates': sum(c.template_count for c in categories_with_performance),
                    'total_views': sum(c.total_views or 0 for c in categories_with_performance),
                    'total_downloads': sum(c.total_downloads or 0 for c in categories_with_performance)
                }
            }

            logger.info(f"Successfully retrieved performance analytics for {analytics['summary']['total_categories']} categories")
            return analytics

        except Exception as e:
            logger.error(f"Error getting category performance analytics: {e}")
            raise ValidationError("Error retrieving category performance analytics")

    @staticmethod
    def get_template_leaderboard(metric='downloads', limit=20, days_back=30):
        """
        Get template leaderboard based on various metrics

        Args:
            metric: Ranking metric (downloads, views, ratings, usage)
            limit: Number of templates to return
            days_back: Number of days to consider

        Returns:
            QuerySet of top templates with ranking

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting template leaderboard: metric={metric}, limit={limit}, days={days_back}")

            # Calculate date range
            start_date = timezone.now() - timedelta(days=days_back)

            # Define metric fields
            metric_fields = {
                'downloads': 'download_count',
                'views': 'view_count',
                'ratings': 'rating',
                'usage': 'active_usage_count'
            }

            metric_field = metric_fields.get(metric, 'download_count')

            # Get templates with ranking
            leaderboard = Template.objects.filter(
                status='published',
                created_at__gte=start_date
            ).annotate(
                rank=Window(
                    expression=Rank(),
                    order_by=F(metric_field).desc() if not metric_field.startswith('-') else F(metric_field[1:]).asc()
                )
            ).order_by(metric_field if metric_field.startswith('-') else f'-{metric_field}')[:limit]

            logger.info(f"Successfully retrieved {leaderboard.count()} templates for leaderboard")
            return leaderboard

        except Exception as e:
            logger.error(f"Error getting template leaderboard: {e}")
            raise ValidationError("Error retrieving template leaderboard")