"""
Domain Registrar Service
Interface with Namecheap/GoDaddy APIs for domain registration
Production-ready with mock mode for development
"""
import logging
import requests
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class DomainRegistrarService:
    """
    Unified interface for domain registrar operations
    Supports Namecheap and GoDaddy APIs
    """

    def __init__(self, registrar: str = 'namecheap'):
        """
        Initialize registrar service

        Args:
            registrar: 'namecheap' or 'godaddy'
        """
        self.registrar = registrar
        self.mode = getattr(settings, 'DOMAIN_REGISTRAR_MODE', 'mock')  # mock or live

        if self.mode == 'live':
            if registrar == 'namecheap':
                self.api_user = getattr(settings, 'NAMECHEAP_API_USER', '')
                self.api_key = getattr(settings, 'NAMECHEAP_API_KEY', '')
                self.username = getattr(settings, 'NAMECHEAP_USERNAME', '')
                self.api_endpoint = 'https://api.namecheap.com/xml.response'
                self.sandbox_mode = getattr(settings, 'NAMECHEAP_SANDBOX', True)
                if self.sandbox_mode:
                    self.api_endpoint = 'https://api.sandbox.namecheap.com/xml.response'

            elif registrar == 'godaddy':
                self.api_key = getattr(settings, 'GODADDY_API_KEY', '')
                self.api_secret = getattr(settings, 'GODADDY_API_SECRET', '')
                self.api_endpoint = 'https://api.godaddy.com/v1'
                self.sandbox_mode = getattr(settings, 'GODADDY_SANDBOX', True)
                if self.sandbox_mode:
                    self.api_endpoint = 'https://api.ote-godaddy.com/v1'

    def search_domain(self, domain_name: str) -> Dict[str, Any]:
        """
        Search for domain availability and pricing

        Args:
            domain_name: Domain to search (e.g., "mystore.com")

        Returns:
            dict: {
                'available': bool,
                'domain': str,
                'price_usd': Decimal,
                'renewal_price_usd': Decimal,
                'premium': bool,
                'suggestions': list
            }
        """
        if self.mode == 'mock':
            return self._mock_search_domain(domain_name)

        try:
            if self.registrar == 'namecheap':
                return self._namecheap_search(domain_name)
            elif self.registrar == 'godaddy':
                return self._godaddy_search(domain_name)
            else:
                raise ValueError(f"Unsupported registrar: {self.registrar}")

        except Exception as e:
            logger.error(f"Domain search failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def check_availability(self, domain_name: str) -> Dict[str, Any]:
        """
        Quick availability check for a single domain

        Args:
            domain_name: Domain to check

        Returns:
            dict: {available: bool, domain: str, price_usd: Decimal}
        """
        if self.mode == 'mock':
            return self._mock_check_availability(domain_name)

        try:
            if self.registrar == 'namecheap':
                return self._namecheap_check_availability(domain_name)
            elif self.registrar == 'godaddy':
                return self._godaddy_check_availability(domain_name)

        except Exception as e:
            logger.error(f"Availability check failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def purchase_domain(self, domain_name: str, registration_years: int = 1,
                       contact_info: Dict = None) -> Dict[str, Any]:
        """
        Purchase a domain from registrar

        IMPORTANT: Only call AFTER receiving payment confirmation from mobile money webhook

        Args:
            domain_name: Domain to purchase
            registration_years: Registration period (default 1 year)
            contact_info: Registrant contact information

        Returns:
            dict: {
                'success': bool,
                'domain_id': str,
                'order_id': str,
                'expires_at': datetime,
                'registrar_response': dict
            }
        """
        if self.mode == 'mock':
            return self._mock_purchase_domain(domain_name, registration_years)

        try:
            if self.registrar == 'namecheap':
                return self._namecheap_purchase(domain_name, registration_years, contact_info)
            elif self.registrar == 'godaddy':
                return self._godaddy_purchase(domain_name, registration_years, contact_info)

        except Exception as e:
            logger.error(f"Domain purchase failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def renew_domain(self, domain_name: str, renewal_years: int = 1) -> Dict[str, Any]:
        """
        Renew an existing domain

        IMPORTANT: Only call AFTER receiving renewal payment confirmation

        Args:
            domain_name: Domain to renew
            renewal_years: Renewal period (default 1 year)

        Returns:
            dict: {
                'success': bool,
                'renewal_id': str,
                'new_expiry_date': datetime
            }
        """
        if self.mode == 'mock':
            return self._mock_renew_domain(domain_name, renewal_years)

        try:
            if self.registrar == 'namecheap':
                return self._namecheap_renew(domain_name, renewal_years)
            elif self.registrar == 'godaddy':
                return self._godaddy_renew(domain_name, renewal_years)

        except Exception as e:
            logger.error(f"Domain renewal failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def configure_dns(self, domain_name: str, dns_records: List[Dict]) -> Dict[str, Any]:
        """
        Auto-configure DNS records for domain

        Args:
            domain_name: Domain to configure
            dns_records: List of DNS records to create

        Returns:
            dict: Configuration result
        """
        if self.mode == 'mock':
            return self._mock_configure_dns(domain_name, dns_records)

        try:
            if self.registrar == 'namecheap':
                return self._namecheap_configure_dns(domain_name, dns_records)
            elif self.registrar == 'godaddy':
                return self._godaddy_configure_dns(domain_name, dns_records)

        except Exception as e:
            logger.error(f"DNS configuration failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== MOCK METHODS (Development) ====================

    def _mock_search_domain(self, domain_name: str) -> Dict[str, Any]:
        """Mock domain search for development"""
        import random

        # Simulate some domains as taken
        taken_domains = ['google', 'facebook', 'amazon', 'apple', 'microsoft']
        domain_base = domain_name.split('.')[0]

        is_available = domain_base.lower() not in taken_domains

        result = {
            'success': True,
            'available': is_available,
            'domain': domain_name,
            'price_usd': Decimal('12.00'),
            'renewal_price_usd': Decimal('12.00'),
            'premium': False,
            'registrar': 'namecheap_mock'
        }

        # Generate suggestions if not available
        if not is_available:
            result['suggestions'] = [
                {'domain': f"{domain_base}shop.com", 'price_usd': Decimal('12.00'), 'available': True},
                {'domain': f"my{domain_base}.com", 'price_usd': Decimal('12.00'), 'available': True},
                {'domain': f"{domain_base}.shop", 'price_usd': Decimal('14.00'), 'available': True},
                {'domain': f"{domain_base}.store", 'price_usd': Decimal('14.00'), 'available': True},
                {'domain': f"{domain_base}.online", 'price_usd': Decimal('10.00'), 'available': True},
            ]
        else:
            result['suggestions'] = []

        logger.info(f"[MOCK] Domain search: {domain_name} - Available: {is_available}")
        return result

    def _mock_check_availability(self, domain_name: str) -> Dict[str, Any]:
        """Mock availability check"""
        search_result = self._mock_search_domain(domain_name)
        return {
            'success': True,
            'available': search_result['available'],
            'domain': domain_name,
            'price_usd': search_result['price_usd']
        }

    def _mock_purchase_domain(self, domain_name: str, years: int) -> Dict[str, Any]:
        """Mock domain purchase"""
        import uuid

        mock_order_id = f"mock-order-{uuid.uuid4().hex[:12]}"
        mock_domain_id = f"mock-domain-{uuid.uuid4().hex[:12]}"
        expires_at = timezone.now() + timedelta(days=365 * years)

        logger.info(f"[MOCK] Domain purchased: {domain_name} for {years} year(s)")
        logger.info(f"[MOCK] Order ID: {mock_order_id}, Expires: {expires_at}")

        return {
            'success': True,
            'domain_id': mock_domain_id,
            'order_id': mock_order_id,
            'domain_name': domain_name,
            'expires_at': expires_at,
            'registrar': 'namecheap_mock',
            'registrar_response': {
                'mode': 'mock',
                'order_id': mock_order_id,
                'domain_id': mock_domain_id,
                'registered_at': timezone.now().isoformat(),
                'expires_at': expires_at.isoformat()
            }
        }

    def _mock_renew_domain(self, domain_name: str, years: int) -> Dict[str, Any]:
        """Mock domain renewal"""
        import uuid

        mock_renewal_id = f"mock-renewal-{uuid.uuid4().hex[:12]}"
        new_expiry = timezone.now() + timedelta(days=365 * years)

        logger.info(f"[MOCK] Domain renewed: {domain_name} for {years} year(s)")
        logger.info(f"[MOCK] Renewal ID: {mock_renewal_id}, New expiry: {new_expiry}")

        return {
            'success': True,
            'renewal_id': mock_renewal_id,
            'domain_name': domain_name,
            'new_expiry_date': new_expiry,
            'registrar_response': {
                'mode': 'mock',
                'renewal_id': mock_renewal_id,
                'renewed_at': timezone.now().isoformat(),
                'new_expiry': new_expiry.isoformat()
            }
        }

    def _mock_configure_dns(self, domain_name: str, dns_records: List[Dict]) -> Dict[str, Any]:
        """Mock DNS configuration"""
        logger.info(f"[MOCK] DNS configured for {domain_name}")
        logger.info(f"[MOCK] Records: {dns_records}")

        return {
            'success': True,
            'domain_name': domain_name,
            'records_configured': len(dns_records),
            'dns_records': dns_records
        }

    # ==================== NAMECHEAP API METHODS ====================

    def _namecheap_search(self, domain_name: str) -> Dict[str, Any]:
        """
        Search domain using Namecheap API
        Docs: https://www.namecheap.com/support/api/methods/domains/check/
        """
        # TODO: Implement Namecheap API integration
        # API endpoint: domains.check
        # Returns: availability + pricing
        pass

    def _namecheap_check_availability(self, domain_name: str) -> Dict[str, Any]:
        """Namecheap availability check"""
        # TODO: Implement Namecheap domains.check API call
        pass

    def _namecheap_purchase(self, domain_name: str, years: int, contact_info: Dict) -> Dict[str, Any]:
        """
        Purchase domain via Namecheap API
        Docs: https://www.namecheap.com/support/api/methods/domains/create/
        """
        # TODO: Implement Namecheap domains.create API call
        # Requires: domain, years, contact info (registrant, admin, tech, billing)
        pass

    def _namecheap_renew(self, domain_name: str, years: int) -> Dict[str, Any]:
        """
        Renew domain via Namecheap API
        Docs: https://www.namecheap.com/support/api/methods/domains/renew/
        """
        # TODO: Implement Namecheap domains.renew API call
        pass

    def _namecheap_configure_dns(self, domain_name: str, dns_records: List[Dict]) -> Dict[str, Any]:
        """
        Configure DNS via Namecheap API
        Docs: https://www.namecheap.com/support/api/methods/domains-dns/set-hosts/
        """
        # TODO: Implement Namecheap DNS configuration
        # API endpoint: domains.dns.setHosts
        pass

    # ==================== GODADDY API METHODS ====================

    def _godaddy_search(self, domain_name: str) -> Dict[str, Any]:
        """
        Search domain using GoDaddy API
        Docs: https://developer.godaddy.com/doc/endpoint/domains
        """
        try:
            headers = {
                'Authorization': f'sso-key {self.api_key}:{self.api_secret}'
            }

            # First check availability of the exact domain
            availability_result = self._godaddy_check_availability(domain_name)

            if not availability_result.get('success'):
                return availability_result

            # Get suggestions using the suggest endpoint
            suggest_url = f'{self.api_endpoint}/domains/suggest'
            params = {
                'query': domain_name,
                'limit': 10,
                'waitMs': 2000
            }

            suggest_response = requests.get(suggest_url, params=params, headers=headers, timeout=10)
            suggest_response.raise_for_status()
            suggestions_data = suggest_response.json()

            # Parse suggestions
            suggestions = []
            for suggestion in suggestions_data:
                price_micro = suggestion.get('price', 0)
                price_usd = Decimal(str(price_micro / 1_000_000))  # Convert from micro-units

                suggestions.append({
                    'domain': suggestion.get('domain'),
                    'price_usd': price_usd,
                    'available': True  # Suggestions are typically available
                })

            return {
                'success': True,
                'available': availability_result.get('available', False),
                'domain': domain_name,
                'price_usd': availability_result.get('price_usd', Decimal('12.00')),
                'renewal_price_usd': availability_result.get('price_usd', Decimal('12.00')),
                'premium': False,
                'registrar': 'godaddy',
                'suggestions': suggestions
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"GoDaddy search API error for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'GoDaddy API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"GoDaddy search failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _godaddy_check_availability(self, domain_name: str) -> Dict[str, Any]:
        """
        GoDaddy availability check
        Endpoint: GET /v1/domains/available
        """
        try:
            headers = {
                'Authorization': f'sso-key {self.api_key}:{self.api_secret}'
            }

            url = f'{self.api_endpoint}/domains/available'
            params = {'domain': domain_name}

            response = requests.get(url, params=params, headers=headers, timeout=10)

            # Try to get error details before raising
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_data.get('error', response.text))
                    logger.error(f"GoDaddy API error for {domain_name}: {error_msg} (Status: {response.status_code})")
                    return {
                        'success': False,
                        'error': f'GoDaddy API error: {error_msg}'
                    }
                except:
                    pass

            response.raise_for_status()
            result = response.json()

            # Extract availability and pricing
            available = result.get('available', False)
            price_micro = result.get('price', 12_000_000)  # Default to $12 if not provided
            price_usd = Decimal(str(price_micro / 1_000_000))  # Convert from micro-units

            return {
                'success': True,
                'available': available,
                'domain': domain_name,
                'price_usd': price_usd
            }

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_data.get('error', str(e)))
                except:
                    error_msg = e.response.text or str(e)

            logger.error(f"GoDaddy availability check error for {domain_name}: {error_msg}", exc_info=True)
            return {
                'success': False,
                'error': f'GoDaddy API error: {error_msg}'
            }
        except Exception as e:
            logger.error(f"GoDaddy availability check failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _godaddy_purchase(self, domain_name: str, years: int, contact_info: Dict) -> Dict[str, Any]:
        """
        Purchase domain via GoDaddy API
        Endpoint: POST /v1/domains/purchase
        Docs: https://developer.godaddy.com/doc/endpoint/domains#/v1/purchase
        """
        try:
            headers = {
                'Authorization': f'sso-key {self.api_key}:{self.api_secret}',
                'Content-Type': 'application/json'
            }

            # Build contact object (same for all 4 contacts as per GoDaddy schema)
            contact_obj = {
                'nameFirst': contact_info.get('first_name', ''),
                'nameLast': contact_info.get('last_name', ''),
                'email': contact_info.get('email', ''),
                'phone': contact_info.get('phone', ''),
                'addressMailing': {
                    'address1': contact_info.get('address', ''),
                    'city': contact_info.get('city', ''),
                    'state': contact_info.get('state', ''),
                    'postalCode': contact_info.get('zip', ''),
                    'country': contact_info.get('country', 'US')
                }
            }

            # Build purchase request body
            purchase_data = {
                'domain': domain_name,
                'period': years,
                'privacy': False,  # Can be configured
                'nameServers': [],  # Use GoDaddy default nameservers
                'consent': {
                    'agreementKeys': ['DNRA'],  # Domain Name Registration Agreement
                    'agreedBy': contact_info.get('email', ''),
                    'agreedAt': timezone.now().isoformat()
                },
                'contactAdmin': contact_obj,
                'contactBilling': contact_obj,
                'contactRegistrant': contact_obj,
                'contactTech': contact_obj
            }

            url = f'{self.api_endpoint}/domains/purchase'
            response = requests.post(url, json=purchase_data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Parse response
            order_id = result.get('orderId', '')
            domain_id = result.get('domainId', order_id)

            # Calculate expiry date
            expires_at = timezone.now() + timedelta(days=365 * years)

            logger.info(f"GoDaddy domain purchased: {domain_name}, Order: {order_id}")

            return {
                'success': True,
                'domain_id': domain_id,
                'order_id': order_id,
                'domain_name': domain_name,
                'expires_at': expires_at,
                'registrar': 'godaddy',
                'registrar_response': result
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"GoDaddy purchase API error for {domain_name}: {str(e)}", exc_info=True)
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', str(e))
                except:
                    error_msg = e.response.text or str(e)

            return {
                'success': False,
                'error': f'GoDaddy purchase failed: {error_msg}'
            }
        except Exception as e:
            logger.error(f"GoDaddy purchase failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _godaddy_renew(self, domain_name: str, years: int) -> Dict[str, Any]:
        """
        Renew domain via GoDaddy API
        Endpoint: POST /v1/domains/{domain}/renew
        Docs: https://developer.godaddy.com/doc/endpoint/domains#/v1/renew
        """
        try:
            headers = {
                'Authorization': f'sso-key {self.api_key}:{self.api_secret}',
                'Content-Type': 'application/json'
            }

            url = f'{self.api_endpoint}/domains/{domain_name}/renew'
            renew_data = {'period': years}

            response = requests.post(url, json=renew_data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Calculate new expiry
            new_expiry = timezone.now() + timedelta(days=365 * years)
            renewal_id = result.get('orderId', f'renewal-{domain_name}')

            logger.info(f"GoDaddy domain renewed: {domain_name}, Renewal ID: {renewal_id}")

            return {
                'success': True,
                'renewal_id': renewal_id,
                'domain_name': domain_name,
                'new_expiry_date': new_expiry,
                'registrar_response': result
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"GoDaddy renewal API error for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'GoDaddy renewal failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"GoDaddy renewal failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _godaddy_configure_dns(self, domain_name: str, dns_records: List[Dict]) -> Dict[str, Any]:
        """
        Configure DNS via GoDaddy API
        Endpoint: PUT /v1/domains/{domain}/records
        Docs: https://developer.godaddy.com/doc/endpoint/domains#/v1/recordReplaceTypeName
        """
        try:
            headers = {
                'Authorization': f'sso-key {self.api_key}:{self.api_secret}',
                'Content-Type': 'application/json'
            }

            # Transform our DNS records format to GoDaddy format
            godaddy_records = []
            for record in dns_records:
                godaddy_records.append({
                    'type': record.get('type'),  # A, CNAME, TXT, etc.
                    'name': record.get('name', '@'),
                    'data': record.get('value'),
                    'ttl': record.get('ttl', 3600)
                })

            url = f'{self.api_endpoint}/domains/{domain_name}/records'
            response = requests.put(url, json=godaddy_records, headers=headers, timeout=30)
            response.raise_for_status()

            logger.info(f"GoDaddy DNS configured for {domain_name}: {len(godaddy_records)} records")

            return {
                'success': True,
                'domain_name': domain_name,
                'records_configured': len(godaddy_records),
                'dns_records': godaddy_records
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"GoDaddy DNS API error for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'GoDaddy DNS configuration failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"GoDaddy DNS configuration failed for {domain_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
