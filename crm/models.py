from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from filesharing.models import Collection
import logging

logger = logging.getLogger(__name__)

class Project(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    client_link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

class Stage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)  # Порядок етапу
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_stages')

    def __str__(self):
        return f"{self.name} (Project: {self.project.name}, Order: {self.order})"

    class Meta:
        ordering = ['order']  # Автоматичне сортування за порядком

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