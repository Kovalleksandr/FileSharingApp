#filesharing\serializers.py
from rest_framework import serializers
from .models import Collection, Photo, Folder
from accounts.models import User
from crm.models import Project
import logging

logger = logging.getLogger('filesharing')

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'file', 'is_selected']

class FolderSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True, read_only=True, source='photo_set')

    class Meta:
        model = Folder
        fields = ['id', 'name', 'photos']

class CollectionSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), allow_null=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all(), allow_null=True)
    folders = FolderSerializer(many=True, read_only=True, source='folder_set')

    class Meta:
        model = Collection
        fields = ['id', 'name', 'owner', 'created_at', 'project', 'parent', 'is_client_selection', 'folders']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user:
            if data.get('project') and data['project'].company != request.user.company:
                logger.error(f"User {request.user.email} attempted to access project {data.get('project').id} from another company")
                raise serializers.ValidationError("You do not have access to this project.")
        return data

class FullFolderSerializer(serializers.ModelSerializer):
    collection = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all())
    parent = serializers.PrimaryKeyRelatedField(queryset=Folder.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Folder
        fields = ['id', 'name', 'collection', 'parent', 'created_at']

    def to_internal_value(self, data):
        logger.debug(f"Data to_internal_value: {data}")
        data = data.copy()
        if not 'parent' in data:
            data['parent'] = None
            logger.debug("Set parent to None")
        validated_data = super().to_internal_value(data)
        logger.debug(f"FolderSerializer to_internal_value output: {validated_data}")
        return validated_data

    def validate(self, data):
        logger.debug(f"FolderSerializer validate input: {data}")
        request = self.context.get('request')
        if request and request.user:
            collection = data.get('collection')
            if collection.project and collection.project.company != request.user.company:
                logger.error(f"User {request.user.email} attempted to access collection {collection.id} from another company")
                raise serializers.ValidationError("You do not have access to this collection.")
        return data

class FullPhotoSerializer(serializers.ModelSerializer):
    collection = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all())
    folder = serializers.PrimaryKeyRelatedField(queryset=Folder.objects.all(), allow_null=True)
    uploaded_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Photo
        fields = ['id', 'file', 'collection', 'folder', 'uploaded_by', 'uploaded_at', 'is_selected']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user:
            collection = data.get('collection')
            if collection.project and collection.project.company != request.user.company:
                logger.error(f"User {request.user.email} attempted to access collection {collection.id} from another company")
                raise serializers.ValidationError("You do not have access to this collection.")
            folder = data.get('folder')
            if folder and folder.collection != collection:
                logger.error(f"Folder {folder.id} does not belong to collection {collection.id}")
                raise serializers.ValidationError("Folder does not belong to this collection.")
        return data