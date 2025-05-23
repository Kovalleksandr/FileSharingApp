from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Collection, Photo
from .serializers import CollectionSerializer, PhotoSerializer
from accounts.models import User
import logging

logger = logging.getLogger('filesharing')

class IsPhotographerOrRetoucher(permissions.BasePermission):
    def has_permission(self, request, view):
        is_authenticated = request.user.is_authenticated
        role = request.user.role if is_authenticated else 'none'
        email = request.user.email if is_authenticated else 'anonymous'
        logger.debug(f"Checking permission for user {email}, role: {role}, authenticated: {is_authenticated}")
        return is_authenticated and role in ['photographer', 'retoucher']

class ClientCollectionView(APIView):
    def get(self, request, collection_id):
        try:
            collection = Collection.objects.get(id=collection_id)
            serializer = CollectionSerializer(collection)
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
        

#---------------------------------------------------------------------------------------------
''' class PhotoUploadView(APIView).
    ендпоінт для завантаження фотографій у колекцію.
    Використовується MultiPartParser для обробки файлів.
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Відповідає за перевірку прав доступу та збереження фотографії у базі даних.
    Використовує PhotoSerializer для валідації даних.
    Повертає 201 Created при успішному завантаженні, 400 Bad Request при помилках валідації,
    401 Unauthorized при відсутності аутентифікації, 403 Forbidden при недостатніх правах доступу.

    НЕОБХІДНО РЕАЛІЗУВАТИ ПРИВЯЗКУ ДО ПРОЕКТУ, ЩОБ ЗАБЕЗПЕЧИТИ, ЩО ФОТОГРАФІЇ МОЖУТЬ БУТИ ЗАВАНТАЖЕНІ ТІЛЬКИ В КОЛЕКЦІЇ, ЯКІ ПРИНАДЛЕЖАТЬ ЦЬОМУ ПРОЕКТУ.
'''        
class PhotoUploadView(APIView):
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

            files = request.FILES.getlist('files')  # Отримуємо список файлів
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
        


#---------------------------------------------------------------------------------------------
''' class PhotoDeleteView(APIView).
    Це ендпоінт для видалення фотографій з колекції.
    Використовується для видалення фотографії за її ID.
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Повертає 204 No Content при успішному видаленні, 404 Not Found, якщо фотографія не знайдена,
    403 Forbidden, якщо користувач не має доступу до цієї фотографії.
'''

class PhotoDeleteView(APIView):
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
            import os
            if os.path.exists(photo_file):
                os.remove(photo_file)
                logger.info(f"Photo file {photo_file} deleted from storage")
            logger.info(f"Photo {photo_id} deleted by {request.user.email} from collection {collection_id}")
            return Response({"message": "Photo deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Photo.DoesNotExist:
            logger.error(f"Photo {photo_id} not found in collection {collection_id}")
            return Response({"error": "Photo not found"}, status=status.HTTP_404_NOT_FOUND)





#---------------------------------------------------------------------------------------------
''' class CollectionListView(APIView) Реалізація створення підколекцій.
    Це ендпоінт для створення підколекцій у файлообміннику. 
    Повинна створюватися колекція з батьківської колекції, яка передається в запиті.
'''
class CollectionCreateView(APIView):
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
    


#---------------------------------------------------------------------------------------------
''' class CollectionView(APIView).  
    Це ендпоінт для отримання інформації про колекцію.
    Використовується для отримання даних про конкретну колекцію за її ID.
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Повертає 200 OK з даними колекції, 404 Not Found, якщо колекція не знайдена,
    403 Forbidden, якщо користувач не має доступу до цієї колекції.
'''
class CollectionView(APIView):
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
        


#---------------------------------------------------------------------------------------------
'''class ClientCollectionView(APIView)
    Це ендпоінт для отримання інформації про колекцію для клієнта.
    Використовується для отримання даних про конкретну колекцію за її ID.
    Доступний тільки для авторизованих користувачів з роллю клієнта.
    Повертає 200 OK з даними колекції, 404 Not Found, якщо колекція не знайдена,
    403 Forbidden, якщо користувач не має доступу до цієї колекції.
    Використовується для вибору фотографії з колекції.
    Повертає 200 OK з повідомленням про успішний вибір фотографії,
    404 Not Found, якщо фотографія не знайдена.

'''
class ClientCollectionView(APIView):
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
        


#---------------------------------------------------------------------------------------------
""" class GenerateClientLinkView(APIView)
    Це ендпоінт для генерації посилання для клієнта на колекцію.
    Використовується для створення посилання, яке може бути надіслане клієнту для доступу до колекції.
    Доступний тільки для авторизованих користувачів з роллю фотографа або ретушера.
    Повертає 200 OK з посиланням на колекцію, 404 Not Found, якщо колекція не знайдена,
    403 Forbidden, якщо користувач не має доступу до цієї колекції.
"""

class GenerateClientLinkView(APIView):
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
        
