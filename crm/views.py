from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from .models import Project, Stage
from .serializers import ProjectSerializer, StageSerializer

class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role not in ['owner', 'photographer']:
            return Response({"error": "Only owners or photographers can create projects"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StageCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            project = serializer.validated_data['project']
            if project.owner != request.user:
                return Response({"error": "Only project owner can create stages"}, status=status.HTTP_403_FORBIDDEN)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StageUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, stage_id):
        try:
            stage = Stage.objects.get(id=stage_id)
        except Stage.DoesNotExist:
            return Response({"error": "Stage not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if stage.project.owner != request.user:
            return Response({"error": "Only project owner can update stages"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StageSerializer(stage, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            new_order = serializer.validated_data.get('order', stage.order)
            if new_order != stage.order:
                project = stage.project
                if new_order < stage.order:
                    Stage.objects.filter(project=project, order__gte=new_order, order__lt=stage.order).update(order=models.F('order') + 1)
                else:
                    Stage.objects.filter(project=project, order__gt=stage.order, order__lte=new_order).update(order=models.F('order') - 1)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StageDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, stage_id):
        try:
            stage = Stage.objects.get(id=stage_id)
        except Stage.DoesNotExist:
            return Response({"error": "Stage not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if stage.project.owner != request.user:
            return Response({"error": "Only project owner can delete stages"}, status=status.HTTP_403_FORBIDDEN)
        
        # Зсуваємо наступні етапи вниз
        Stage.objects.filter(project=stage.project, order__gt=stage.order).update(order=models.F('order') - 1)
        stage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class StageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if project.owner != request.user:
            return Response({"error": "Only project owner can view stages"}, status=status.HTTP_403_FORBIDDEN)
        
        stages = Stage.objects.filter(project=project).order_by('order')
        serializer = StageSerializer(stages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)