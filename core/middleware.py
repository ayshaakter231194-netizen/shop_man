# core/middleware.py
from django.http import HttpResponseForbidden
from django.urls import reverse

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if the request is for admin URLs
        if request.path.startswith('/admin/'):
            # Allow superusers
            if request.user.is_superuser:
                return None
                
            # Check if user has admin access through profile
            if hasattr(request.user, 'userprofile'):
                if request.user.userprofile.can_access_admin:
                    return None
            
            # Redirect or deny access for non-admin users
            return HttpResponseForbidden("""
                <h1>Access Denied</h1>
                <p>You don't have permission to access the Django admin interface.</p>
                <p>Please contact your system administrator if you need access.</p>
                <a href="/">Return to Dashboard</a>
            """)
        
        return None