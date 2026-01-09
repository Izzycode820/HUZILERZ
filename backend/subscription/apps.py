from django.apps import AppConfig


class SubscriptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscription'
    verbose_name = 'Subscription Management'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import subscription.signals
        except ImportError:
            pass
        
        # Initialize JWT subscription claims integration
        try:
            from subscription.services import subscription_claims_service
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Subscription app initialized with JWT claims integration")
            
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"JWT claims service not available: {str(e)}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Subscription app initialization error: {str(e)}")
