"""
User Session Management Service
"""
from authentication.models import UserSession
from .auth_service import AuthenticationService


class SessionService:
    """User session management service"""
    
    @staticmethod
    def create_session(request, user=None):
        """Create or get user session"""
        if not request:
            return None
        
        # Get session key
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Check if session exists
        session = UserSession.objects.filter(session_key=session_key).first()
        
        if not session:
            # Extract device info
            device_info = AuthenticationService._extract_device_info(request)
            ip_address = AuthenticationService._get_client_ip(request)
            
            # Create new session
            session = UserSession.objects.create(
                user=user,
                session_key=session_key,
                device_type=device_info.get('device_type', 'unknown'),
                browser=device_info.get('browser', ''),
                os=device_info.get('os', ''),
                ip_address=ip_address,
                is_authenticated=bool(user),
                authentication_method='password' if user else 'guest'
            )
        
        return session
    
    @staticmethod
    def update_session_activity(request, action_type='page_view'):
        """Update session activity"""
        if not request or not hasattr(request, 'session'):
            return
        
        session = SessionService.create_session(request)
        if session:
            session.update_activity(action_type)
    
    @staticmethod
    def should_prompt_authentication(request):
        """Determine if user should be prompted to authenticate"""
        if not request or not hasattr(request, 'session'):
            return False
        
        session = SessionService.create_session(request)
        return session.should_show_auth_prompt() if session else False
    
    @staticmethod
    def mark_auth_prompt_shown(request):
        """Mark that authentication prompt was shown"""
        if not request or not hasattr(request, 'session'):
            return
        
        session = SessionService.create_session(request)
        if session:
            session.mark_auth_prompt_shown()
    
    @staticmethod
    def convert_session_to_authenticated(request, user, trigger=None):
        """Convert guest session to authenticated session"""
        if not request or not hasattr(request, 'session'):
            return
        
        session = SessionService.create_session(request, user)
        if session:
            session.user = user
            session.mark_converted(trigger)
            
            # Update user conversion status
            if not user.is_guest_converted:
                user.is_guest_converted = True
                user.save(update_fields=['is_guest_converted'])