from rest_framework import serializers
from django.db import models  # Додаємо імпорт
from .models import Project, Stage

class StageSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Stage
        fields = ['id', 'project', 'name', 'order', 'created_at', 'created_by']

    def create(self, validated_data):
        # Автоматично встановлюємо created_by як поточного користувача
        validated_data['created_by'] = self.context['request'].user
        # Якщо order не вказано, ставимо його останнім
        if 'order' not in validated_data or validated_data['order'] is None:
            last_order = Stage.objects.filter(project=validated_data['project']).aggregate(models.Max('order'))['order__max']
            validated_data['order'] = (last_order or 0) + 1
        else:
            # Зсуваємо інші етапи, якщо вставляємо в середину
            project = validated_data['project']
            new_order = validated_data['order']
            Stage.objects.filter(project=project, order__gte=new_order).update(order=models.F('order') + 1)
        return Stage.objects.create(**validated_data)

class ProjectSerializer(serializers.ModelSerializer):
    stages = StageSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'owner', 'created_at', 'client_link', 'stages']
        read_only_fields = ['owner', 'created_at', 'client_link']