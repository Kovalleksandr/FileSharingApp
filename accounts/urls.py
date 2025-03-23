from django.urls import path
from .views import AcceptInvitationView, UserListView, InviteUserView, ValidateInviteView

urlpatterns = [
    path('accept-invitation/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('invite/', InviteUserView.as_view(), name='invite-user'),
    path('validate-invite/<uuid:uuid>/', ValidateInviteView.as_view(), name='validate-invite'),
]