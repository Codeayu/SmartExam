import time
import logging
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db import connections
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

class DBConnectionManagerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Initialize active user tracking
        self.active_users = {}
        # Connection limit
        self.max_connections = 5  # Keeping at 5 for free database
        # Idle timeout in seconds (increased to 10 minutes)
        self.idle_timeout = 600
        # Track paths that should bypass intensive connection management
        self.priority_paths = ['/login/', '/register/', '/admin/login/']
        # Cache last check time to avoid frequent connection checks
        self.last_connection_check = time.time()
        # Only check connections every 5 seconds
        self.connection_check_interval = 5
    
    def __call__(self, request):
        # Determine if this is a priority path (login/register)
        is_priority_path = any(request.path.startswith(path) for path in self.priority_paths)
        
        # For login and register paths, completely bypass middleware processing
        if is_priority_path:
            # Ensure we have at least one connection available for auth
            self.ensure_auth_connection()
            response = self.get_response(request)
            return response
            
        # Only do full connection management for non-priority paths
        # and only check connections periodically to reduce overhead
        current_time = time.time()
        if current_time - self.last_connection_check > self.connection_check_interval:
            self.manage_connections(request)
            self.last_connection_check = current_time
        
        # Update last activity timestamp for the user
        # But don't save to session on every request to reduce writes
        if request.user.is_authenticated:
            self.active_users[request.user.id] = time.time()
            
            # Only update session activity every 10 minutes instead of every request
            last_update = request.session.get('last_activity_update', 0)
            if current_time - last_update > 600:  # 10 minutes
                request.session['last_activity'] = current_time
                request.session['last_activity_update'] = current_time
                request.session.modified = True
        
        response = self.get_response(request)
        
        # After the view
        # Only do cleanup for non-priority paths to avoid slowing down logins
        # and only run cleanup operations every 30 seconds
        if not is_priority_path and current_time - self.last_connection_check > 30:
            self.cleanup_idle_connections()
        
        return response
    
    def ensure_auth_connection(self):
        """Make sure we have at least one connection available for authentication"""
        connection_count = len(connections.all())
        
        if connection_count >= self.max_connections:
            # If we're at limit, close one connection to ensure auth works
            for conn in connections.all():
                try:
                    conn.close()
                    break  # Only need to close one
                except:
                    continue
    
    def manage_connections(self, request):
        """Monitor connection count and handle when approaching limits"""
        # Get current connection count (this is approximate)
        connection_count = len(connections.all())
        
        if connection_count >= self.max_connections - 1:  # Near limit
            # Force close idle connections
            self.force_close_idle_sessions()
            
            # If still at limit after cleanup, show warning or redirect
            if len(connections.all()) >= self.max_connections:
                if request.user.is_authenticated:
                    messages.warning(
                        request, 
                        "The system is currently experiencing high traffic. "
                        "Please try again in a few moments."
                    )
                return redirect(reverse('connection_limit'))
    
    def cleanup_idle_connections(self):
        """Close connections for users who have been idle too long"""
        current_time = time.time()
        idle_users = []
        
        # Find idle users
        for user_id, last_active in self.active_users.items():
            if current_time - last_active > self.idle_timeout:
                idle_users.append(user_id)
        
        # Remove idle users from tracking
        for user_id in idle_users:
            self.active_users.pop(user_id, None)
    
    def force_close_idle_sessions(self):
        """Force close sessions for inactive users - only when critically needed"""
        # Find sessions that haven't been active recently
        timeout_time = timezone.now() - timezone.timedelta(seconds=self.idle_timeout)
        
        # Batch process to reduce query load (limit to oldest 5)
        expired_sessions = Session.objects.filter(
            expire_date__gt=timezone.now(),  # Not yet expired by Django
            last_activity__lt=timeout_time   # But inactive based on our criteria
        ).order_by('last_activity')[:5]  # Only process oldest 5 sessions
        
        # Delete these sessions
        count = 0
        for session in expired_sessions:
            try:
                session.delete()  # Delete one by one to avoid large transactions
                count += 1
            except Exception as e:
                logger.error(f"Error deleting session: {str(e)}")
        
        if count > 0:
            logger.info(f"Closed {count} idle sessions to free up database connections")
            
        # Explicitly close connections from the pool
        for conn in connections.all():
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Session timeout in seconds (30 minutes default - increased)
        self.timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 1800)
        # Track paths that should bypass processing
        self.bypass_paths = ['/login/', '/register/', '/admin/login/']
    
    def __call__(self, request):
        # Skip intensive processing for login and registration
        if any(request.path.startswith(path) for path in self.bypass_paths):
            return self.get_response(request)
            
        if request.user.is_authenticated:
            current_time = time.time()
            last_activity = request.session.get('last_activity', 0)
            
            # If session is expired
            if (current_time - last_activity) > self.timeout:
                # Close this connection to free up the pool
                for conn in connections.all():
                    try:
                        conn.close()
                    except:
                        pass
                    
                # Clear session and logout
                request.session.flush()
                messages.info(request, "Your session has expired due to inactivity.")
                return redirect(settings.LOGIN_URL)
        
        response = self.get_response(request)
        return response