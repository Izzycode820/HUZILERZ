"""
Cameroon Mobile Money Operator Detection
Handles phone number validation and operator identification for MTN/Orange
"""
import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CameroonOperatorDetector:
    """Detect mobile money operator from Cameroon phone numbers"""
    
    # Cameroon mobile operator prefixes
    MTN_PREFIXES = ['67', '650', '651', '652', '653', '654']
    ORANGE_PREFIXES = ['69', '655', '656', '657', '658', '659']
    
    # Test numbers for sandbox environment (Official Fapshi sandbox numbers)
    # Source: Fapshi documentation
    TEST_NUMBERS = {
        # ✅ Success - MTN Cameroon
        '670000000': 'mobile money',
        '650000000': 'mobile money',
        # ✅ Success - Orange Cameroon
        '690000000': 'orange money',
        '690000002': 'orange money',
        '656000000': 'orange money',
        # ❌ Failure - MTN Cameroon (for testing failure scenarios)
        '670000001': 'mobile money',
        '670000003': 'mobile money',
        '650000001': 'mobile money',
        # ❌ Failure - Orange Cameroon (for testing failure scenarios)
        '690000001': 'orange money',
        '656000001': 'orange money'
    }
    
    @classmethod
    def validate_phone_number(cls, phone: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Validate and format Cameroon phone number
        
        Returns:
            (formatted_phone, error_message)
        """
        if not phone:
            return None, "Phone number is required"
        
        # Remove spaces, dashes, plus signs, and parentheses
        clean_phone = re.sub(r'[\s\-\+\(\)]', '', str(phone))
        
        # Handle test numbers first (for sandbox)
        if clean_phone in cls.TEST_NUMBERS:
            return clean_phone, None
        
        # Remove Cameroon country code if present
        if clean_phone.startswith('237'):
            clean_phone = clean_phone[3:]
        elif clean_phone.startswith('00237'):
            clean_phone = clean_phone[5:]
        
        # Remove leading zero if present
        if clean_phone.startswith('0'):
            clean_phone = clean_phone[1:]
        
        # Validate length (should be 9 digits for Cameroon)
        if not re.match(r'^\d{9}$', clean_phone):
            return None, "Invalid phone number format. Must be 9 digits (example: 670123456)"
        
        # Return with Cameroon country code for international format
        formatted_phone = f"237{clean_phone}"
        return formatted_phone, None
    
    @classmethod
    def detect_operator(cls, phone: str) -> Optional[str]:
        """
        Detect mobile money operator from phone number
        
        Returns:
            'mobile money' for MTN, 'orange money' for Orange, None if unknown
        """
        if not phone:
            return None
        
        # Handle test numbers
        if phone in cls.TEST_NUMBERS:
            return cls.TEST_NUMBERS[phone]
        
        # Clean phone to work with local format
        clean_phone = phone.replace('237', '') if phone.startswith('237') else phone
        
        if len(clean_phone) < 2:
            return None
        
        # Check 3-digit prefixes first (more specific)
        if len(clean_phone) >= 3:
            prefix_3 = clean_phone[:3]
            if prefix_3 in cls.MTN_PREFIXES:
                return 'mobile money'
            elif prefix_3 in cls.ORANGE_PREFIXES:
                return 'orange money'
        
        # Check 2-digit prefixes
        prefix_2 = clean_phone[:2]
        if prefix_2 in cls.MTN_PREFIXES:
            return 'mobile money'
        elif prefix_2 in cls.ORANGE_PREFIXES:
            return 'orange money'
        
        return None
    
    @classmethod
    def get_operator_display_name(cls, operator: str) -> str:
        """Get user-friendly operator name"""
        operator_names = {
            'mobile money': 'MTN Mobile Money',
            'orange money': 'Orange Money'
        }
        return operator_names.get(operator, operator)
    
    @classmethod
    def format_phone_for_display(cls, phone: str) -> str:
        """Format phone number for user display"""
        if not phone:
            return ""
        
        # Handle test numbers
        if phone in cls.TEST_NUMBERS:
            return f"Test: {phone}"
        
        # Format with country code and spacing
        if phone.startswith('237') and len(phone) == 12:
            return f"+237 {phone[3:5]} {phone[5:7]} {phone[7:9]} {phone[9:11]} {phone[11:12]}"
        
        return phone
    
    @classmethod
    def format_phone_for_api(cls, phone: str) -> str:
        """
        Format phone number for Fapshi API (local format without country code)
        """
        if not phone:
            return ""
        
        # Handle test numbers (keep as is)
        if phone in cls.TEST_NUMBERS:
            return phone
        
        # Remove country code for local API format
        if phone.startswith('237'):
            return phone[3:]
        
        return phone
    
    @classmethod
    def is_valid_cameroon_number(cls, phone: str) -> bool:
        """Quick check if phone number is valid for Cameroon"""
        formatted_phone, error = cls.validate_phone_number(phone)
        return formatted_phone is not None and error is None
    
    @classmethod
    def is_test_number(cls, phone: str) -> bool:
        """Check if phone number is a test/sandbox number"""
        clean_phone = re.sub(r'[\s\-\+\(\)]', '', str(phone)) if phone else ""
        return clean_phone in cls.TEST_NUMBERS
    
    @classmethod
    def get_validation_error_message(cls, phone: str) -> str:
        """Get detailed validation error message"""
        if not phone:
            return "Phone number is required"
        
        _, error = cls.validate_phone_number(phone)
        if error:
            return error
        
        operator = cls.detect_operator(phone)
        if not operator:
            return "Unsupported phone number. Please use MTN (67X, 650-654) or Orange (69X, 655-659) numbers."
        
        return ""
    
    @classmethod
    def get_operator_info(cls, phone: str) -> dict:
        """
        Get comprehensive operator information
        
        Returns:
            Dict with operator details, validation status, and formatted numbers
        """
        formatted_phone, validation_error = cls.validate_phone_number(phone)
        
        if validation_error:
            return {
                'is_valid': False,
                'error': validation_error,
                'operator': None,
                'operator_display': None,
                'formatted_phone': None,
                'api_phone': None,
                'is_test_number': False
            }
        
        operator = cls.detect_operator(formatted_phone)
        
        return {
            'is_valid': True,
            'error': None,
            'operator': operator,
            'operator_display': cls.get_operator_display_name(operator) if operator else None,
            'formatted_phone': formatted_phone,
            'display_phone': cls.format_phone_for_display(formatted_phone),
            'api_phone': cls.format_phone_for_api(formatted_phone),
            'is_test_number': cls.is_test_number(phone),
            'country_code': '237'
        }