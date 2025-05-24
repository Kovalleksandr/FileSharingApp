from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Collection, Photo
from .serializers import CollectionSerializer, PhotoSerializer
import logging
import os
from .permissions import IsPhotographerOrRetoucher

logger = logging.getLogger('filesharing')

class ClientCollectionView(APIView):
    """
    Ендпоінт для отримання інформації про колекцію для клієнта.
    Використовується для отримання даних про конкретну колекцію за її ID (GET)
    або для вибору фотографії з колекції (POST).
    Доступний для всіх користувачів (GET) або клієнтів (POST).
    Повертає:
        - GET: 200 OK з даними колекції, 404 Not Found, якщо колекція не знайдена.
        - POST: 200 OK з повідомленням про успішний вибір фотографії,
                404 Not Found, якщо фотографія не знайдена.
    """
    def get(self, request, collection_id):
        try:
            collection = Collection.objects.get(id=collection_id)
            serializer = CollectionSerializer(collection)
            logger.info(f"Collection {collection_id} viewed by client")
            return Response(serializer.data)
        except Collection.DoesNotExist:
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, collection_id):
        try:
            photo = Photo.objects.get(id=request.data.get('photo_id'), collection_id=collection_id)
            photo.is_selected = True
            photo.save()
            logger.info(f"Photo selected in collection {collection_id}, photo_id: {request.data.get('photo_id')}")
            return Response({"message": "Photo selected"})
        except Photo.DoesNotExist:
            return Response({"error": "Photo not found"}, status=status.HTTP_404_NOT_FOUND)

class PhotoUploadView(APIView):
    """
    Ендпоінт для завантаження фотографій у колекцію.
    Використовується MultiPartParser для обробки файлів.
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Відповідає за перевірку прав доступу та збереження фотографії у базі даних.
    Використовує PhotoSerializer для валідації даних.
    Повертає:
        - 201 Created при успішному завантаженні.
        - 400 Bad Request при помилках валідації.
        - 401 Unauthorized при відсутності аутентифікації.
        - 403 Forbidden при недостатніх правах доступу.
        - 404 Not Found, якщо колекція не знайдена.
    Користувач може завантажувати фото лише в колекції, які належать проєкту його компанії.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def post(self, request, collection_id):
        logger.debug(f"Photo upload attempt by {request.user.email if request.user.is_authenticated else 'anonymous'} for collection {collection_id}")
        if not request.user.is_authenticated:
            logger.error("User is not authenticated")
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            collection = Collection.objects.get(id=collection_id)
            if collection.project and collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)

            files = request.FILES.getlist('files')
            if not files:
                return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)

            uploaded_photos = []
            for file in files:
                data = {
                    'file': file,
                    'collection': collection.id,
                    'uploaded_by': request.user.id
                }
                serializer = PhotoSerializer(data=data)
                if serializer.is_valid():
                    photo = serializer.save()
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
    Використовується для видалення фотографії за її ID.
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Повертає:
        - 200 OK з повідомленням про успішне видалення.
        - 404 Not Found, якщо фотографія не знайдена.
        - 403 Forbidden, якщо користувач не має доступу до цієї фотографії.
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
            logger.info(f"Attempting to delete photo {photo_id} with file {photo_file}")
            photo.delete()
            logger.info(f"Photo {photo_id} deleted from database by {request.user.email} in collection {collection_id}")
            try:
                if os.path.exists(photo_file):
                    os.remove(photo_file)
                    logger.info(f"Photo file {photo_file} successfully deleted from storage")
                else:
                    logger.warning(f"Photo file {photo_file} not found on disk")
                return Response({"message": "Photo deleted"}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Failed to delete photo file {photo_file}: {str(e)}")
                return Response({"message": "Photo deleted, but file removal failed"}, status=status.HTTP_200_OK)
        except Photo.DoesNotExist:
            logger.error(f"Photo {photo_id} not found in collection {collection_id}")
            return Response({"error": "Photo not found"}, status=status.HTTP_404_NOT_FOUND)

class CollectionCreateView(APIView):
    """
    Ендпоінт для створення колекцій або підколекцій.
    Використовується для створення нової колекції з батьківською колекцією (опціонально).
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Повертає:
        - 201 Created з даними нової колекції.
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

class CollectionView(APIView):
    """
    Ендпоінт для отримання та редагування інформації про колекцію.
    Використовується для отримання даних про колекцію за її ID (GET)
    або оновлення назви колекції (PATCH).
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Повертає:
        - GET: 200 OK з даними колекції, 404 Not Found, якщо колекція не знайдена,
               403 Forbidden, якщо користувач не має доступу.
        - PATCH: 200 OK з оновленими даними колекції, 400 Bad Request при помилках валідації,
                 404 Not Found, якщо колекція не знайдена,
                 403 Forbidden, якщо користувач не має доступу.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def get(self, request, collection_id):
        logger.debug(f"Collection view attempt by {request.user.email} for collection {collection_id}")
        try:
            collection = Collection.objects.get(id=collection_id)
            if collection.project and collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)
            serializer = CollectionSerializer(collection)
            logger.info(f"Collection {collection_id} viewed by {request.user.email}")
            return Response(serializer.data)
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, collection_id):
        logger.debug(f"Collection update attempt by {request.user.email} for collection {collection_id}")
        try:
            collection = Collection.objects.get(id=collection_id)
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
    Використовується для видалення колекції за її ID.
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Повертає:
        - 200 OK з повідомленням про успішне видалення.
        - 404 Not Found, якщо колекція не знайдена.
        - 403 Forbidden, якщо користувач не має доступу до цієї колекції.
        - 400 Bad Request, якщо колекція містить фотографії або підколекції.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def delete(self, request, collection_id):
        logger.debug(f"Collection deletion attempt by {request.user.email} for collection {collection_id}")
        try:
            collection = Collection.objects.get(id=collection_id)
            if collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)
            if collection.photos.exists():
                logger.warning(f"Collection {collection_id} contains photos and cannot be deleted")
                return Response({"error": "Collection contains photos and cannot be deleted"}, status=status.HTTP_400_BAD_REQUEST)
            if collection.subcollections.exists():
                logger.warning(f"Collection {collection_id} contains subcollections and cannot be deleted")
                return Response({"error": "Collection contains subcollections and cannot be deleted"}, status=status.HTTP_400_BAD_REQUEST)
            collection.delete()
            logger.info(f"Collection {collection_id} deleted by {request.user.email}")
            return Response({"message": "Collection deleted"}, status=status.HTTP_200_OK)
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)

class GenerateClientLinkView(APIView):
    """
    Ендпоінт для генерації посилання для клієнта на колекцію.
    Використовується для створення посилання, яке може бути надіслане клієнту для доступу до колекції.
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Повертає:
        - 200 OK з посиланням на колекцію.
        - 404 Not Found, якщо колекція не знайдена.
        - 403 Forbidden, якщо користувач не має доступу до цієї колекції.
    """
    permission_classes = [permissions.IsAuthenticated, IsPhotographerOrRetoucher]

    def post(self, request):
        collection_id = request.data.get('collection_id')
        try:
            collection = Collection.objects.get(id=collection_id)
            if collection.project.company != request.user.company:
                logger.warning(f"Access denied for {request.user.email} to collection {collection_id}")
                return Response({"error": "You do not have access to this collection"}, status=status.HTTP_403_FORBIDDEN)
            client_link = f"http://localhost:8000/api/filesharing/collections/{collection_id}/client/"
            logger.info(f"Client link generated for collection {collection_id} by {request.user.email}: {client_link}")
            return Response({"client_link": client_link})
        except Collection.DoesNotExist:
            logger.error(f"Collection {collection_id} not found")
            return Response({"error": "Collection not found"}, status=status.HTTP_404_NOT_FOUND)