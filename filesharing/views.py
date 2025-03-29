from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Collection, Photo
from .serializers import CollectionSerializer, PhotoSerializer

class ClientCollectionView(APIView):
    def get(self, request, collection_id):
        try:
            collection = Collection.objects.get(id=collection_id)
            serializer = CollectionSerializer(collection)
            return Response(serializer.data)
        except Collection.DoesNotExist:
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, collection_id):
        """Позначення фото клієнтом"""
        try:
            photo = Photo.objects.get(id=request.data.get('photo_id'), collection_id=collection_id)
            photo.is_selected = True
            photo.save()
            return Response({"message": "Photo selected"})
        except Photo.DoesNotExist:
            return Response({"error": "Photo not found"}, status=status.HTTP_404_NOT_FOUND)