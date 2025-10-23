# core/decorators.py
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from functools import wraps

def view_permission_required(view_code):
    """
    Decorator to check if user has permission to access a specific view
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Superusers and system admins have access to everything
            if request.user.is_superuser or hasattr(request.user, 'userprofile') and request.user.userprofile.can_access_admin:
                return view_func(request, *args, **kwargs)
            
            # Check if user has the specific view permission
            if hasattr(request.user, 'userprofile'):
                if request.user.userprofile.has_view_permission(view_code):
                    return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("You don't have permission to access this page.")
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """
    Decorator to ensure only admin users can access the view
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if (request.user.is_superuser or 
            (hasattr(request.user, 'userprofile') and request.user.userprofile.can_access_admin)):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Admin access required.")
    return _wrapped_view