from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views as core_views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Include core app URLs - this should handle all core app routes
    path('', include('core.urls')),
    
    # Authentication URLs - using Django's default accounts/ path
   path('accounts/login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
   path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
  
    

    
]