from django.urls import path
from .views import ClientCollectionView, PhotoUploadView, CollectionCreateView, CollectionView, GenerateClientLinkView, PhotoDeleteView

urlpatterns = [
    path('collections/<int:collection_id>/client/', ClientCollectionView.as_view(), name='client-collection'),
    path('collections/<int:collection_id>/photos/', PhotoUploadView.as_view(), name='photo-upload'),
    path('collections/<int:collection_id>/', CollectionView.as_view(), name='collection-view'),
    path('collections/', CollectionCreateView.as_view(), name='collection-create'),
    path('generate-client-link/', GenerateClientLinkView.as_view(), name='generate-client-link'),
    path('collections/<int:collection_id>/photos/<int:photo_id>/', PhotoDeleteView.as_view(), name='photo-delete'),
]