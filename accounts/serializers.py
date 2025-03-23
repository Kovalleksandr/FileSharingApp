from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Invitation, User

User = get_user_model()

class AcceptInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    uuid = serializers.UUIDField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            invitation = Invitation.objects.get(email=data['email'], uuid=data['uuid'])
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation.")

        data['invitation'] = invitation
        return data

    def create(self, validated_data):
        invitation = validated_data['invitation']
        user = User.objects.create_user(
            username=invitation.email,
            email=invitation.email,
            password=validated_data['password'],
            role=invitation.role,
        )
        invitation.delete()  # Видаляємо використане запрошення
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']

class InviteSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = Invitation
        fields = ['email', 'role']

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("This email is already registered.")
        return data