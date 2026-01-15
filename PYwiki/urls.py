"""
URL configuration for PYwiki project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import login_view, logout_view, get_user_list, delete_users, admin_panel, create_user
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login')),
    path('', include('base.urls')),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("get-user-list/", get_user_list, name="get_user_list"),
    path("delete_users/", delete_users, name="delete_users"),
    path("admin-panel/", admin_panel, name="admin_panel"),
    path("create-user/", create_user, name="create_user")
]