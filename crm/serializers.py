from rest_framework import serializers
from django.db import models
from .models import Company, Stage, Project

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'owner', 'created_at']
        read_only_fields = ['owner', 'created_at']

class StageSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Stage
        fields = ['id', 'name', 'order', 'created_at', 'created_by']
        read_only_fields = ['created_at', 'created_by']

    def create(self, validated_data):
        # Автоматично встановлюємо created_by як поточного користувача
        validated_data['created_by'] = self.context['request'].user
        # Автоматично встановлюємо company з користувача
        validated_data['company'] = self.context['request'].user.company
        # Якщо order не вказано, ставимо його останнім
        if 'order' not in validated_data or validated_data['order'] is None:
            last_order = Stage.objects.filter(company=validated_data['company']).aggregate(models.Max('order'))['order__max']
            validated_data['order'] = (last_order or 0) + 1
        else:
            # Зсуваємо інші етапи, якщо вставляємо в середину
            company = validated_data['company']
            new_order = validated_data['order']
            Stage.objects.filter(company=company, order__gte=new_order).update(order=models.F('order') + 1)
        return Stage.objects.create(**validated_data)

class ProjectSerializer(serializers.ModelSerializer):
    current_stage = serializers.PrimaryKeyRelatedField(queryset=Stage.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'company', 'owner', 'current_stage', 'created_at', 'client_link']
        read_only_fields = ['owner', 'created_at', 'client_link', 'company']

    def create(self, validated_data):
        # Додаємо дебаг для перевірки вхідних даних
        print("Validated data:", validated_data)
        validated_data['owner'] = self.context['request'].user
        validated_data['company'] = self.context['request'].user.company
        if 'current_stage' not in validated_data or validated_data['current_stage'] is None:
            first_stage = Stage.objects.filter(company=validated_data['company'], order=1).first()
            if first_stage:
                validated_data['current_stage'] = first_stage
        return Project.objects.create(**validated_data)