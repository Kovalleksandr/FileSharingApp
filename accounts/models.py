import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('photographer', 'Photographer'),
        ('retoucher', 'Retoucher'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='owner')
    company = models.ForeignKey(
        'crm.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

class Invitation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invitations")

    def __str__(self):
        return f"Invitation for {self.email} as {self.role}"