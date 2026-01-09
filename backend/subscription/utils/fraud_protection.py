"""
Fraud protection system for payment processing
Implements risk assessment and velocity checking
"""
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

class PaymentFraudProtection:
    """
    Comprehensive fraud protection for payment processing
    Implements multiple layers of security checks
    """
    
    # Risk score thresholds
    LOW_RISK_THRESHOLD = 25
    MEDIUM_RISK_THRESHOLD = 50
    HIGH_RISK_THRESHOLD = 75
    
    @classmethod
    def validate_phone_number_patterns(cls, phone_number: str) -> Tuple[bool, int, List[str]]:
        """
        Validate phone number for suspicious patterns
        
        Returns:
            (is_valid, risk_score, flags)
        """
        flags = []
        risk_score = 0
        
        if not phone_number:
            return False, 100, ['MISSING_PHONE']
        
        # Clean phone number for analysis
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        
        # Check length
        if len(clean_phone) < 9 or len(clean_phone) > 15:
            flags.append('INVALID_LENGTH')
            risk_score += 30
        
        # Check for repeated digits (e.g., 1111111111)
        if len(set(clean_phone)) <= 3 and len(clean_phone) >= 8:
            flags.append('REPEATED_DIGITS')
            risk_score += 50
        
        # Check for sequential patterns
        sequential_patterns = ['0123456789', '1234567890', '9876543210']
        if any(pattern in clean_phone for pattern in sequential_patterns):
            flags.append('SEQUENTIAL_PATTERN')
            risk_score += 40
        
        # Check for known test/fake numbers patterns
        fake_patterns = ['123456789', '000000000', '111111111', '999999999']
        if any(pattern in clean_phone for pattern in fake_patterns):
            flags.append('FAKE_NUMBER_PATTERN')
            risk_score += 35
        
        # Check for Cameroon test numbers (lower risk in development)
        test_patterns = ['467331234', '467890123']
        if any(pattern in clean_phone for pattern in test_patterns):
            flags.append('TEST_NUMBER')
            risk_score += 5  # Very low risk for legitimate test numbers
        
        is_valid = risk_score < cls.HIGH_RISK_THRESHOLD
        return is_valid, risk_score, flags
    
    @classmethod
    def check_payment_velocity(
        cls, 
        user, 
        amount: float, 
        time_window_minutes: int = 60
    ) -> Tuple[bool, int, Optional[timezone.datetime]]:
        """
        Check if user is making too many payment attempts
        
        Returns:
            (is_allowed, remaining_attempts, next_allowed_time)
        """
        cache_key = f"payment_velocity:{user.id}"
        now = timezone.now()
        
        # Get recent payment attempts
        attempts = cache.get(cache_key, [])
        
        # Filter attempts within time window
        cutoff_time = now - timedelta(minutes=time_window_minutes)
        recent_attempts = [
            attempt for attempt in attempts 
            if attempt['timestamp'] > cutoff_time
        ]
        
        # Calculate totals
        attempt_count = len(recent_attempts)
        total_amount = sum(attempt['amount'] for attempt in recent_attempts)
        
        # Define limits based on risk assessment
        max_attempts = cls._get_velocity_limits(user)['max_attempts']
        max_amount = cls._get_velocity_limits(user)['max_amount']
        
        # Check attempt limit
        if attempt_count >= max_attempts:
            oldest_attempt = min(recent_attempts, key=lambda x: x['timestamp'])
            next_allowed = oldest_attempt['timestamp'] + timedelta(minutes=time_window_minutes)
            return False, 0, next_allowed
        
        # Check amount limit
        if total_amount + amount > max_amount:
            return False, max_attempts - attempt_count, None
        
        # Add current attempt to tracking
        recent_attempts.append({
            'timestamp': now,
            'amount': amount,
            'user_id': user.id,
            'ip_address': getattr(user, '_current_ip', 'unknown')
        })
        
        # Store updated attempts
        cache.set(cache_key, recent_attempts, time_window_minutes * 60 + 300)
        
        remaining_attempts = max_attempts - len(recent_attempts)
        return True, remaining_attempts, None
    
    @classmethod
    def _get_velocity_limits(cls, user) -> Dict[str, int]:
        """Get velocity limits based on user profile"""
        # Check user account age and history
        account_age_days = (timezone.now() - user.date_joined).days
        
        # New users have stricter limits
        if account_age_days < 1:
            return {'max_attempts': 2, 'max_amount': 15000}
        elif account_age_days < 7:
            return {'max_attempts': 3, 'max_amount': 25000}
        elif account_age_days < 30:
            return {'max_attempts': 4, 'max_amount': 40000}
        else:
            return {'max_attempts': 5, 'max_amount': 50000}
    
    @classmethod
    def analyze_transaction_risk(cls, payment_data: Dict) -> Dict[str, any]:
        """
        Comprehensive transaction risk analysis
        
        Returns:
            Risk assessment with score and recommendations
        """
        risk_factors = []
        risk_score = 0
        
        user = payment_data.get('user')
        amount = payment_data.get('amount', 0)
        phone_number = payment_data.get('phone_number', '')
        
        # Phone number risk assessment
        phone_valid, phone_risk, phone_flags = cls.validate_phone_number_patterns(phone_number)
        if not phone_valid:
            risk_factors.extend([f"PHONE_{flag}" for flag in phone_flags])
            risk_score += phone_risk
        
        # Amount-based risk assessment
        if amount > 50000:  # High value for Cameroon context
            risk_factors.append('HIGH_VALUE_TRANSACTION')
            risk_score += 25
        elif amount > 100000:  # Very high value
            risk_factors.append('VERY_HIGH_VALUE')
            risk_score += 40
        
        if amount < 500:  # Suspiciously low amount
            risk_factors.append('SUSPICIOUS_LOW_AMOUNT')
            risk_score += 15
        
        # User account risk factors
        if user:
            account_age_days = (timezone.now() - user.date_joined).days
            
            if account_age_days < 1:
                risk_factors.append('BRAND_NEW_ACCOUNT')
                risk_score += 35
            elif account_age_days < 7:
                risk_factors.append('VERY_NEW_ACCOUNT')
                risk_score += 20
            elif account_age_days < 30:
                risk_factors.append('NEW_ACCOUNT')
                risk_score += 10
            
            # Check user's payment history
            payment_history_risk = cls._assess_payment_history_risk(user)
            risk_score += payment_history_risk['score']
            risk_factors.extend(payment_history_risk['factors'])
        
        # Velocity risk assessment
        if user:
            velocity_ok, remaining, next_allowed = cls.check_payment_velocity(user, amount)
            if not velocity_ok:
                risk_factors.append('HIGH_PAYMENT_VELOCITY')
                risk_score += 45
        
        # Time-based risk factors
        current_hour = timezone.now().hour
        if current_hour < 6 or current_hour > 23:  # Late night/early morning
            risk_factors.append('UNUSUAL_TIME')
            risk_score += 10
        
        # Weekend risk (slightly higher)
        if timezone.now().weekday() >= 5:  # Saturday/Sunday
            risk_factors.append('WEEKEND_TRANSACTION')
            risk_score += 5
        
        # Determine risk level and recommendations
        risk_level = cls._calculate_risk_level(risk_score)
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'allow_transaction': risk_score < cls.HIGH_RISK_THRESHOLD,
            'requires_verification': risk_score >= cls.MEDIUM_RISK_THRESHOLD,
            'requires_manual_review': risk_score >= cls.HIGH_RISK_THRESHOLD,
            'recommendations': cls._generate_risk_recommendations(risk_level, risk_factors)
        }
    
    @classmethod
    def _assess_payment_history_risk(cls, user) -> Dict[str, any]:
        """Assess risk based on user's payment history"""
        risk_score = 0
        factors = []
        
        try:
            from ..models import Payment
            
            # Get user's recent payments (last 30 days)
            recent_payments = Payment.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            failed_payments = recent_payments.filter(status='failed').count()
            total_payments = recent_payments.count()
            
            if total_payments == 0:
                factors.append('NO_PAYMENT_HISTORY')
                risk_score += 15
            else:
                failure_rate = failed_payments / total_payments
                
                if failure_rate > 0.5:  # More than 50% failure rate
                    factors.append('HIGH_FAILURE_RATE')
                    risk_score += 30
                elif failure_rate > 0.3:  # More than 30% failure rate
                    factors.append('MODERATE_FAILURE_RATE')
                    risk_score += 15
            
            # Check for rapid successive attempts
            recent_attempts = recent_payments.filter(
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
            
            if recent_attempts > 3:
                factors.append('RAPID_SUCCESSIVE_ATTEMPTS')
                risk_score += 25
        
        except Exception as e:
            logger.error(f"Payment history risk assessment failed: {str(e)}")
            factors.append('HISTORY_ASSESSMENT_ERROR')
            risk_score += 10
        
        return {'score': risk_score, 'factors': factors}
    
    @classmethod
    def _calculate_risk_level(cls, risk_score: int) -> str:
        """Calculate risk level from score"""
        if risk_score >= cls.HIGH_RISK_THRESHOLD:
            return 'HIGH'
        elif risk_score >= cls.MEDIUM_RISK_THRESHOLD:
            return 'MEDIUM'
        elif risk_score >= cls.LOW_RISK_THRESHOLD:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    @classmethod
    def _generate_risk_recommendations(cls, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Generate recommendations based on risk assessment"""
        recommendations = []
        
        if risk_level == 'HIGH':
            recommendations.extend([
                'Block transaction pending manual review',
                'Require additional identity verification',
                'Contact user via verified channels'
            ])
        
        elif risk_level == 'MEDIUM':
            recommendations.extend([
                'Require phone verification',
                'Add additional fraud checks',
                'Monitor transaction closely'
            ])
        
        elif risk_level == 'LOW':
            recommendations.extend([
                'Process with standard monitoring',
                'Log for pattern analysis'
            ])
        
        # Specific recommendations based on risk factors
        if 'HIGH_VALUE_TRANSACTION' in risk_factors:
            recommendations.append('Verify transaction amount with user')
        
        if 'NEW_ACCOUNT' in risk_factors:
            recommendations.append('Implement account verification steps')
        
        if 'HIGH_PAYMENT_VELOCITY' in risk_factors:
            recommendations.append('Enforce cooling-off period')
        
        return recommendations
    
    @classmethod
    def log_fraud_assessment(cls, user, assessment: Dict[str, any]):
        """Log fraud assessment for monitoring and analysis"""
        logger.info(
            f"FRAUD_ASSESSMENT: User={user.id if user else 'None'} "
            f"RiskLevel={assessment['risk_level']} "
            f"Score={assessment['risk_score']} "
            f"Factors={','.join(assessment['risk_factors'][:5])}"  # Limit to first 5 factors
        )
        
        # Log high-risk transactions separately
        if assessment['risk_level'] == 'HIGH':
            logger.warning(
                f"HIGH_RISK_TRANSACTION: User={user.id if user else 'None'} "
                f"Score={assessment['risk_score']} "
                f"AllFactors={assessment['risk_factors']}"
            )
    
    @classmethod
    def should_block_transaction(cls, assessment: Dict[str, any]) -> bool:
        """Determine if transaction should be blocked"""
        return (
            assessment['risk_score'] >= cls.HIGH_RISK_THRESHOLD or
            'FAKE_NUMBER_PATTERN' in assessment['risk_factors'] or
            'REPEATED_DIGITS' in assessment['risk_factors']
        )
    
    @classmethod
    def get_fraud_prevention_headers(cls) -> Dict[str, str]:
        """Get headers for fraud prevention API calls"""
        return {
            'X-Fraud-Check': 'enabled',
            'X-Risk-Assessment': 'comprehensive',
            'User-Agent': 'HUZILERZ-FraudProtection/1.0'
        }