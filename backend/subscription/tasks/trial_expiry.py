"""
Trial Expiry Handler
Celery task to check and handle expired trials
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


@shared_task(name='subscription.tasks.check_trial_expiry')
def check_trial_expiry():
    """
    Check for expired trials and handle them
    Runs daily via Celery Beat
    """
    try:
        from ..models.trial import Trial
        from ..services.trial_service import TrialService

        # Get trials that have expired but status not updated
        expired_trials = Trial.objects.filter(
            status='active',
            expires_at__lte=timezone.now()
        ).select_related('user')

        expired_count = 0

        for trial in expired_trials:
            try:
                # Call service to handle expiry (emits signals, updates status)
                TrialService.handle_trial_expiry(trial)
                expired_count += 1
                logger.info(f"Processed expired trial for {trial.user.email} - {trial.tier}")

            except Exception as e:
                logger.error(f"Failed to process expired trial {trial.id}: {str(e)}", exc_info=True)
                continue

        logger.info(f"Trial expiry check completed: {expired_count} trials expired")

        return {
            'success': True,
            'expired_count': expired_count,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Trial expiry check failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
