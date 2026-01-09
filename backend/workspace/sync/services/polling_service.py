"""
Polling Backup Service
1-minute polling system as backup when webhooks fail
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import models, transaction
from django.apps import apps
from django.core.exceptions import ValidationError
from workspace.core.services.base_data_export_service import workspace_data_export_service
from .webhook_service import webhook_service
import logging

logger = logging.getLogger('workspace.sync.polling')


class PollingBackupService:
    """
    1-minute polling backup system for data synchronization
    Ensures eventual consistency when webhooks fail
    """

    # Polling configuration
    POLL_INTERVAL_SECONDS = 60  # 1 minute
    MAX_POLLING_ERRORS = 10
    BATCH_SIZE = 50  # Process up to 50 workspaces per cycle

    def __init__(self):
        self.is_running = False
        self.polling_tasks = {}

    async def start_polling_for_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """
        Start polling for a specific workspace

        Args:
            workspace_id: UUID of the workspace to monitor

        Returns:
            Dict with start result
        """
        try:
            # Initialize or get polling state
            polling_state = await self._get_or_create_polling_state(workspace_id)

            # Start polling task if not already running
            if workspace_id not in self.polling_tasks:
                task = asyncio.create_task(
                    self._polling_loop_for_workspace(workspace_id)
                )
                self.polling_tasks[workspace_id] = task

                logger.info(f"Started polling for workspace {workspace_id}")

                return {
                    'success': True,
                    'workspace_id': workspace_id,
                    'polling_active': True,
                    'next_poll_at': polling_state.next_poll_at.isoformat()
                }
            else:
                return {
                    'success': True,
                    'workspace_id': workspace_id,
                    'message': 'Polling already active for this workspace'
                }

        except Exception as e:
            logger.error(f"Failed to start polling for workspace {workspace_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def stop_polling_for_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """
        Stop polling for a specific workspace

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Dict with stop result
        """
        try:
            # Cancel polling task if running
            if workspace_id in self.polling_tasks:
                task = self.polling_tasks[workspace_id]
                task.cancel()
                del self.polling_tasks[workspace_id]

                # Update polling state
                PollingState = apps.get_model('workspace_sync', 'PollingState')
                PollingState.objects.filter(
                    workspace_id=workspace_id
                ).update(
                    is_polling_active=False,
                    updated_at=timezone.now()
                )

                logger.info(f"Stopped polling for workspace {workspace_id}")

                return {
                    'success': True,
                    'workspace_id': workspace_id,
                    'polling_active': False
                }
            else:
                return {
                    'success': True,
                    'workspace_id': workspace_id,
                    'message': 'Polling was not active for this workspace'
                }

        except Exception as e:
            logger.error(f"Failed to stop polling for workspace {workspace_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def start_global_polling(self) -> Dict[str, Any]:
        """
        Start global polling for all active workspaces
        """
        try:
            if self.is_running:
                return {
                    'success': True,
                    'message': 'Global polling already running'
                }

            self.is_running = True

            # Start global polling task
            asyncio.create_task(self._global_polling_loop())

            logger.info("Started global polling service")

            return {
                'success': True,
                'message': 'Global polling started'
            }

        except Exception as e:
            logger.error(f"Failed to start global polling: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _global_polling_loop(self):
        """
        Global polling loop that manages all workspace polling
        """
        while self.is_running:
            try:
                # Get workspaces that need polling
                workspaces_to_poll = await self._get_workspaces_due_for_polling()

                if workspaces_to_poll:
                    logger.info(f"Polling {len(workspaces_to_poll)} workspaces")

                    # Process workspaces in parallel with semaphore
                    semaphore = asyncio.Semaphore(10)  # Limit concurrent polling
                    polling_tasks = [
                        self._poll_workspace_with_semaphore(semaphore, workspace_id)
                        for workspace_id in workspaces_to_poll
                    ]

                    # Wait for all polling tasks to complete
                    await asyncio.gather(*polling_tasks, return_exceptions=True)

                # Wait before next polling cycle
                await asyncio.sleep(self.POLL_INTERVAL_SECONDS)

            except Exception as e:
                logger.error(f"Error in global polling loop: {str(e)}")
                await asyncio.sleep(self.POLL_INTERVAL_SECONDS)

    async def _polling_loop_for_workspace(self, workspace_id: str):
        """
        Polling loop for a specific workspace
        """
        while workspace_id in self.polling_tasks:
            try:
                # Check if it's time to poll this workspace
                polling_state = await self._get_polling_state(workspace_id)

                if polling_state and timezone.now() >= polling_state.next_poll_at:
                    await self._poll_workspace(workspace_id)

                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                logger.info(f"Polling cancelled for workspace {workspace_id}")
                break
            except Exception as e:
                logger.error(f"Error in polling loop for workspace {workspace_id}: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _poll_workspace_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        workspace_id: str
    ):
        """
        Poll workspace with semaphore control for concurrency
        """
        async with semaphore:
            await self._poll_workspace(workspace_id)

    async def _poll_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """
        Poll a single workspace for data changes

        Args:
            workspace_id: UUID of the workspace to poll

        Returns:
            Dict with polling result
        """
        try:
            # Get polling state
            polling_state = await self._get_polling_state(workspace_id)
            if not polling_state:
                return {'success': False, 'error': 'No polling state found'}

            # Get workspace
            Workspace = apps.get_model('core', 'Workspace')
            workspace = Workspace.objects.get(id=workspace_id, is_active=True)

            # Check for changes since last poll
            changes_detected = await self._detect_workspace_changes(
                workspace, polling_state.last_poll_at
            )

            if changes_detected:
                logger.info(f"Changes detected in workspace {workspace_id}, triggering sync")

                # Trigger sync for detected changes
                await self._sync_detected_changes(workspace_id, changes_detected)

                # Mark poll as completed with changes
                polling_state.mark_poll_completed(changes_detected=True)
            else:
                # Mark poll as completed without changes
                polling_state.mark_poll_completed(changes_detected=False)

            return {
                'success': True,
                'workspace_id': workspace_id,
                'changes_detected': bool(changes_detected),
                'change_count': len(changes_detected) if changes_detected else 0
            }

        except Exception as e:
            logger.error(f"Failed to poll workspace {workspace_id}: {str(e)}")

            # Mark polling as failed
            if polling_state:
                polling_state.mark_poll_failed()

            return {
                'success': False,
                'workspace_id': workspace_id,
                'error': str(e)
            }

    async def _detect_workspace_changes(
        self,
        workspace,
        last_poll_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Detect changes in workspace data since last poll

        Args:
            workspace: Workspace instance
            last_poll_time: Last successful poll time

        Returns:
            List of detected changes
        """
        changes = []

        try:
            # Check different workspace types for changes
            workspace_type = workspace.type

            if workspace_type == 'store':
                changes.extend(await self._detect_store_changes(workspace.id, last_poll_time))
            elif workspace_type == 'blog':
                changes.extend(await self._detect_blog_changes(workspace.id, last_poll_time))
            elif workspace_type == 'services':
                changes.extend(await self._detect_services_changes(workspace.id, last_poll_time))

            # Check workspace-level changes
            changes.extend(await self._detect_workspace_level_changes(workspace.id, last_poll_time))

            return changes

        except Exception as e:
            logger.error(f"Failed to detect changes for workspace {workspace.id}: {str(e)}")
            return []

    async def _detect_store_changes(self, workspace_id: str, since: datetime) -> List[Dict[str, Any]]:
        """Detect changes in store workspace"""
        changes = []

        try:
            # Check for product changes
            Product = apps.get_model('store', 'Product')
            changed_products = Product.objects.filter(
                workspace_id=workspace_id,
                updated_at__gt=since
            ).values('id', 'name', 'updated_at')

            for product in changed_products:
                changes.append({
                    'type': 'product.updated',
                    'entity_type': 'Product',
                    'entity_id': str(product['id']),
                    'entity_name': product['name'],
                    'changed_at': product['updated_at'].isoformat()
                })

            # Check for order changes
            Order = apps.get_model('store', 'Order')
            changed_orders = Order.objects.filter(
                workspace_id=workspace_id,
                updated_at__gt=since
            ).values('id', 'order_number', 'updated_at')

            for order in changed_orders:
                changes.append({
                    'type': 'order.updated',
                    'entity_type': 'Order',
                    'entity_id': str(order['id']),
                    'entity_name': order['order_number'],
                    'changed_at': order['updated_at'].isoformat()
                })

        except Exception as e:
            logger.warning(f"Failed to detect store changes: {str(e)}")

        return changes

    async def _detect_blog_changes(self, workspace_id: str, since: datetime) -> List[Dict[str, Any]]:
        """Detect changes in blog workspace"""
        changes = []

        try:
            # Check for post changes
            BaseWorkspaceContentModel = apps.get_model('core', 'BaseWorkspaceContentModel')
            changed_posts = BaseWorkspaceContentModel.objects.filter(
                workspace_id=workspace_id,
                updated_at__gt=since
            ).values('id', 'title', 'updated_at', 'status')

            for post in changed_posts:
                # Determine event type based on status
                event_type = 'post.updated'
                if post['status'] == 'published':
                    event_type = 'post.published'

                changes.append({
                    'type': event_type,
                    'entity_type': 'Post',
                    'entity_id': str(post['id']),
                    'entity_name': post['title'],
                    'changed_at': post['updated_at'].isoformat()
                })

        except Exception as e:
            logger.warning(f"Failed to detect blog changes: {str(e)}")

        return changes

    async def _detect_services_changes(self, workspace_id: str, since: datetime) -> List[Dict[str, Any]]:
        """Detect changes in services workspace"""
        changes = []

        try:
            # Check for service changes
            Service = apps.get_model('services', 'Service')
            changed_services = Service.objects.filter(
                workspace_id=workspace_id,
                updated_at__gt=since
            ).values('id', 'name', 'updated_at')

            for service in changed_services:
                changes.append({
                    'type': 'service.updated',
                    'entity_type': 'Service',
                    'entity_id': str(service['id']),
                    'entity_name': service['name'],
                    'changed_at': service['updated_at'].isoformat()
                })

            # Check for booking changes
            Booking = apps.get_model('services', 'Booking')
            changed_bookings = Booking.objects.filter(
                service__workspace_id=workspace_id,
                updated_at__gt=since
            ).values('id', 'service__name', 'updated_at')

            for booking in changed_bookings:
                changes.append({
                    'type': 'booking.updated',
                    'entity_type': 'Booking',
                    'entity_id': str(booking['id']),
                    'entity_name': f"Booking for {booking['service__name']}",
                    'changed_at': booking['updated_at'].isoformat()
                })

        except Exception as e:
            logger.warning(f"Failed to detect services changes: {str(e)}")

        return changes

    async def _detect_workspace_level_changes(self, workspace_id: str, since: datetime) -> List[Dict[str, Any]]:
        """Detect workspace-level changes (settings, branding, etc.)"""
        changes = []

        try:
            # Check workspace settings changes
            Workspace = apps.get_model('core', 'Workspace')
            workspace = Workspace.objects.filter(
                id=workspace_id,
                updated_at__gt=since
            ).first()

            if workspace:
                changes.append({
                    'type': 'workspace.settings_updated',
                    'entity_type': 'Workspace',
                    'entity_id': str(workspace.id),
                    'entity_name': workspace.name,
                    'changed_at': workspace.updated_at.isoformat()
                })

        except Exception as e:
            logger.warning(f"Failed to detect workspace-level changes: {str(e)}")

        return changes

    async def _sync_detected_changes(self, workspace_id: str, changes: List[Dict[str, Any]]):
        """
        Trigger sync for detected changes using webhook service
        """
        try:
            for change in changes:
                # Get full entity data for sync
                entity_data = await self._get_entity_data(
                    change['entity_type'],
                    change['entity_id']
                )

                if entity_data:
                    # Send webhook using the webhook service
                    await webhook_service.send_workspace_webhook(
                        workspace_id=workspace_id,
                        event_type=change['type'],
                        data=entity_data,
                        entity_type=change['entity_type'],
                        entity_id=change['entity_id']
                    )

        except Exception as e:
            logger.error(f"Failed to sync detected changes: {str(e)}")

    async def _get_entity_data(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full entity data for synchronization
        """
        try:
            if entity_type == 'Product':
                Product = apps.get_model('store', 'Product')
                product = Product.objects.get(id=entity_id)
                return {
                    'id': str(product.id),
                    'name': product.name,
                    'description': product.description,
                    'price': str(product.price),
                    'featured_image': product.featured_image,
                    'is_active': product.is_active
                }

            elif entity_type == 'Post':
                BaseWorkspaceContentModel = apps.get_model('core', 'BaseWorkspaceContentModel')
                post = BaseWorkspaceContentModel.objects.get(id=entity_id)
                return {
                    'id': str(post.id),
                    'title': post.title,
                    'content': post.content,
                    'excerpt': post.excerpt,
                    'featured_image': post.featured_image,
                    'status': post.status,
                    'is_active': post.is_active
                }

            elif entity_type == 'Service':
                Service = apps.get_model('services', 'Service')
                service = Service.objects.get(id=entity_id)
                return {
                    'id': str(service.id),
                    'name': service.name,
                    'description': service.description,
                    'price': str(service.price),
                    'duration_minutes': service.duration_minutes,
                    'is_active': service.is_active
                }

            # Add more entity types as needed

            return None

        except Exception as e:
            logger.error(f"Failed to get entity data for {entity_type}:{entity_id}: {str(e)}")
            return None

    async def _get_workspaces_due_for_polling(self) -> List[str]:
        """
        Get workspaces that are due for polling
        """
        try:
            PollingState = apps.get_model('workspace_sync', 'PollingState')

            # Get workspaces due for polling
            due_states = PollingState.objects.filter(
                is_polling_active=True,
                next_poll_at__lte=timezone.now()
            )[:self.BATCH_SIZE]

            return [str(state.workspace.id) for state in due_states]

        except Exception as e:
            logger.error(f"Failed to get workspaces due for polling: {str(e)}")
            return []

    async def _get_or_create_polling_state(self, workspace_id: str):
        """
        Get or create polling state for workspace
        """
        try:
            PollingState = apps.get_model('workspace_sync', 'PollingState')
            Workspace = apps.get_model('core', 'Workspace')

            workspace = Workspace.objects.get(id=workspace_id)

            polling_state, created = PollingState.objects.get_or_create(
                workspace=workspace,
                defaults={
                    'last_poll_at': timezone.now(),
                    'next_poll_at': timezone.now() + timedelta(seconds=self.POLL_INTERVAL_SECONDS),
                    'is_polling_active': True
                }
            )

            return polling_state

        except Exception as e:
            logger.error(f"Failed to get/create polling state: {str(e)}")
            return None

    async def _get_polling_state(self, workspace_id: str):
        """
        Get existing polling state for workspace
        """
        try:
            PollingState = apps.get_model('workspace_sync', 'PollingState')
            return PollingState.objects.get(workspace_id=workspace_id)
        except:
            return None

    def get_polling_status(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current polling status

        Args:
            workspace_id: Optional workspace ID to get specific status

        Returns:
            Dict with polling status information
        """
        try:
            PollingState = apps.get_model('workspace_sync', 'PollingState')

            if workspace_id:
                # Get status for specific workspace
                try:
                    state = PollingState.objects.get(workspace_id=workspace_id)
                    return {
                        'workspace_id': workspace_id,
                        'is_active': state.is_polling_active,
                        'last_poll_at': state.last_poll_at.isoformat(),
                        'next_poll_at': state.next_poll_at.isoformat(),
                        'consecutive_failures': state.consecutive_failures,
                        'is_healthy': state.is_healthy
                    }
                except PollingState.DoesNotExist:
                    return {
                        'workspace_id': workspace_id,
                        'is_active': False,
                        'message': 'No polling state found'
                    }
            else:
                # Get global status
                total_workspaces = PollingState.objects.count()
                active_workspaces = PollingState.objects.filter(is_polling_active=True).count()
                healthy_workspaces = PollingState.objects.filter(
                    is_polling_active=True,
                    consecutive_failures__lt=5
                ).count()

                return {
                    'global_polling_active': self.is_running,
                    'total_workspaces': total_workspaces,
                    'active_workspaces': active_workspaces,
                    'healthy_workspaces': healthy_workspaces,
                    'active_tasks': len(self.polling_tasks)
                }

        except Exception as e:
            logger.error(f"Failed to get polling status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance for global use
polling_service = PollingBackupService()