from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from filesharing.models import Collection

class Project(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    client_link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

@receiver(post_save, sender=Project)
def create_project_collection(sender, instance, created, **kwargs):
    if created:
        collection = Collection.objects.create(
            name=f"{instance.name} - Project Folder",
            owner=instance.owner,
            project=instance
        )
        instance.client_link = f"http://localhost:8000/api/filesharing/collections/{collection.id}/client/"
        instance.save(update_fields=['client_link'])  # Оновлюємо лише client_link