from django.urls import path
from .views import ClientCollectionView, PhotoUploadView, CollectionCreateView, CollectionView

urlpatterns = [
    path('collections/<int:collection_id>/client/', ClientCollectionView.as_view(), name='client-collection'),
    path('collections/<int:collection_id>/photos/', PhotoUploadView.as_view(), name='photo-upload'),
    path('collections/<int:collection_id>/', CollectionView.as_view(), name='collection-view'),
    path('collections/', CollectionCreateView.as_view(), name='collection-create'),
]