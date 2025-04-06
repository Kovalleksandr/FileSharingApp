from django.urls import path
from .views import (
    CompanyCreateView,
    ProjectListCreateView,
    StageCreateView,
    StageUpdateView,
    StageDeleteView,
    StageListView,
    ProjectUpdateView,
    ProjectDeleteView
)

urlpatterns = [
    path('companies/', CompanyCreateView.as_view(), name='company-create'),
    path('projects/', ProjectListCreateView.as_view(), name='project-list-create'),
    path('stages/', StageCreateView.as_view(), name='stage-create'),
    path('stages/<int:stage_id>/', StageUpdateView.as_view(), name='stage-update'),
    path('stages/<int:stage_id>/delete/', StageDeleteView.as_view(), name='stage-delete'),
    path('stages/list/', StageListView.as_view(), name='stage-list'),
    path('projects/<int:project_id>/', ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:project_id>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
]