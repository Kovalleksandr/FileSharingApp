from django.urls import path
from .views import ProjectCreateView, StageCreateView, StageUpdateView, StageDeleteView  # Додано StageDeleteView


urlpatterns = [
    path('projects/', ProjectCreateView.as_view(), name='project-create'),
    path('stages/', StageCreateView.as_view(), name='stage-create'),
    path('stages/<int:stage_id>/', StageUpdateView.as_view(), name='stage-update'),
    path('stages/<int:stage_id>/delete/', StageDeleteView.as_view(), name='stage-delete'),
]