#filesharing\views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Collection, Photo, Folder
from .serializers import CollectionSerializer, PhotoSerializer, FolderSerializer
from crm.models import Company, Project
import logging
import os
from .permissions import IsPhotographerOrRetoucher

# Налаштування логування
logger = logging.getLogger('filesharing')

class ClientCollectionView(APIView):
    """
    Ендпоінт для клієнтського доступу до колекції.
    Дозволяє отримати дані колекції (GET) або вибрати фото (POST).
    GET доступний для всіх, POST доступний для клієнтів.
    Повертає:
        - GET: 200 OK з даними колекції, 404 якщо колекція не знайдена.
        - POST: 200 OK з даними оновленого фото, 404 якщо фото не знайдено.
    """
    def get(self, request, collection_id):
        try:
            collection = Collection.objects.get(pk=collection_id)
            serializer = CollectionSerializer(collection, context={'request': request})
            logger.info(f"Client viewed collection {collection_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, collection_id):
        try:
            data = request.data
            photo_id = data.get('photo_id')
            if not photo_id:
                logger.error(f"Invalid photo_id: {photo_id}")
                return Response({"error": "Invalid photo_id"}, status=status.HTTP_400_BAD_REQUEST)

            photo = Photo.objects.get(id=photo_id, collection_id=collection_id)
            photo.is_selected = True
            photo.save()
            serializer = PhotoSerializer(photo)
            logger.info(f"Photo {photo_id} selected in collection {collection_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Photo.DoesNotExist:
            logger.error(f"Photo ID {photo_id} not found in collection {collection_id}")
            return Response({"error": "Photo not found"}, status=status.HTTP_404_NOT_FOUND)
        

        
class FolderCreateView(APIView):
    """
    Ендпоінт для створення папок у колекції.
    Доступний для авторизованих фотографів/ретушерів.
    Повертає:
        - 201 Created з даними папки.
        - 400 Bad Request при помилках валідації.
        - 403 Forbidden без прав доступу.
        - 404 Not Found якщо колекція не знайдена.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def post(self, request):
        logger.debug(f"Folder creation attempt by {request.user.email}")
        serializer = FolderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            folder = serializer.save()
            logger.info(f"Folder created: {folder.name} in collection {folder.collection_id} by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Folder creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PhotoUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def post(self, request, collection_id):
        logger.debug(f"Photo upload attempt by {request.user.email} for collection {collection_id}")
        try:
            collection = Collection.objects.get(pk=collection_id)
            if collection.project and collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)

            files = request.FILES.getlist('files')
            if not files:
                logger.error("No files provided in upload request")
                return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)

            folder_id = request.data.get('folder_id')
            uploaded_photos = []
            for file in files:
                data = {
                    'file': file,
                    'collection': collection.id,
                    'folder': folder_id,  # Змінено з 'folder_id' на 'folder'
                    'uploaded_by': request.user.id
                }
                serializer = PhotoSerializer(data=data, context={'request': request})
                if serializer.is_valid():
                    photo = serializer.save(uploaded_by=request.user)
                    uploaded_photos.append(serializer.data)
                    logger.info(f"Photo uploaded by {request.user.email} to collection {collection_id}: {photo.file.url}")
                else:
                    logger.error(f"Serializer errors for file {file.name}: {serializer.errors}")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(uploaded_photos, status=status.HTTP_201_CREATED)
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

class PhotoDeleteView(APIView):
    """
    Ендпоінт для видалення фотографій з колекції.
    Доступний для авторизованих фотографів/ретушерів.
    Повертає:
        - 200 OK при успішному видаленні.
        - 403 Forbidden без прав доступу.
        - 404 Not Found якщо фото не знайдено.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def delete(self, request, collection_id, photo_id):
        logger.debug(f"Photo deletion attempt by {request.user.email} for photo {photo_id} in collection {collection_id}")
        try:
            photo = Photo.objects.get(id=photo_id, collection_id=collection_id)
            if photo.uploaded_by != request.user and request.user.role != 'retoucher':
                logger.warning(f"Access denied for {request.user.email} to delete photo {photo_id}")
                return Response({"error": "You can only delete your own photos"}, status=status.HTTP_403_FORBIDDEN)
            photo_file = photo.file.path
            photo.delete()
            logger.info(f"Photo {photo_id} deleted from database by {request.user.email}")
            try:
                if os.path.exists(photo_file):
                    os.remove(photo_file)
                    logger.info(f"Photo file {photo_file} deleted from storage")
                else:
                    logger.warning(f"Photo file {photo_file} not found on disk")
            except Exception as e:
                logger.error(f"Failed to delete photo file {photo_file}: {str(e)}")
            return Response({"message": "Photo deleted"}, status=status.HTTP_200_OK)
        except Photo.DoesNotExist:
            logger.error(f"Photo {photo_id} not found in collection {collection_id}")
            return Response({"error": "Photo not found"}, status=status.HTTP_404_NOT_FOUND)

class CollectionCreateView(APIView):
    """
    Ендпоінт для створення колекцій/підколекцій.
    Доступний для авторизованих фотографів/ретушерів.
    Повертає:
        - 201 Created з даними колекції.
        - 400 Bad Request при помилках валідації.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def post(self, request):
        logger.debug(f"Collection creation attempt by {request.user.email}")
        data = {
            'name': request.data.get('name'),
            'owner': request.user.id,
            'project': request.data.get('project_id'),
            'parent': request.data.get('parent_id')
        }
        serializer = CollectionSerializer(data=data)
        if serializer.is_valid():
            collection = serializer.save()
            logger.info(f"Collection created by {request.user.email}: {collection.name}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CollectionListView(APIView):
    """
    Ендпоінт для отримання списку колекцій.
    Доступний для авторизованих фотографів/ретушерів.
    Повертає:
        - 200 OK зі списком колекцій.
        - 403 Forbidden без прав доступу.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def get(self, request):
        logger.debug(f"Collection list view attempt by {request.user.email}")
        collections = Collection.objects.filter(project__company=request.user.company)
        serializer = CollectionSerializer(collections, many=True)
        logger.info(f"Collection list viewed by {request.user.email}, count: {len(collections)}")
        return Response(serializer.data, status=status.HTTP_200_OK)

class CollectionView(APIView):
    """
    Ендпоінт для роботи з колекцією (отримання/редагування).
    Доступний для авторизованих фотографів/ретушерів.
    Повертає:
        - GET: 200 OK з даними колекції, 404 якщо не знайдена.
        - PATCH: 200 OK з оновленими даними, 400/404 при помилках.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def get(self, request, collection_id):
        logger.debug(f"Collection view attempt by {request.user.email} for collection {collection_id}")
        try:
            collection = Collection.objects.get(pk=collection_id)
            if collection.project and collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)
            serializer = CollectionSerializer(collection)
            logger.info(f"Collection {collection_id} viewed by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, collection_id):
        logger.debug(f"Collection update attempt by {request.user.email} for collection {collection_id}")
        try:
            collection = Collection.objects.get(pk=collection_id)
            if collection.project and collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)
            serializer = CollectionSerializer(collection, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Collection {collection_id} updated by {request.user.email}: new name {serializer.data.get('name')}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.error(f"Serializer errors for collection {collection_id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

class CollectionDeleteView(APIView):
    """
    Ендпоінт для видалення колекції.
    Доступний для авторизованих фотографів/ретушерів.
    Повертає:
        - 200 OK при успішному видаленні.
        - 400 Bad Request якщо є фото/підколекції.
        - 403 Forbidden без прав доступу.
        - 404 Not Found якщо колекція не знайдена.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def delete(self, request, collection_id):
        logger.debug(f"Collection deletion attempt by {request.user.email} for collection {collection_id}")
        try:
            collection = Collection.objects.get(pk=collection_id)
            if collection.project and collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)
            if collection.photos.exists():
                logger.warning(f"Collection {collection_id} contains photos")
                return Response({"error": "Collection contains photos and cannot be deleted"}, status=status.HTTP_400_BAD_REQUEST)
            if collection.subcollections.exists():
                logger.warning(f"Collection {collection_id} contains subcollections")
                return Response({"error": "Collection contains subcollections and cannot be deleted"}, status=status.HTTP_400_BAD_REQUEST)
            collection.delete()
            logger.info(f"Collection {collection_id} deleted by {request.user.email}")
            return Response({"message": "Collection deleted"}, status=status.HTTP_200_OK)
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

class GenerateClientLinkView(APIView):
    """
    Ендпоінт для генерації клієнтського посилання на колекцію.
    Доступний для авторизованих фотографів/ретушерів.
    Повертає:
        - 200 OK з посиланням.
        - 403 Forbidden без прав доступу.
        - 404 Not Found якщо колекція не знайдена.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def post(self, request):
        collection_id = request.data.get('collection_id')
        logger.debug(f"Client link generation attempt by {request.user.email} for collection {collection_id}")
        try:
            collection = Collection.objects.get(pk=collection_id)
            if collection.project and collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)
            client_link = f"http://localhost:8000/api/filesharing/collections/{collection_id}/client/"
            logger.info(f"Client link generated for collection {collection_id} by {request.user.email}: {client_link}")
            return Response({"client_link": client_link}, status=status.HTTP_200_OK)
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)