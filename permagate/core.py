from django.db.models import QuerySet
from django.conf import settings
from .models import UserPermission, GroupPermission, User
from .permission import Permission
import importlib


def has_permission(user: User, permission: str) -> bool:
    """
    Verifies that a user has a specific permission, or is a member of a group that has the permission. Note that the
    permission string "a.b>" implies that a user has the a.b permission as well as all child permissions.
    :param user:
    :param permission:
    :return: True if the user has the specified permission
    """
    permissions_module = importlib.import_module(settings.PERMAGATE_PERMISSIONS)
    root: Permission = permissions_module.root
    if root.exists(permission):
        user_permission = _has_permission(user.permagate_permissions.all(), permission)
        if not user_permission:
            for group in user.groups.all():
                group_permissions = group.permagate_permissions.all()
                if _has_permission(group_permissions, permission):
                    return True
        else:
            return user_permission
    return False


def _has_permission(
    queryset: QuerySet[UserPermission, GroupPermission],
    permission: str,
    wildcard_only: bool = False,
) -> bool:
    """
    Determines if a given permission is contained in the specified queryset while considering the inclusive wildcard
    operator '>'.
    :param queryset: The queryset we're operating on
    :param permission: The permission we're looking up
    :param wildcard_only: Only check if the permission string w/ an appended wildcard character is found in the queryset
    :return: True if the queryset contains the permission
    """
    assert (
        ">" not in permission
    ), "A required permission cannot contain an inclusive wildcard '>'"
    assert len(permission) > 0, "The permission string cannot be empty"
    found = (
        not wildcard_only and queryset.filter(permission=permission).exists()
    ) or queryset.filter(permission=f"{permission}>").exists()
    if found:
        return True
    path_segments = permission.split(".")
    path_segments.pop()
    # If there are no segments left in the permission string, the permission was not found
    if not path_segments:
        return False
    permission = ".".join(path_segments)
    # If not set, this is our first run, narrow down the queryset (performance gain?)
    if not wildcard_only:
        queryset = queryset.filter(permission__iendswith=">")
    return _has_permission(queryset, permission, True)
