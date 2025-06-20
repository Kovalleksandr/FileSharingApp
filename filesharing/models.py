#filesharing\models.py
from django.db import models
from accounts.models import User
import os
import logging

logger = logging.getLogger('filesharing')

class Collection(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey('crm.Project', on_delete=models.CASCADE, null=True, blank=True, related_name='collections')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcollections')
    is_client_selection = models.BooleanField(default=False, help_text="Позначає, чи є колекція клієнтською підбіркою")

    def __str__(self):
        return self.name

class Folder(models.Model):
    name = models.CharField(max_length=255)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='folder_set')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['name', 'collection', 'parent']
        
    def __str__(self):
        return f"{self.name} in {self.collection.name}"

class Photo(models.Model):
    def get_upload_path(instance, filename):
        company_name = instance.collection.project.company.name
        project_name = instance.collection.project.name
        folder_name = instance.folder.name if instance.folder else ''
        path = os.path.join(company_name, project_name, folder_name, filename)
        logger.debug(f"Photo upload path: {path}")
        return path

    file = models.FileField(upload_to=get_upload_path)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='photos')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_selected = models.BooleanField(default=False, help_text="Позначено клієнтом для підбірки")

    def __str__(self):
        return f"Photo in {self.collection.name} by {self.uploaded_by.email}"