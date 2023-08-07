from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User as UserType
from django.core.exceptions import ValidationError
from .permission import Permission
from typing import Type

User: Type[UserType] = get_user_model()


def validate_permission(permission: str):
    root = Permission.get_root()
    if permission not in root.permission_list:
        raise ValidationError(
            f"{permission} is not a valid permission, check the list of valid permissions"
        )


class UserPermission(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="permagate_permissions"
    )
    permission = models.CharField(validators=[validate_permission], max_length=255)

    class Meta:
        unique_together = ["user", "permission"]


class GroupPermission(models.Model):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="permagate_permissions"
    )
    permission = models.CharField(validators=[validate_permission], max_length=255)

    class Meta:
        unique_together = ["group", "permission"]
