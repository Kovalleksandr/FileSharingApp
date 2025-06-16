#filesharing\serializers.py
from rest_framework import serializers
from .models import Collection, Photo, Folder
from accounts.models import User
from crm.models import Project
import logging

logger = logging.getLogger('filesharing')

class CollectionSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), allow_null=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all(), allow_null=True)

    class Meta:
        model = Collection
        fields = ['id', 'name', 'owner', 'created_at', 'project', 'parent', 'is_client_selection']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user:
            if data.get('project') and data['project'].company != request.user.company:
                logger.error(f"User {request.user.email} attempted to access project {data['project'].id} from another company")
                raise serializers.ValidationError("You do not have access to this project.")
        return data

class FolderSerializer(serializers.ModelSerializer):
    collection = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all())
    parent = serializers.PrimaryKeyRelatedField(queryset=Folder.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Folder
        fields = ['id', 'name', 'collection', 'parent', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user:
            collection = data.get('collection')
            if collection.project and collection.project.company != request.user.company:
                logger.error(f"User {request.user.email} attempted to access collection {collection.id} from another company")
                raise serializers.ValidationError("You do not have access to this collection.")
        if 'parent' not in data:
            data['parent'] = None
        return data

class PhotoSerializer(serializers.ModelSerializer):
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