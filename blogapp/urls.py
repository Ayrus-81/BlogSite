from django.contrib.auth.views import LoginView
from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),

    path('index/', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('update_profile/', views.profile_update, name='update_profile'),
    path('logout/', views.home_view, name='logout'),


##------forgot password-----##

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='password_reset'),
    path('password-reset-done/', TemplateView.as_view(template_name="user/password_reset_done.html"), name='password_reset_done'),
    path('password-reset-complete/', TemplateView.as_view(template_name="user/password_reset_complete.html"), name='password_reset_complete'),
    path('password-reset-invalid/', TemplateView.as_view(template_name="user/password_reset_invalid.html"), name='password_reset_invalid'),

##-----Blog-----##

    path('blogs/', views.blog_post_list, name='blog_post_list'),
    path('blogs/create/', views.create_blog_post, name='create_blog_post'),
    path('blogs/<int:id>/edit/', views.edit_blog_post, name='edit_blog_post'),
    path('blogs/<int:id>/delete/', views.delete_blog_post, name='delete_blog_post'),
    path('blogs/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/', views.blog_post_detail, name='blog_post_detail'),
    path('my-blogs/', views.my_blog_post_list, name='my_blog_post_list'),



# Custom login and dashboard for admin
    path('login/', LoginView.as_view(), name='login'),  # Default user login
    path('custom/admin_login/', views.admin_login, name='admin_login'),  # Custom admin login
    path('custom/admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # User management
    path('users/', views.user_list, name='user_list'),
    path('users/block/<int:user_id>/', views.block_user, name='block_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # Post management
    path('posts/', views.post_list, name='post_list'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('posts/toggle_publish/<int:post_id>/', views.toggle_publish_post, name='toggle_publish_post'),
]
