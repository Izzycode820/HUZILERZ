"""
PostHog Analytics Service

Wrapper for PostHog integration.
Sends events to PostHog for advanced analytics, funnels, and session replay.

Design Principles:
- Performance: Async event sending, non-blocking
- Reliability: Graceful degradation if PostHog unavailable
- Privacy: workspace_id as distinctId (merchant-level tracking)
"""

from typing import Dict, Any, Optional
from django.conf import settings
import posthog
import logging

logger = logging.getLogger('analytics.posthog')


class PostHogService:
    """
    PostHog integration service.
    
    Sends analytics events to PostHog for:
    - Funnel analysis
    - Session replay
    - Advanced dashboards
    - A/B testing (future)
    
    Usage:
        service = PostHogService()
        service.capture_event(workspace_id, 'order_completed', {'order_value': 1000})
    """
    
    def __init__(self):
        """Initialize PostHog client."""
        self.enabled = getattr(settings, 'POSTHOG_ENABLED', False)
        
        if self.enabled:
            posthog_key = getattr(settings, 'POSTHOG_API_KEY', None)
            posthog_host = getattr(settings, 'POSTHOG_HOST', 'https://app.posthog.com')
            
            if not posthog_key:
                logger.warning("PostHog enabled but no API key configured")
                self.enabled = False
            else:
                posthog.project_api_key = posthog_key
                posthog.host = posthog_host
                logger.info(f"PostHog initialized (host: {posthog_host})")
    
    def capture_event(
        self,
        workspace_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Capture an event in PostHog.
        
        Args:
            workspace_id: Workspace UUID (used as distinctId)
            event_name: Event name (order_completed, etc.)
            properties: Event properties
            session_id: Optional session ID for customer journey tracking
            
        Returns:
            True if event sent successfully, False otherwise
            
        Reliability: Never raises exceptions - logs errors and returns False
        """
        if not self.enabled:
            return False
        
        try:
            properties = properties or {}
            
            # Always include workspace_id in properties for filtering
            properties['workspace_id'] = str(workspace_id)
            
            # Include session_id if provided (for funnel analysis)
            if session_id:
                properties['session_id'] = str(session_id)
            
            # Send to PostHog
            posthog.capture(
                distinct_id=str(workspace_id),  # Merchant-level tracking
                event=event_name,
                properties=properties
            )
            
            logger.debug(f"PostHog event captured: {event_name} for workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event to PostHog: {e}", exc_info=True)
            return False
    
    def identify_workspace(
        self,
        workspace_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Identify a workspace in PostHog.
        
        Sets workspace properties for segmentation (plan, created_at, etc.)
        
        Args:
            workspace_id: Workspace UUID
            properties: Workspace properties (plan, name, etc.)
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            properties = properties or {}
            
            posthog.identify(
                distinct_id=str(workspace_id),
                properties=properties
            )
            
            logger.debug(f"PostHog workspace identified: {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to identify workspace in PostHog: {e}", exc_info=True)
            return False
    
    def set_workspace_property(
        self,
        workspace_id: str,
        property_name: str,
        property_value: Any
    ) -> bool:
        """
        Set a single property on a workspace.
        
        Useful for updating plan, subscription status, etc.
        
        Args:
            workspace_id: Workspace UUID
            property_name: Property key
            property_value: Property value
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            posthog.set(
                distinct_id=str(workspace_id),
                properties={property_name: property_value}
            )
            
            logger.debug(f"PostHog property set: {property_name} for workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set workspace property in PostHog: {e}", exc_info=True)
            return False
    
    def flush(self):
        """
        Flush any pending events to PostHog.
        
        Useful for testing or before shutdown.
        """
        if self.enabled:
            try:
                posthog.flush()
            except Exception as e:
                logger.error(f"Failed to flush PostHog queue: {e}")


# Singleton instance
_posthog_service = None


def get_posthog_service() -> PostHogService:
    """Get singleton PostHog service instance."""
    global _posthog_service
    if _posthog_service is None:
        _posthog_service = PostHogService()
    return _posthog_service
