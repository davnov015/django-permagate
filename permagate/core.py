from django.db.models import QuerySet
from .models import UserPermission, GroupPermission, User
from .permission import Permission
import logging


logger = logging.getLogger(__name__)


def has_permission(user: User, permission: str) -> bool:
    """
    Verifies that a user has a specific permission, or is a member of a group that has the permission. Note that the
    permission string "a.b>" implies that a user has the a.b permission as well as all child permissions.
    :param user: A User model instance
    :param permission: An absolute permission string (does not contain the inclusive wildcard '>')
    :return: True if the user has the specified permission
    """
    root: Permission = Permission.get_root()
    if root.exists(permission):
        user_permission = _has_permission(user.permagate_permissions.all(), permission)
        if not user_permission:
            for group in user.groups.all():
                group_permissions = group.permagate_permissions.all()
                if _has_permission(group_permissions, permission):
                    return True
        else:
            return user_permission
    else:
        logger.warning(f"Checking for permission {permission} that does not exist")
    return False


def _has_permission(
    queryset: QuerySet[UserPermission, GroupPermission],
    permission: str,
    wildcard_only: bool = False,
) -> bool:
    """
    Determines if a given permission is contained in the specified queryset while considering the inclusive wildcard
    operator '>'. The root permission ('*') is also considered.
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
        not wildcard_only
        and (
            queryset.filter(permission=permission).exists()
            or queryset.filter(permission="*")
        )
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
