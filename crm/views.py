#crm\views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from .models import Company, Stage, Project
from .serializers import CompanySerializer, StageSerializer, ProjectSerializer

# ---- COMPANY-КОМПАНІЇ ---- #

class CompanyCreateView(APIView): # ---- COMPANY-КОМПАНІЇ-додавання ---- #
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'owner':
            return Response({"error": "Only owners can create companies"}, status=status.HTTP_403_FORBIDDEN)
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save(owner=request.user)
            request.user.company = company
            request.user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ---- PROJECT-ПРОЄКТИ ---- #

class ProjectListCreateView(APIView): # ---- PROJECT-ПРОЄКТИ-додавання ---- #
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.company:
            return Response({"error": "User must belong to a company"}, status=status.HTTP_400_BAD_REQUEST)
        projects = Project.objects.filter(company=request.user.company)
        stage_name = request.query_params.get('stage_name')
        if stage_name:
            projects = projects.filter(current_stage__name=stage_name)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')

    def post(self, request):
        if request.user.role not in ['owner', 'photographer']:
            return Response({"error": "Only owners or photographers can create projects"}, status=status.HTTP_403_FORBIDDEN)
        if not request.user.company:
            return Response({"error": "User must belong to a company"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProjectSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED, content_type='application/json; charset=utf-8')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

class ProjectUpdateView(APIView): # ---- PROJECT-ПРОЄКТИ-оновлення ---- #
    permission_classes = [IsAuthenticated]

    def put(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if project.company != request.user.company:
            return Response({"error": "You can only update projects in your company"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectDeleteView(APIView): # ---- PROJECT-ПРОЄКТИ-видалення ---- #
    permission_classes = [IsAuthenticated]

    def delete(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if project.company != request.user.company or request.user.role not in ['owner', 'admin']:
            return Response({"error": "Only owners or admins in the same company can delete projects"}, status=status.HTTP_403_FORBIDDEN)
        
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ---- STAGE-ЕТАПИ ---- #

class StageCreateView(APIView): # ---- STAGE-ЕТАПИ-додавання ---- #
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role not in ['owner', 'admin']:
            return Response({"error": "Only owners or admins can create stages"}, status=status.HTTP_403_FORBIDDEN)
        if not request.user.company:
            return Response({"error": "User must belong to a company"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = StageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()  # company і created_by встановлюються в serializer.create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StageUpdateView(APIView): # ---- STAGE-ЕТАПИ-оновлення ---- #
    permission_classes = [IsAuthenticated]

    def put(self, request, stage_id):
        try:
            stage = Stage.objects.get(id=stage_id)
        except Stage.DoesNotExist:
            return Response({"error": "Stage not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if stage.company != request.user.company:
            return Response({"error": "You can only update stages in your company"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StageSerializer(stage, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            new_order = serializer.validated_data.get('order', stage.order)
            if new_order != stage.order:
                company = stage.company
                if new_order < stage.order:
                    Stage.objects.filter(company=company, order__gte=new_order, order__lt=stage.order).update(order=models.F('order') + 1)
                else:
                    Stage.objects.filter(company=company, order__gt=stage.order, order__lte=new_order).update(order=models.F('order') - 1)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StageDeleteView(APIView): # ---- STAGE-ЕТАПИ-видалення ---- #
    permission_classes = [IsAuthenticated]

    def delete(self, request, stage_id):
        try:
            stage = Stage.objects.get(id=stage_id)
        except Stage.DoesNotExist:
            return Response({"error": "Stage not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if stage.company != request.user.company or request.user.role not in ['owner', 'admin']:
            return Response({"error": "Only owners or admins in the same company can delete stages"}, status=status.HTTP_403_FORBIDDEN)
        
        # Зсуваємо наступні етапи вниз
        Stage.objects.filter(company=stage.company, order__gt=stage.order).update(order=models.F('order') - 1)
        stage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class StageListView(APIView): # ---- STAGE-ЕТАПИ-список ---- #
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.company:
            return Response({"error": "User must belong to a company"}, status=status.HTTP_400_BAD_REQUEST)
        
        stages = Stage.objects.filter(company=request.user.company).order_by('order')
        serializer = StageSerializer(stages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)