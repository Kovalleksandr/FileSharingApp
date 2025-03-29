from rest_framework import serializers
from .models import Collection, Photo

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'file', 'uploaded_by', 'collection', 'uploaded_at', 'is_selected']

class CollectionSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'name', 'owner', 'created_at', 'photos']