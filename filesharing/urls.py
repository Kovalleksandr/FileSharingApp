from django.urls import path
from .views import ClientCollectionView

urlpatterns = [
    path('collections/<int:collection_id>/client/', ClientCollectionView.as_view(), name='client-collection'),
]