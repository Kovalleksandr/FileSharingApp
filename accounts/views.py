import logging
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from .models import User, Invitation
from .serializers import UserSerializer, InviteSerializer, AcceptInvitationSerializer

logger = logging.getLogger('accounts')

class AcceptInvitationView(APIView):
    def post(self, request):
        logger.debug(f"Received registration request: {request.data}")
        serializer = AcceptInvitationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User registered successfully: {user.email} (ID: {user.id})")
            return Response({"message": "User registered successfully", "user_id": user.id}, status=status.HTTP_201_CREATED)
        logger.warning(f"Registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class InviteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.debug(f"Invite request from {request.user.email}: {request.data}")
        if request.user.role != 'owner':
            logger.warning(f"Permission denied for {request.user.email} (role: {request.user.role})")
            raise PermissionDenied("Only owners can send invitations.")
        
        serializer = InviteSerializer(data=request.data)
        if serializer.is_valid():
            invitation = serializer.save(owner=request.user)
            invite_link = f"http://localhost:8000/api/accounts/accept-invitation/?uuid={invitation.uuid}"
            
            # Відправка email у HTML
            subject = "Запрошення до FileSharingApp"
            from_email = "no-reply@filesharingapp.com"
            to_email = invitation.email
            text_content = f"Вітаємо!\n\nВи отримали запрошення до FileSharingApp.\nПерейдіть за посиланням: {invite_link}\n\nКоманда FileSharingApp"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Вітаємо!</h2>
                    <p>Ви отримали запрошення до FileSharingApp.</p>
                    <a href="{invite_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Зареєструватися</a>
                    <p>З повагою,<br>Команда FileSharingApp</p>
                </body>
            </html>
            """
            try:
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                logger.info(f"Invitation email sent to {invitation.email} by {request.user.email}")
            except Exception as e:
                logger.error(f"Failed to send email to {invitation.email}: {str(e)}")
                return Response({"error": "Failed to send invitation email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({"message": "Invitation sent successfully"}, status=status.HTTP_201_CREATED)
        logger.warning(f"Invite creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
class ValidateInviteView(APIView):
    def get(self, request, uuid):
        logger.debug(f"Validating invitation with UUID: {uuid}")
        try:
            invitation = Invitation.objects.get(uuid=uuid)
            logger.info(f"Valid invitation found for {invitation.email}")
            return Response({
                "email": invitation.email,
                "role": invitation.role
            }, status=status.HTTP_200_OK)
        except Invitation.DoesNotExist:
            logger.warning(f"Invalid invitation: UUID {uuid} not found")
            return Response({"error": "Invalid invitation"}, status=status.HTTP_404_NOT_FOUND)