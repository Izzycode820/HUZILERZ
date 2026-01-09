"""
Webhook Service with Shopify-proven 8-retry pattern
Implements enterprise-grade webhook delivery with exponential backoff
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
import asyncio
import time
import random
import hashlib
import hmac
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.apps import apps
import httpx
import backoff
import logging

logger = logging.getLogger('workspace.sync.webhook')


class WebhookService:
    """
    Enterprise webhook delivery service with Shopify's proven patterns
    Implements 8-retry exponential backoff with full jitter
    """

    # Shopify's proven retry delays (seconds)
    RETRY_DELAYS = [1, 2, 4, 8, 16, 32, 64, 128]

    # HTTP timeout settings
    REQUEST_TIMEOUT = 5.0  # Shopify's 5-second rule
    CONNECT_TIMEOUT = 3.0

    # Webhook security
    WEBHOOK_SECRET_HEADER = 'X-Huzilerz-Webhook-Signature'

    def __init__(self):
        self.client = None
        self._setup_http_client()

    def _setup_http_client(self):
        """Setup httpx async client with optimal configuration"""
        limits = httpx.Limits(
            max_keepalive_connections=100,
            max_connections=200,
            keepalive_expiry=30.0
        )

        timeout = httpx.Timeout(
            connect=self.CONNECT_TIMEOUT,
            read=self.REQUEST_TIMEOUT,
            write=self.REQUEST_TIMEOUT,
            pool=10.0
        )

        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            http2=True,  # Enable HTTP/2 for better performance
            follow_redirects=False,  # Security: Don't follow redirects
            verify=True  # Always verify SSL certificates
        )

    async def send_workspace_webhook(
        self,
        workspace_id: str,
        event_type: str,
        data: Dict[str, Any],
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send webhook to all deployed sites for a workspace

        Args:
            workspace_id: UUID of the workspace
            event_type: Type of event (product.created, etc.)
            data: Event payload data
            entity_type: Model name (Product, Post, etc.)
            entity_id: ID of the changed entity
            user_id: User who triggered the change

        Returns:
            Dict with delivery results
        """
        try:
            # Create sync event record
            SyncEvent = apps.get_model('workspace_sync', 'SyncEvent')
            sync_event = SyncEvent.objects.create(
                workspace_id=workspace_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                event_data=data,
                triggered_by_user_id=user_id or ''
            )

            # Get all deployed sites for this workspace
            deployed_sites = await self._get_deployed_sites(workspace_id)

            if not deployed_sites:
                sync_event.mark_completed()
                return {
                    'success': True,
                    'message': 'No deployed sites to sync',
                    'sync_event_id': str(sync_event.event_id)
                }

            # Update sync event with target sites
            site_ids = [site['id'] for site in deployed_sites]
            sync_event.sites_to_sync = site_ids
            sync_event.save(update_fields=['sites_to_sync'])

            # Send webhooks to all sites
            delivery_results = await self._deliver_to_all_sites(
                sync_event, deployed_sites, data
            )

            # Update sync event status
            successful_deliveries = sum(1 for result in delivery_results if result['success'])

            if successful_deliveries == len(deployed_sites):
                sync_event.mark_completed()
            elif successful_deliveries == 0:
                sync_event.mark_failed("All webhook deliveries failed")
            else:
                # Partial success - will be retried by background task
                sync_event.sync_status = 'retrying'
                sync_event.save(update_fields=['sync_status'])

            return {
                'success': successful_deliveries > 0,
                'sync_event_id': str(sync_event.event_id),
                'total_sites': len(deployed_sites),
                'successful_deliveries': successful_deliveries,
                'delivery_results': delivery_results
            }

        except Exception as e:
            logger.error(f"Failed to send workspace webhook: {str(e)}")
            raise

    async def _deliver_to_all_sites(
        self,
        sync_event,
        deployed_sites: List[Dict],
        data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Deliver webhook to all deployed sites concurrently
        Uses asyncio.Semaphore to control concurrent requests
        """
        # Limit concurrent webhooks to prevent overwhelming targets
        semaphore = asyncio.Semaphore(10)

        # Create delivery tasks
        delivery_tasks = []
        for site in deployed_sites:
            task = self._deliver_to_site_with_semaphore(
                semaphore, sync_event, site, data
            )
            delivery_tasks.append(task)

        # Wait for all deliveries to complete
        delivery_results = await asyncio.gather(
            *delivery_tasks, return_exceptions=True
        )

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(delivery_results):
            if isinstance(result, Exception):
                processed_results.append({
                    'site_id': deployed_sites[i]['id'],
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _deliver_to_site_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        sync_event,
        site: Dict,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deliver webhook to single site with semaphore control
        """
        async with semaphore:
            return await self._deliver_to_site(sync_event, site, data)

    async def _deliver_to_site(
        self,
        sync_event,
        site: Dict,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deliver webhook to a single deployed site with 8-retry pattern
        """
        site_id = site['id']
        webhook_url = f"{site['live_url']}/api/webhook/workspace-update"

        # Create webhook delivery record
        WebhookDelivery = apps.get_model('workspace_sync', 'WebhookDelivery')
        delivery = WebhookDelivery.objects.create(
            sync_event=sync_event,
            target_site_id=site_id,
            target_url=webhook_url,
            scheduled_at=timezone.now()
        )

        # Prepare webhook payload
        payload = {
            'event_id': str(sync_event.event_id),
            'event_type': sync_event.event_type,
            'workspace_id': str(sync_event.workspace.id),
            'entity_type': sync_event.entity_type,
            'entity_id': sync_event.entity_id,
            'data': data,
            'timestamp': sync_event.created_at.isoformat(),
            'attempt': 1
        }

        # Attempt delivery with exponential backoff
        for attempt in range(len(self.RETRY_DELAYS) + 1):
            try:
                # Update delivery record
                delivery.attempt_number = attempt + 1
                delivery.save(update_fields=['attempt_number'])

                # Send webhook
                result = await self._send_webhook_request(
                    webhook_url, payload, delivery
                )

                if result['success']:
                    # Mark successful delivery
                    delivery.mark_delivered(
                        status_code=result['status_code'],
                        response_body=result['response_body'][:1000],  # Limit response size
                        duration_ms=result['duration_ms']
                    )

                    # Add to successfully synced sites
                    sync_event.add_synced_site(site_id)

                    return {
                        'site_id': site_id,
                        'success': True,
                        'attempt': attempt + 1,
                        'duration_ms': result['duration_ms']
                    }

                else:
                    # Check if we should retry
                    if attempt < len(self.RETRY_DELAYS):
                        # Calculate delay with jitter
                        base_delay = self.RETRY_DELAYS[attempt]
                        jittered_delay = self._calculate_jitter(base_delay)

                        # Schedule retry
                        delivery.schedule_retry(jittered_delay)

                        # Log retry
                        logger.warning(
                            f"Webhook delivery failed, retrying in {jittered_delay}s. "
                            f"Attempt {attempt + 1}/{len(self.RETRY_DELAYS) + 1} "
                            f"for site {site_id}: {result['error']}"
                        )

                        # Wait with jittered delay
                        await asyncio.sleep(jittered_delay)
                        continue
                    else:
                        # Max retries reached
                        delivery.mark_failed(
                            error_message=result['error'],
                            status_code=result.get('status_code'),
                            duration_ms=result.get('duration_ms')
                        )

                        return {
                            'site_id': site_id,
                            'success': False,
                            'error': result['error'],
                            'attempts': attempt + 1
                        }

            except Exception as e:
                error_msg = f"Webhook delivery exception: {str(e)}"

                if attempt < len(self.RETRY_DELAYS):
                    logger.warning(f"{error_msg}. Retrying...")
                    base_delay = self.RETRY_DELAYS[attempt]
                    jittered_delay = self._calculate_jitter(base_delay)
                    await asyncio.sleep(jittered_delay)
                    continue
                else:
                    # Max retries reached
                    delivery.mark_failed(error_message=error_msg)
                    return {
                        'site_id': site_id,
                        'success': False,
                        'error': error_msg,
                        'attempts': attempt + 1
                    }

        # Should never reach here, but safety fallback
        return {
            'site_id': site_id,
            'success': False,
            'error': 'Unexpected end of retry loop',
            'attempts': len(self.RETRY_DELAYS) + 1
        }

    @backoff.on_exception(
        backoff.expo,
        (httpx.ConnectError, httpx.TimeoutException),
        max_tries=3,
        jitter=backoff.full_jitter
    )
    async def _send_webhook_request(
        self,
        url: str,
        payload: Dict[str, Any],
        delivery
    ) -> Dict[str, Any]:
        """
        Send single webhook request with timeout and security
        Uses backoff decorator for connection-level retries
        """
        start_time = time.time()

        try:
            # Mark as sending
            delivery.mark_sent()

            # Generate webhook signature for security
            signature = self._generate_webhook_signature(payload)

            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Huzilerz-Webhook/1.0',
                self.WEBHOOK_SECRET_HEADER: signature,
                'X-Huzilerz-Event-Type': payload['event_type'],
                'X-Huzilerz-Event-ID': payload['event_id'],
                'X-Huzilerz-Delivery-ID': str(delivery.delivery_id)
            }

            # Send request
            response = await self.client.post(
                url,
                json=payload,
                headers=headers
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Check response status
            if 200 <= response.status_code < 300:
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response_body': response.text[:1000],  # Limit size
                    'duration_ms': duration_ms
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': f"HTTP {response.status_code}: {response.text[:500]}",
                    'duration_ms': duration_ms
                }

        except httpx.TimeoutException:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                'success': False,
                'error': f"Request timeout after {self.REQUEST_TIMEOUT}s",
                'duration_ms': duration_ms
            }

        except httpx.ConnectError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                'success': False,
                'error': f"Connection error: {str(e)}",
                'duration_ms': duration_ms
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'duration_ms': duration_ms
            }

    def _calculate_jitter(self, base_delay: int) -> float:
        """
        Calculate jittered delay using full jitter algorithm
        Prevents thundering herd when multiple clients retry simultaneously
        """
        # Full jitter: random between 0 and base_delay
        return random.uniform(0, base_delay)

    def _generate_webhook_signature(self, payload: Dict[str, Any]) -> str:
        """
        Generate HMAC signature for webhook security
        Allows receiving sites to verify webhook authenticity
        """
        import json

        # Get webhook secret from settings
        secret = getattr(settings, 'WEBHOOK_SECRET_KEY', 'default-secret-key')

        # Create payload string
        payload_string = json.dumps(payload, sort_keys=True, separators=(',', ':'))

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    async def _get_deployed_sites(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all active deployed sites for a workspace
        """
        DeployedSite = apps.get_model('hosting', 'DeployedSite')

        sites = DeployedSite.objects.filter(
            workspace_id=workspace_id,
            status='active'
        ).values('id', 'live_url', 'custom_domain')

        return list(sites)

    async def retry_failed_webhooks(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retry failed webhook deliveries
        Called by background task every few minutes
        """
        try:
            SyncEvent = apps.get_model('workspace_sync', 'SyncEvent')

            # Get events that can be retried
            query = SyncEvent.objects.filter(
                sync_status__in=['failed', 'retrying'],
                retry_count__lt=models.F('max_retries')
            )

            if workspace_id:
                query = query.filter(workspace_id=workspace_id)

            failed_events = query[:50]  # Limit batch size

            retry_results = []
            for event in failed_events:
                # Check if enough time has passed since last attempt
                if self._should_retry_event(event):
                    result = await self._retry_sync_event(event)
                    retry_results.append(result)

            return {
                'success': True,
                'events_processed': len(retry_results),
                'results': retry_results
            }

        except Exception as e:
            logger.error(f"Failed to retry webhooks: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _should_retry_event(self, sync_event) -> bool:
        """
        Check if sync event should be retried based on backoff timing
        """
        if sync_event.retry_count >= len(self.RETRY_DELAYS):
            return False

        # Calculate expected retry time
        total_delay = sum(self.RETRY_DELAYS[:sync_event.retry_count])
        retry_time = sync_event.created_at + timedelta(seconds=total_delay)

        return timezone.now() >= retry_time

    async def _retry_sync_event(self, sync_event) -> Dict[str, Any]:
        """
        Retry a failed sync event
        """
        try:
            # Increment retry count
            sync_event.increment_retry()

            # Get sites that haven't been synced yet
            pending_sites = []
            for site_id in sync_event.sites_to_sync:
                if site_id not in sync_event.sites_synced:
                    deployed_sites = await self._get_deployed_sites(sync_event.workspace.id)
                    site = next((s for s in deployed_sites if s['id'] == site_id), None)
                    if site:
                        pending_sites.append(site)

            if not pending_sites:
                sync_event.mark_completed()
                return {
                    'event_id': str(sync_event.event_id),
                    'success': True,
                    'message': 'All sites already synced'
                }

            # Retry delivery to pending sites
            delivery_results = await self._deliver_to_all_sites(
                sync_event, pending_sites, sync_event.event_data
            )

            # Update sync event status
            successful_deliveries = sum(1 for result in delivery_results if result['success'])

            if successful_deliveries == len(pending_sites):
                sync_event.mark_completed()
            elif sync_event.retry_count >= sync_event.max_retries:
                sync_event.mark_failed("Max retries exceeded")

            return {
                'event_id': str(sync_event.event_id),
                'success': successful_deliveries > 0,
                'retry_attempt': sync_event.retry_count,
                'successful_deliveries': successful_deliveries,
                'total_pending': len(pending_sites)
            }

        except Exception as e:
            sync_event.mark_failed(f"Retry failed: {str(e)}")
            return {
                'event_id': str(sync_event.event_id),
                'success': False,
                'error': str(e)
            }

    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()


# Singleton instance for global use
webhook_service = WebhookService()