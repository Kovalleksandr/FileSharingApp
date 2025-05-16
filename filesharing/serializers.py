from rest_framework import serializers
from .models import Collection, Photo
from accounts.models import User

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'file', 'collection', 'uploaded_by', 'uploaded_at', 'is_selected']
        read_only_fields = ['uploaded_at', 'is_selected']  # uploaded_by НЕ read_only

    def validate_collection(self, value):
        # Перевірка, чи колекція існує
        if not Collection.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Collection does not exist")
        return value

    def validate_uploaded_by(self, value):
        # Перевірка, чи користувач існує
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("User does not exist")
        return value

class CollectionSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True, read_only=True)
    subcollections = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'name', 'owner', 'created_at', 'project', 'parent', 'photos', 'subcollections']