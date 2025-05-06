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
        self.max_connections = 5
        # Idle timeout in seconds (5 minutes)
        self.idle_timeout = 300
    
    def __call__(self, request):
        # Before the view
        self.manage_connections(request)
        
        # Update last activity timestamp for the user
        if request.user.is_authenticated:
            self.active_users[request.user.id] = time.time()
            
            # Store the last activity time in the session as well
            request.session['last_activity'] = time.time()
            request.session.modified = True
        
        response = self.get_response(request)
        
        # After the view
        self.cleanup_idle_connections()
        
        return response
    
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
        """Force close sessions for inactive users"""
        # Find sessions that haven't been active recently
        timeout_time = timezone.now() - timezone.timedelta(seconds=self.idle_timeout)
        
        # Get expired sessions
        expired_sessions = Session.objects.filter(
            expire_date__gt=timezone.now(),  # Not yet expired by Django
            last_activity__lt=timeout_time   # But inactive based on our criteria
        )
        
        # Delete these sessions
        count = expired_sessions.count()
        expired_sessions.delete()
        
        if count > 0:
            logger.info(f"Closed {count} idle sessions to free up database connections")
            
        # Explicitly close connections from the pool
        for conn in connections.all():
            conn.close()


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Session timeout in seconds (15 minutes default)
        self.timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 900)
    
    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = time.time()
            last_activity = request.session.get('last_activity', 0)
            
            # If session is expired
            if (current_time - last_activity) > self.timeout:
                # Close this connection to free up the pool
                for conn in connections.all():
                    conn.close()
                    
                # Clear session and logout
                request.session.flush()
                messages.info(request, "Your session has expired due to inactivity.")
                return redirect(settings.LOGIN_URL)
            
            # Update the last activity time
            request.session['last_activity'] = current_time
            request.session.modified = True
            
        response = self.get_response(request)
        return response