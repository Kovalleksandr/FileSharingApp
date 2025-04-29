from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Invitation, User
from django.contrib.auth.password_validation import validate_password
import logging

logger = logging.getLogger('accounts')

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role', 'company']
        extra_kwargs = {
            'company': {'read_only': True},
            'role': {'read_only': True}
        }

    def validate_password(self, value):
        validate_password(value)  # Викликає валідацію з AUTH_PASSWORD_VALIDATORS
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role='owner'  # Примусово встановлюємо role='owner' для цього ендпоінта
        )
        return user

class AcceptInvitationSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)  # Викликає валідацію з AUTH_PASSWORD_VALIDATORS
        return value

    def validate(self, data):
        logger.debug(f"Validating AcceptInvitationSerializer data: {data}")
        try:
            invitation = Invitation.objects.get(email=data['email'], uuid=data['uuid'])
            logger.debug(f"Found invitation: UUID={invitation.uuid}, Email={invitation.email}, Role={invitation.role}")
        except Invitation.DoesNotExist:
            logger.error(f"Invalid invitation: UUID={data['uuid']}, Email={data['email']}")
            raise serializers.ValidationError("Invalid invitation.")
        data['invitation'] = invitation
        return data

    def create(self, validated_data):
        logger.debug(f"Creating user with validated data: {validated_data}")
        invitation = validated_data['invitation']
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=invitation.role,
            company=invitation.owner.company
        )
        logger.debug(f"User created: ID={user.id}, Username={user.username}, Email={user.email}, Role={user.role}, Company={user.company_id}")
        invitation.delete()
        logger.debug(f"Invitation deleted: UUID={invitation.uuid}")
        return user

class InviteSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = Invitation
        fields = ['email', 'role']

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("This email is already registered.")
        # Видаляємо старе запрошення, якщо воно існує
        Invitation.objects.filter(email=data['email']).delete()
        return data