#crm\models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from filesharing.models import Collection
import logging

logger = logging.getLogger(__name__)

class Company(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_companies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Stage(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stages')  # Без null=True
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_stages')

    def __str__(self):
        return f"{self.name} (Company: {self.company.name}, Order: {self.order})"

    class Meta:
        ordering = ['order']
        unique_together = ('company', 'order')

class Project(models.Model):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')  # Без null=True
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    current_stage = models.ForeignKey(Stage, on_delete=models.PROTECT, null=True, blank=True, related_name='active_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    client_link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

@receiver(post_save, sender=Project)
def create_project_collection(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Creating collection for project '{instance.name}' (id={instance.id}) with owner_id={instance.owner_id}")
        collection = Collection.objects.create(
            name=f"{instance.name} - Project Folder",
            owner=instance.owner,
            project=instance
        )
        instance.client_link = f"http://localhost:8000/api/filesharing/collections/{collection.id}/client/"
        instance.save(update_fields=['client_link'])
        logger.info(f"Project '{instance.name}' (id={instance.id}) updated with client_link: {instance.client_link}")