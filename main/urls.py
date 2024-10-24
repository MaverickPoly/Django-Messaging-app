from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.home, name='home'),

    # profiles
    path('profile/<int:pk>/', views.profile, name='profile'),
    path('profile/<int:pk>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:pk>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:user_id>/subscribers/', views.subscribers_list_view, name='subscribers_list'),
    path('profile/<int:user_id>/subscriptions/', views.subscriptions_list_view, name='subscriptions_list'),
    path('profile/<int:user_id>/chat/', views.chat, name='chat'),
    path('profile/inbox/', views.inbox, name='inbox'),
    path('profile/inbox/delete/<int:message_id>/', views.delete_message, name='delete_message'),


    # post stuff
    path('add_post/', views.add_post, name='add_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('edit_post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),


    # fast utils
    path('unsubscribe/<int:pk>/', views.unsubscribe, name='unsubscribe'),
    path('subscribe/<int:pk>/', views.subscribe, name='subscribe'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('search/', views.search_posts, name='search_posts'),


    # auth
    path('login/', views.login_user, name='login'),
    path('signup/', views.signup_user, name='signup'),
    path('logout/', views.logout_user, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
