#accounts\urls.py
from django.urls import path
from . import views  # Імпортуємо views із поточного додатку accounts

urlpatterns = [
    path('register/', views.RegisterOwnerView.as_view(), name='register-owner'),
    path('accept-invitation/', views.AcceptInvitationView.as_view(), name='accept-invitation'),
    path('invitations/', views.InviteUserView.as_view(), name='invite-user'),
    path('invitations/<uuid:uuid>/', views.ValidateInviteView.as_view(), name='validate-invite'),
    path('users/', views.UserListView.as_view(), name='user-list'),
]
