from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from .models import User, Invitation
from .serializers import UserSerializer, InviteSerializer, AcceptInvitationSerializer

class AcceptInvitationView(APIView):
    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully", "user_id": user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class InviteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'owner':
            raise PermissionDenied("Only owners can send invitations.")
        
        serializer = InviteSerializer(data=request.data)
        if serializer.is_valid():
            invitation = serializer.save(owner=request.user)
            invite_link = f"http://localhost:8000/api/accounts/accept-invitation/?uuid={invitation.uuid}"
            return Response({"invite_link": invite_link}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ValidateInviteView(APIView):
    def get(self, request, uuid):
        try:
            invitation = Invitation.objects.get(uuid=uuid)
            return Response({
                "email": invitation.email,
                "role": invitation.role
            }, status=status.HTTP_200_OK)
        except Invitation.DoesNotExist:
            return Response({"error": "Invalid invitation"}, status=status.HTTP_404_NOT_FOUND)