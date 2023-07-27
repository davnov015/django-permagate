from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class UserPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="permagate_permissions")
    permission = models.CharField()


class GroupPermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="permagate_permissions")
    permission = models.CharField()
