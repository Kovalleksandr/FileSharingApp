from django.db import models
from accounts.models import User

class Collection(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey('crm.Project', on_delete=models.CASCADE, null=True, blank=True, related_name='collections')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcollections')  # Додано для папок

    def __str__(self):
        return self.name

class Photo(models.Model):
    file = models.FileField(upload_to='photos/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='photos')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Поле для клієнтської підбірки
    is_selected = models.BooleanField(default=False, help_text="Позначено клієнтом для підбірки")

    def __str__(self):
        return f"Photo in {self.collection.name} by {self.uploaded_by.email}"