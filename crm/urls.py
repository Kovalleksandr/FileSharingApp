from django.urls import path
from .views import ProjectListCreateView, StageCreateView, StageUpdateView, StageDeleteView, StageListView, ProjectUpdateView

urlpatterns = [
    path('projects/', ProjectListCreateView.as_view(), name='project-list-create'),
    path('projects/<int:project_id>/', ProjectUpdateView.as_view(), name='project-update'),
    path('stages/', StageCreateView.as_view(), name='stage-create'),
    path('stages/<int:stage_id>/', StageUpdateView.as_view(), name='stage-update'),
    path('stages/<int:stage_id>/delete/', StageDeleteView.as_view(), name='stage-delete'),
    path('projects/<int:project_id>/stages/', StageListView.as_view(), name='stage-list'),
]