from django.urls import path
from .views import (
    FolderCreateView,
    PhotoUploadView,
    ClientCollectionView,
    PhotoDeleteView,
    CollectionCreateView,
    CollectionListView,
    CollectionView,
    CollectionDeleteView,
    GenerateClientLinkView,
    FolderClientView,
    ClientCollectionCreateView
)

urlpatterns = [
    path('folders/', FolderCreateView.as_view(), name='folder-create'),
    path('photos/upload/<int:collection_id>/', PhotoUploadView.as_view(), name='photo-upload'),
    path('collections/<int:collection_id>/client/', ClientCollectionView.as_view(), name='client-collection'),
    path('photos/<int:collection_id>/<int:photo_id>/delete/', PhotoDeleteView.as_view(), name='photo-delete'),
    path('collections/create/', CollectionCreateView.as_view(), name='collection-create'),
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/<int:collection_id>/', CollectionView.as_view(), name='collection-view'),
    path('collections/<int:collection_id>/delete/', CollectionDeleteView.as_view(), name='collection-delete'),
    path('collections/client-link/', GenerateClientLinkView.as_view(), name='generate-client-link'),
    # path('folders/client-link/', FolderClientLinkView.as_view(), name='folder-client-link'),  # Закоментовано через відсутність класу
    path('folders/<int:id>/client/', FolderClientView.as_view(), name='folder-client-view'),
    path('folders/<int:id>/client/collection/', ClientCollectionCreateView.as_view(), name='client-collection-create'), 
]