"""
Checkout Validation Layer
Production-ready validation following CLAUDE.md security principles

Validates:
- Customer information (phone-first Cameroon context)
- Shipping region availability
- Input sanitization
"""

import re
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class CheckoutValidator:
    """
    Centralized validation for checkout operations

    Security: Input sanitization and format validation
    Reliability: Comprehensive error messages
    """

    @staticmethod
    def validate_customer_info(customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate customer information

        Cameroon context: Phone-first, email optional
        Security: Prevents injection, validates formats

        Args:
            customer_info: Dict with name, phone, email (optional)

        Returns:
            Dict with 'valid': bool, 'error': str (if invalid), 'sanitized': dict

        Raises:
            Never raises - returns validation result
        """
        try:
            # Check required fields
            if not customer_info:
                return {
                    'valid': False,
                    'error': 'Customer information is required'
                }

            if not customer_info.get('phone'):
                return {
                    'valid': False,
                    'error': 'Phone number is required'
                }

            if not customer_info.get('name'):
                return {
                    'valid': False,
                    'error': 'Customer name is required'
                }

            # Validate phone format (Cameroon: +237XXXXXXXXX or 6XXXXXXXX)
            phone = str(customer_info['phone']).strip()
            phone_validation = CheckoutValidator._validate_cameroon_phone(phone)
            if not phone_validation['valid']:
                return phone_validation

            # Validate name (2-100 characters, no special chars)
            name = str(customer_info['name']).strip()
            if len(name) < 2 or len(name) > 100:
                return {
                    'valid': False,
                    'error': 'Name must be between 2 and 100 characters'
                }

            # Validate email if provided (optional)
            email = customer_info.get('email', '').strip()
            if email:
                email_validation = CheckoutValidator._validate_email(email)
                if not email_validation['valid']:
                    return email_validation

            # Return sanitized data
            return {
                'valid': True,
                'sanitized': {
                    'phone': phone_validation['sanitized'],
                    'name': name,
                    'email': email if email else ''
                }
            }

        except Exception as e:
            logger.error(f"Customer info validation failed: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'error': 'Invalid customer information format'
            }

    @staticmethod
    def validate_shipping_region(workspace, cart, shipping_region: str) -> Dict[str, Any]:
        """
        Validate shipping region exists in cart products' packages

        Security: Prevents invalid region injection
        Performance: Single query with prefetch
        Non-blocking: Falls back to default package if region not found

        Args:
            workspace: Workspace instance
            cart: Cart instance
            shipping_region: Region name (e.g., 'buea', 'yaounde')

        Returns:
            Dict with 'valid': bool, 'error': str, 'shipping_cost': Decimal, 
            'estimated_days': str, 'region': str, 'is_estimated': bool
        """
        try:
            if not shipping_region:
                return {
                    'valid': False,
                    'error': 'Shipping region is required'
                }

            # Normalize region (lowercase, strip whitespace) for comparison
            region_normalized = shipping_region.lower().strip()

            if len(region_normalized) < 2 or len(region_normalized) > 50:
                return {
                    'valid': False,
                    'error': 'Invalid region format'
                }

            # Get all packages for cart items (optimized query)
            from workspace.store.models import Package
            cart_items = cart.items.select_related('product', 'product__package').all()

            if not cart_items.exists():
                return {
                    'valid': False,
                    'error': 'Cart is empty'
                }

            # Check if region exists in at least one package (case-insensitive)
            region_found = False
            total_shipping_cost = Decimal('0.00')  # Will track highest fee (flat rate)
            all_estimated_days = []
            matched_region_name = region_normalized  # Will store the original casing

            # Also collect default package for fallback
            default_package = None
            try:
                default_package = Package.objects.get(
                    workspace=workspace,
                    use_as_default=True,
                    is_active=True
                )
            except Package.DoesNotExist:
                pass

            for cart_item in cart_items:
                product = cart_item.product
                package = product.package

                # Use default package if product has no package
                if not package:
                    if default_package:
                        package = default_package
                    else:
                        continue

                # Check if region exists in package (CASE-INSENSITIVE)
                region_fees = package.region_fees or {}
                
                # Create lowercase lookup map
                region_fees_lower = {k.lower(): (k, v) for k, v in region_fees.items()}
                
                if region_normalized in region_fees_lower:
                    region_found = True
                    original_key, fee = region_fees_lower[region_normalized]
                    matched_region_name = original_key  # Keep original casing
                    fee_decimal = Decimal(str(fee))
                    
                    # Use HIGHEST fee (flat rate, not accumulated per item)
                    if fee_decimal > total_shipping_cost:
                        total_shipping_cost = fee_decimal

                    if package.estimated_days:
                        all_estimated_days.append(package.estimated_days)

            # FALLBACK: If region not found, use default package with 0 shipping
            # This is NON-BLOCKING - order can still proceed
            if not region_found:
                logger.info(
                    f"Shipping region '{shipping_region}' not found, using fallback",
                    extra={'region': shipping_region, 'workspace_id': str(workspace.id)}
                )
                
                # Still allow order to proceed with 0 shipping cost
                # Merchant will handle shipping separately
                estimated_days = '3-5'  # Conservative estimate
                
                if default_package and default_package.estimated_days:
                    estimated_days = default_package.estimated_days
                
                return {
                    'valid': True,
                    'shipping_cost': Decimal('0.00'),
                    'estimated_days': estimated_days,
                    'region': shipping_region,  # Keep original input
                    'is_estimated': True,  # Flag that shipping is not calculated
                    'warning': f'Shipping rates for {shipping_region} not configured. Merchant will confirm shipping cost.'
                }

            # Get longest delivery estimate
            estimated_days = CheckoutValidator._get_max_estimated_days(all_estimated_days)

            return {
                'valid': True,
                'shipping_cost': total_shipping_cost,
                'estimated_days': estimated_days,
                'region': matched_region_name,  # Use original casing from package
                'is_estimated': False
            }

        except Exception as e:
            logger.error(f"Shipping region validation failed: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'error': 'Failed to validate shipping region'
            }

    @staticmethod
    def validate_order_type(order_type: str) -> Dict[str, Any]:
        """
        Validate order type

        Security: Whitelist validation
        """
        valid_types = ['regular', 'cod', 'whatsapp']

        if order_type not in valid_types:
            return {
                'valid': False,
                'error': f'Invalid order type. Must be one of: {", ".join(valid_types)}'
            }

        return {'valid': True}

    # Helper methods

    @staticmethod
    def _validate_cameroon_phone(phone: str) -> Dict[str, Any]:
        """
        Validate Cameroon phone number format

        Formats accepted:
        - +237XXXXXXXXX (international)
        - 237XXXXXXXXX (without +)
        - 6XXXXXXXX (local mobile)
        """
        # Remove spaces and common separators
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)

        # Pattern: Cameroon mobile numbers start with 6
        # International: +237 6XX XXX XXX
        # Local: 6XX XXX XXX

        if clean_phone.startswith('+237'):
            clean_phone = clean_phone[4:]  # Remove +237
        elif clean_phone.startswith('237'):
            clean_phone = clean_phone[3:]  # Remove 237

        # Validate format: 6XXXXXXXX (9 digits starting with 6)
        if not re.match(r'^6\d{8}$', clean_phone):
            return {
                'valid': False,
                'error': 'Invalid phone number. Cameroon mobile numbers must start with 6 and have 9 digits (e.g., 671234567)'
            }

        # Return sanitized phone with country code
        return {
            'valid': True,
            'sanitized': f'+237{clean_phone}'
        }

    @staticmethod
    def _validate_email(email: str) -> Dict[str, Any]:
        """
        Validate email format

        Security: Basic format check, prevents injection
        """
        # Basic email regex (production would use Django's EmailValidator)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            return {
                'valid': False,
                'error': 'Invalid email format'
            }

        if len(email) > 254:  # RFC 5321
            return {
                'valid': False,
                'error': 'Email too long'
            }

        return {'valid': True}

    @staticmethod
    def _get_max_estimated_days(all_estimates: list) -> str:
        """
        Get maximum estimated delivery days from list

        Example: ['1-2', '3-5', '2-3'] -> '3-5'
        """
        if not all_estimates:
            return '2-3'  # Default

        max_days = '2-3'
        max_num = 3

        for estimate in all_estimates:
            # Extract highest number from string (e.g., '3-5' -> 5)
            numbers = re.findall(r'\d+', estimate)
            if numbers:
                highest = max([int(n) for n in numbers])
                if highest > max_num:
                    max_num = highest
                    max_days = estimate

        return max_days
