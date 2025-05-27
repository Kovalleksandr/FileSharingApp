from django.urls import path
from .views import (
    ClientCollectionView,
    PhotoUploadView,
    PhotoDeleteView,
    CollectionCreateView,
    CollectionListView,
    CollectionView,
    CollectionDeleteView,
    GenerateClientLinkView,
)

urlpatterns = [
    path('collections/<int:collection_id>/client/', ClientCollectionView.as_view(), name='client-collection'),
    path('collections/<int:collection_id>/photos/', PhotoUploadView.as_view(), name='photo-upload'),
    path('collections/<int:collection_id>/photos/<int:photo_id>/', PhotoDeleteView.as_view(), name='photo-delete'),
    path('collections/create/', CollectionCreateView.as_view(), name='collection-create'),
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/<int:collection_id>/', CollectionView.as_view(), name='collection-view'),
    path('collections/<int:collection_id>/delete/', CollectionDeleteView.as_view(), name='collection-delete'),
    path('collections/link/', GenerateClientLinkView.as_view(), name='generate-client-link'),
]