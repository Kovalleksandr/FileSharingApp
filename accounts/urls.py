from django.urls import path
from .views import AcceptInvitationView

urlpatterns = [
    path('accept-invitation/', AcceptInvitationView.as_view(), name='accept-invitation'),
]
