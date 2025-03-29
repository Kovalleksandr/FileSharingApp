from rest_framework import serializers
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'owner', 'created_at', 'client_link']
        read_only_fields = ['owner', 'created_at', 'client_link']  # owner заповнюється автоматично
